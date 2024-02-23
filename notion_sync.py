import pandas as pd
import requests
from dotenv import load_dotenv
import os
import json
# Load environment variables
dotenv_path = os.path.join(os.getcwd(), '.env')
load_dotenv(dotenv_path)
notion_api_key = os.getenv("NOTION_API_KEY")
database_id=os.getenv("NOTION_DATABASE_ID1")

#set working directory to the location of this file
os.chdir(os.path.dirname(os.path.abspath(__file__)))
headers = {
    "Authorization": f"Bearer {notion_api_key}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

json_file_path = 'upserted_records.json'

try:
    with open(json_file_path, 'r') as file:
        upserted_records = json.load(file)
except FileNotFoundError:
    upserted_records = {}
    
    

def search_notion_page_by_email(email_id):
    search_payload = {
        "filter": {
            "property": "EMAIL_ID",
            "text": {
                "equals": email_id
            }
        },
        "page_size": 1
    }
    search_response = requests.post(f'https://api.notion.com/v1/databases/{database_id}/query', json=search_payload, headers=headers)
    print(search_response.json())
    if search_response.status_code == 200:
        results = search_response.json().get("results", [])
        if results:
            return results[0]["id"]  # Return the first match's page ID
    return None

def upsert_notion_page(action, summary, due_date, priority, email_id, to, from_, date):
    # Check if due_date is NaN or 'NA' before processing
        # Before creating a new page, check if it already exists by email_id
    print(due_date)
    if pd.isna(due_date) or due_date == 'NA':
        formatted_due_date = None
    else:
        # Since due_date is already in 'YYYY-MM-DD' format, no need for further formatting
        formatted_due_date = due_date
    if priority:  # Check if priority is not None or empty
        priority = priority.capitalize()  # Capitalize the first letter of the priority tag
    
    # Construct the data payload
    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Action": {
                "rich_text": [
                    {"text": {"content": action}}
                ]
            },
            "Summary": {
                "title": [
                    {"text": {"content": summary}}
                ]
            },
            "Priority": {
                "select": {
                    "name": priority
                }
            },
            "EMAIL_ID": {
                "rich_text": [
                    {"text": {"content": email_id}}
                ]
            },
            "To": {
                "rich_text": [
                    {"text": {"content": to}}
                ]
            },
            "From": {
                "rich_text": [
                    {"text": {"content": from_}}
                ]
            },
            "Date": {
                "date": {"start": date}
                
            }

        }
    }

    if formatted_due_date:
        data["properties"]["Due_Date"] = {
            "date": {"start": formatted_due_date}
        }


    response = requests.post('https://api.notion.com/v1/pages', json=data, headers=headers)
    if response.status_code == 200:
        print(f"{action}: Page upserted successfully")
        return True
    else:
        print(f"{action}: Failed to upsert page", response.text)
        return False

# Load CSV file and iterate over rows to create/update Notion pages
csv_file_path = 'processed_messages.csv'
df = pd.read_csv(csv_file_path)


for index, row in df.iterrows():
    email_id = row['Email_ID']
    action = row['Action'] if pd.notna(row['Action']) and row['Action'] != 'NA' else ''
    if email_id not in upserted_records:  # Proceed if the entry hasn't been upserted yet
        success = upsert_notion_page(action, row['Summary'], row['Due_Date'], row['Priority'], row['Email_ID'], row['To'], row['From'], row['Date'])  # Your function call here
        if success:
            upserted_records[email_id] = {'Upserted': 'Yes'}
            # Write to the JSON file after each successful upsert
            with open(json_file_path, 'w') as file:
                json.dump(upserted_records, file, indent=4)
