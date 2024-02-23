from dotenv import load_dotenv
from openai import OpenAI
import os
import csv
import json
import re
from datetime import date
import logging
import pandas as pd
from datetime import datetime

# Load environment variables
dotenv_path = os.path.join(os.getcwd(), '.env')
load_dotenv(dotenv_path)
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
GPT_MODEL = "gpt-3.5-turbo-0125"
client = OpenAI()
input_csv_file_path = os.path.join(os.getcwd(), 'messages.csv')
output_csv_file_path = os.path.join(os.getcwd(), 'processed_messages.csv')
output_headers = ['Email_ID', 'Thread_ID', 'From', 'To', 'Action', 'Summary', 'Due_Date', 'Priority','Date']

today = date.today()
# Format today's date as DDMMYYYY
today = today.strftime("%d%m%Y")

# Configure logging to write to a file, with a level of DEBUG to capture all messages
logging.basicConfig(filename='api_exchanges.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')



def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

def call_api(email_content, email_from, email_to):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "process_email_content",
                "description": "extract the following: actionable or not , succint summary, due date, and priority from [email content]",
                "parameters": {
                "type": "object",
                "properties": {
                    
                    "action": {
                        "type": "string",
                        "description": "If the email require to take action on it:'actionable'| feature advertisement, spam, ads etc are not actionable return'NA'",
                    },                                    

                    "due_date": {
                        "type": "string",
                        "description": "The due date mentioned in the email, formatted as DDMMYYYY or 'NA'.",
                    },
                    
                    "summary": {
                        "type": "string",
                        "description": "A brief summary of the email's content.",
                    },
                    
                    "priority": {
                        "type": "string",
                        
                        "description": " provide the priority level of the email: urgent , normal, informational only, or garbage(promotional, feature promotion, spam, ads etc). [example1: credit card due date is morethan 5 days :normal, less than 5 days: urgent], [example2: approval for something applied:normal and information only not actionalble, but if rejected : urgent and actionable]",
                    },
                },
                },
                "required": ["action", "summary", "due_date","priority"],
                },
            }
        ]
    
    messages = [
        {"role": "system", "content":   f"""Think step by step and classify the email content accurately. 
                                        Determine whether the email requires action ('actionable') or not ('NA'). 
                                        'Actionable' emails demand a response or follow-up, such as a bill payment reminder or a meeting invitation. 
                                        Non-actionable emails, such as advertisements , approved transaction or informational newsletters, should be marked 'NA'and Informational only.
                                        Next, succinctly summarize the email's content, focusing on the main point or action required if any. 
                                        Identify any due dates mentioned in the email. If a specific date is provided, format it as DDMMYYYY. ASAP means due date is today. 
                                        -calculate difference between today's date and due date in [DAY's field]
                                        If no date is given, return 'NA'.
                                        Finally, assess the priority of the email based on its content and context if my email id (prateekchanda.gcptemp@gmail.com) is not in to field it is not urgent or normal.
                                        - 'Urgent': Requires immediate action or attention, if due in 3 days from todays date:{today}. Examples include overdue bills or urgent meeting requests.
                                        - 'Normal': Important but not urgent, with actions or responses needed within a week.
                                        - 'Informational only': Contains no immediate action or follow-up, such as newsletters or general updates.
                                        - 'Garbage': Promotional content, spam, or advertisements with no relevant action required.
                                        Use these criteria to evaluate each email accurately, ensuring that non-actionable items, 
                                        especially those of a promotional or informational nature, are not classified as 'urgent' 
                                        unless they explicitly contain time-sensitive information requiring immediate attention."""},
        {"role": "user", "content":  f"[email content] today's date is: {today} \n\nFrom: {email_from}\nTo: {email_to}\nContent: {email_content}"}
    ]
    try:
         # Log the request details
        logging.debug(f"API Request - From: {email_from}, To: {email_to}, Content: {email_content}")
        
        chat_response = chat_completion_request(messages, tools=tools, tool_choice={"type": "function", "function": {"name": "process_email_content"}})
       
        # Log the response details
        logging.debug(f"API Response: {chat_response}")
        # Processing chat_response...
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        # Handle JSON parsing error
    except Exception as e:
        print(f"Unexpected error calling API or processing response: {e}")
        # Handle other unexpected errors
        # Log the exception
        logging.error(f"API Call Error: {e}")

    if chat_response.choices[0].message.tool_calls:
        # Access the first tool call response
        tool_call_response = chat_response.choices[0].message.tool_calls[0]
        # Assuming the tool_call_response contains a dictionary in the 'function' attribute that includes 'arguments'
        # Here, you need to parse the JSON string in 'arguments' to a Python dictionary
        processed_info = json.loads(tool_call_response.function.arguments)
        # Extract information from the processed_info dictionary
        # Note: The actual structure of processed_info depends on how your function returns the data
        action = processed_info.get("action", "No action required")
        summary = processed_info.get("summary", "Summary not provided.")
        due_date = processed_info.get("due_date", "Due date not provided.")
        priority = processed_info.get("priority", "Priority not provided.")
        
        print(f"Actionable: {action}, Summary: {summary}, Due Date: {due_date}, Priority: {priority}")
        
    else:
        print("No information extracted from email.")
    return(action, summary, due_date, priority)

