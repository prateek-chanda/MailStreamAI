from base64 import urlsafe_b64decode
import os.path
import csv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

#defining the variables
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
maxResults=3
PROCESSED_EMAILS_FILE = "processed_emails.json"

def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def list_messages(service, user_id="me", label_ids=[]):
    try:
        response = service.users().messages().list(userId=user_id, labelIds=label_ids).execute()
        messages = response.get('messages', [])
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, labelIds=label_ids, pageToken=page_token).execute()
            messages.extend(response['messages'])
        messages = messages[:maxResults]
        messages.reverse()  # Reverse the order of messages
        return messages
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []



def get_message_details(service,  message_id, user_id="me"):
    try:
        message = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
        
        # Initialize details with direct assignments
        details = {
            'message_id': message_id,
            'Thread_ID': message.get('threadId', 'N/A'),  # Safe access using .get
            'Labels': ", ".join(message.get('labelIds', [])),  # Join labels into a string
            'Snippet': message.get('snippet', ''),
            'Body': "N/A"  # Default body value
        }
        
        # Process headers
        headers = {header['name']: header['value'] for header in message['payload'].get('headers', [])}
        for key in ['From', 'To', 'Cc', 'Subject', 'Date']:
            details[key] = headers.get(key, 'N/A')  # Safe access
        
        # Decode the email body if available
        part = find_text_plain_part(message['payload'])
        if part and 'body' in part and 'data' in part['body']:
            details['Body'] = urlsafe_b64decode(part['body']['data'].encode('ASCII')).decode('utf-8')
        
        return details
    except HttpError as error:
        print(f"An error occurred: {error}")
        return {}




def find_text_plain_part(part):
    if part['mimeType'] == 'text/plain':
        return part
    for subpart in part.get('parts', []):
        result = find_text_plain_part(subpart)
        if result:
            return result
    return None


def export_messages_to_csv(messages, filename="messages.csv"):
    file_exists = os.path.exists(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        fieldnames = ['Email_ID', 'Date', 'From', 'To', 'Cc', 'Subject', 'Body', 'Thread_ID', 'Labels', 'Snippet']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for message in messages:
            writer.writerow({
                'Email_ID': message.get('message_id'),
                'Date': message.get('Date'),
                'From': message.get('From'),
                'To': message.get('To'),
                'Cc': message.get('Cc'),
                'Subject': message.get('Subject'),
                'Body': message.get('Body'),
                'Thread_ID': message.get('Thread_ID'),
                'Labels': message.get('Labels'),
                'Snippet': message.get('Snippet')
            })


def load_processed_emails(filename="messages.csv"):
    processed_emails = set()
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                processed_emails.add(row['Email_ID'])
    except FileNotFoundError:
        # If the file doesn't exist, that means no emails have been processed yet.
        pass
    return processed_emails


def save_processed_email(email_id):
    processed_emails = load_processed_emails()
    processed_emails.append(email_id)
    with open(PROCESSED_EMAILS_FILE, "w") as file:
        json.dump(processed_emails, file)


def main():
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    messages = list_messages(service)
    processed_emails = load_processed_emails()
    detailed_messages = []
    for message in messages:
        if message['id'] not in processed_emails:
            detailed_messages.append(get_message_details(service, message['id']))
            #save_processed_email(message['id'])
    export_messages_to_csv(detailed_messages)


if __name__ == "__main__":
    main()
