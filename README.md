# MailStream AI - Automating Email Prioritization

MailStream AI (MSI) leverages advanced AI technologies to transform email management by intelligently parsing, extracting, and prioritizing tasks directly into a Notion dashboard. Designed for professionals overwhelmed by their inboxes, MSI differentiates urgent from routine tasks, schedules them appropriately, and can assign tasks to team members, turning email management into a strategic advantage.

## Features

- **Email Parsing**: Analyze and extract actionable tasks from emails.
- **Task Prioritization**: Distinguish urgent tasks and prioritize them in a Notion dashboard.
- **Scheduling**: Schedule tasks based on urgency and deadlines.
- **Team Delegation**: Assign tasks to appropriate team members directly from the dashboard.
- **Productivity Enhancement**: Focus on high-priority tasks to enhance overall productivity.

## Getting Started

### Prerequisites

- Python 3.6 or later
- Notion account and API access
- Access to an email server (IMAP/SMTP)

### Installation

1. Clone the repository:
git clone https://github.com/prateek-chanda/MailStreamAI.git


### Setup

1. **Configure Email Access**: Edit `fetch_emails.py` with your email server details.
2. **Set Up Notion Integration**: Obtain your Notion API key and configure `notion_sync.py` accordingly.
3. **API Configuration**: Ensure `api_call.py` is set with the correct endpoints for processing the emails.

## Usage

To run MailStream AI, execute the following command in the terminal:

python fetch_emails.py > api_call.py > notion_sync.py 

Only one email is being used as a demo at present

This command initiates the email fetching process, task extraction, and synchronization with Notion.

## Files Description

- **fetch_emails.py**: Connects to your email server, fetches emails, and extracts relevant data for processing.
- **api_call.py**: Handles API calls to the AI service for parsing and prioritizing email content.
- **notion_sync.py**: Synchronizes the processed tasks with your Notion dashboard, organizing them based on priority and urgency.

## Contributing

We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

- Thanks to all contributors who have helped to shape MailStream AI into a valuable tool for professionals.
- Special thanks to the open-source community for the continuous inspiration and support.