def clean_text(raw_text):
    cleanr = re.compile('<.*?>')  # Remove HTML tags
    cleantext = re.sub(cleanr, '', raw_text)
    cleantext = re.sub(r'[^a-zA-Z0-9\s!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~]', '', cleantext)  # Remove non-alphanumeric characters and symbols except spaces and commonly used special characters
    return cleantext



# Read the input CSV and write to the output CSV, ensuring to carry over Email_ID and Thread_ID
with open(input_csv_file_path, 'r', encoding='utf-8-sig') as infile, open(output_csv_file_path, 'w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=output_headers)
    writer.writeheader()
        
    for index, row in enumerate(reader):
        email_content = clean_text(row['Body'])
        email_from = clean_text(row['From'])
        email_to = clean_text(row['To'])
        email_id = row['Email_ID'].strip()  # Assuming you have an Email_ID column in your input CSV
        thread_id = row['Thread_ID']  # Similarly for Thread_ID
        # Call the API with the cleaned email content
        action, summary, due_date, priority = call_api(email_content, email_from, email_to)
        today_formatted = date.today().isoformat() # Use today's date in ISO format
        # Write the processed data along with Email_ID and Thread_ID to the output CSV
        # if due date is not NA calculate difference between today's date and due date
              
        if due_date != 'NA' and due_date != 'ASAP':
                try:
                    # Attempt to parse due_date and calculate differences
                    due_date_object = datetime.strptime(due_date, '%d%m%Y').date()
                    days_diff = (due_date_object - date.today()).days

                    if action != 'NA':
                        priority = 'urgent' if days_diff <= 3 else 'normal'
                    
                    # Use ISO format for output
                    due_date = due_date_object.isoformat()
                except ValueError:
                    # Handle parsing error
                    due_date = 'Invalid format'
                    try:
                        # Attempt to parse due_date and calculate differences
                        due_date_object = datetime.strptime(due_date, '%d%m%Y').date()
                        days_diff = (due_date_object - date.today()).days

                        if action != 'NA':
                            priority = 'urgent' if days_diff <= 3 else 'normal'
                        
                        # Use ISO format for output
                        due_date = due_date_object.isoformat()
                    except ValueError:
                        # Handle parsing error
                        due_date = 'Invalid format'
        elif due_date == 'ASAP':
                    due_date = today_formatted  # Use today's date for ASAP
                
                
        writer.writerow({
                    'Email_ID': email_id,
                    'Thread_ID': thread_id,
                    'From': email_from,  
                    'To': email_to,
                    'Action': action,
                    'Summary': summary,
                    'Due_Date': due_date,
                    'Priority': priority,
                    'Date': today_formatted  
                })
