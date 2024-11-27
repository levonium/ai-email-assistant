import imaplib
import email
import os
from email.message import EmailMessage
from anthropic import Anthropic
from datetime import datetime
import json
import time
from typing import List, Dict
import yaml

class EmailAssistant:
    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize the email assistant with configuration."""
        self.load_config(config_path)
        self.anthropic = Anthropic(api_key=self.config['anthropic_api_key'])
        self.connect_imap()
        self.load_history()

    def load_config(self, config_path: str):
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def connect_imap(self):
        """Establish IMAP connection."""
        self.imap = imaplib.IMAP4_SSL(self.config['imap_server'])
        self.imap.login(self.config['email'], self.config['password'])

    def load_history(self):
        """Load conversation history from JSON file."""
        try:
            with open('conversation_history.json', 'r') as f:
                self.history = json.load(f)
        except FileNotFoundError:
            self.history = []

    def save_history(self):
        """Save conversation history to JSON file."""
        with open('conversation_history.json', 'w') as f:
            json.dump(self.history, f)

    def is_blacklisted(self, sender: str) -> bool:
        """Check if sender is in blacklist."""
        return any(blocked in sender.lower() for blocked in self.config['blacklist'])

    def get_new_emails(self) -> List[Dict]:
        """Fetch new unread emails."""
        self.imap.select('INBOX')
        _, messages = self.imap.search(None, 'UNSEEN')
        
        new_emails = []
        for num in messages[0].split():
            _, msg_data = self.imap.fetch(num, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            sender = email.utils.parseaddr(email_message['From'])[1]
            if self.is_blacklisted(sender):
                continue

            content = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        content += part.get_payload(decode=True).decode()
            else:
                content = email_message.get_payload(decode=True).decode()

            new_emails.append({
                'message_id': email_message['Message-ID'],
                'sender': sender,
                'subject': email_message['Subject'],
                'content': content,
                'uid': num
            })
        
        return new_emails

    def generate_response(self, email_data: Dict) -> str:
        """Generate response using Claude API."""
        system_prompt = self.config['system_prompt']
        email_context = f"""
        From: {email_data['sender']}
        Subject: {email_data['subject']}
        Content: {email_data['content']}
        """
        
        # Include relevant conversation history
        history_context = self._get_relevant_history(email_data['sender'])
        
        message = self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Previous conversations with this sender:\n{history_context}\n\nNew email to respond to:\n{email_context}"
                }
            ]
        )
        
        return message.content

    def _get_relevant_history(self, sender: str) -> str:
        """Get relevant conversation history for a sender."""
        relevant_history = [
            conv for conv in self.history 
            if conv['sender'] == sender
        ][-5:]  # Get last 5 conversations
        
        return "\n\n".join([
            f"Subject: {conv['subject']}\nResponse: {conv['response']}"
            for conv in relevant_history
        ])

    def save_draft(self, email_data: Dict, response: str):
        """Save response as draft."""
        draft = EmailMessage()
        draft['From'] = self.config['email']
        draft['To'] = email_data['sender']
        draft['Subject'] = f"Re: {email_data['subject']}"
        draft.set_content(response)

        self.imap.append('Drafts', '', imaplib.Time2Internaldate(time.time()), str(draft).encode('utf-8'))

    def update_history(self, email_data: Dict, response: str):
        """Update conversation history."""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'sender': email_data['sender'],
            'subject': email_data['subject'],
            'response': response
        })
        self.save_history()

    def run(self, interval: int = 300):
        """Run the email assistant with specified check interval."""
        while True:
            try:
                print(f"Checking for new emails at {datetime.now()}")
                new_emails = self.get_new_emails()
                
                for email_data in new_emails:
                    print(f"Processing email from {email_data['sender']}")
                    response = self.generate_response(email_data)
                    self.save_draft(email_data, response)
                    self.update_history(email_data, response)
                    print(f"Draft saved for email from {email_data['sender']}")
                
                time.sleep(interval)
            except Exception as e:
                print(f"Error occurred: {e}")
                time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    assistant = EmailAssistant()
    assistant.run()
