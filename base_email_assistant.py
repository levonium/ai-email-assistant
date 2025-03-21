import imaplib
import email
import os
from email.message import EmailMessage
from datetime import datetime
import json
import time
from typing import List, Dict
import yaml
from abc import ABC, abstractmethod

class BaseEmailAssistant(ABC):
    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize the email assistant with configuration."""
        self.load_config(config_path)
        self.connect_imap()
        self.load_history()
        self.load_training_context()

    def load_config(self, config_path: str):
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def connect_imap(self):
        """Connect to IMAP server."""
        self.imap = imaplib.IMAP4_SSL(self.config['imap_server'])
        self.imap.login(self.config['email'], self.config['password'])
        self.imap.select('INBOX')

    def load_training_context(self):
        """Load training context from JSON file."""
        try:
            with open('training_context.json', 'r') as f:
                self.training_context = json.load(f)
        except FileNotFoundError:
            self.training_context = {
                'system_prompt': self.config.get('system_prompt', ''),
                'additional_instructions': [],
                'example_responses': []
            }
            self.save_training_context()

    def save_training_context(self):
        """Save training context to JSON file."""
        with open('training_context.json', 'w') as f:
            json.dump(self.training_context, f, indent=2)

    def add_instruction(self, instruction: str):
        """Add a new instruction to the training context."""
        self.training_context['additional_instructions'].append({
            'timestamp': datetime.now().isoformat(),
            'instruction': instruction
        })
        self.save_training_context()
        print(f"Added new instruction to training context")

    def add_example_response(self, email_data: Dict, final_response: str):
        """Add a final response as an example to learn from."""
        self.training_context['example_responses'].append({
            'timestamp': datetime.now().isoformat(),
            'sender': email_data['sender'],
            'subject': email_data['subject'],
            'original_content': email_data['content'],
            'response': final_response
        })
        self.save_training_context()
        print(f"Added final response to training examples")

    def get_new_emails(self, search_criteria: str = 'UNSEEN') -> List[Dict]:
        """Get new emails based on search criteria."""
        emails = []
        _, message_numbers = self.imap.search(None, search_criteria)

        for num in message_numbers[0].split():
            try:
                _, msg_data = self.imap.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)

                # Skip blacklisted senders
                sender = email_message['from']
                if any(blacklisted in sender.lower() for blacklisted in self.config.get('blacklist', [])):
                    continue

                # Skip blacklisted reply-tos if present
                reply_to = email_message.get('reply-to')
                if reply_to and any(blacklisted in reply_to.lower() for blacklisted in self.config.get('blacklist', [])):
                    continue

                # Extract email content
                content = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            content = part.get_payload(decode=True).decode()
                            break
                else:
                    content = email_message.get_payload(decode=True).decode()

                emails.append({
                    'uid': num.decode(),
                    'sender': sender,
                    'subject': email_message['subject'],
                    'content': content
                })
            except Exception as e:
                print(f"Error processing email {num}: {str(e)}")
                continue

        return emails

    def save_draft(self, email_data: Dict, response: str):
        """Save response as draft."""
        try:
            # Create the draft message
            draft = EmailMessage()
            draft['To'] = email_data['sender']
            draft['From'] = self.config['email']
            draft['Subject'] = f"Re: {email_data['subject']}"
            draft.set_content(response)

            # Try common draft folder names
            draft_folders = ['Drafts', 'Draft', '[Gmail]/Drafts', 'INBOX/Drafts']
            saved = False

            for folder in draft_folders:
                try:
                    self.imap.select(folder)
                    self.imap.append(folder, '\\Draft', imaplib.Time2Internaldate(time.time()), str(draft).encode())
                    print(f"Draft saved to {folder} folder for email from {email_data['sender']}")
                    saved = True
                    break
                except:
                    continue

            if not saved:
                # If no drafts folder works, save to INBOX
                self.imap.select('INBOX')
                self.imap.append('INBOX', '\\Draft', imaplib.Time2Internaldate(time.time()), str(draft).encode())
                print(f"Draft saved to INBOX for email from {email_data['sender']}")

            # Go back to INBOX
            self.imap.select('INBOX')
        except Exception as e:
            print(f"Error saving draft: {str(e)}")
            import traceback
            print(f"Full error: {traceback.format_exc()}")

    def mark_as_read(self, uid: str):
        """Mark email as read."""
        self.imap.store(uid, '+FLAGS', '(\Seen)')

    def load_history(self):
        """Load conversation history from JSON file."""
        try:
            with open('conversation_history.json', 'r') as f:
                self.history = json.load(f)
        except FileNotFoundError:
            self.history = {}
            self.save_history()

    def save_history(self):
        """Save conversation history to JSON file."""
        with open('conversation_history.json', 'w') as f:
            json.dump(self.history, f, indent=2)

    def update_history(self, email_data: Dict, response: str):
        """Update conversation history with new interaction."""
        sender = email_data['sender']
        if sender not in self.history:
            self.history[sender] = []

        self.history[sender].append({
            'timestamp': datetime.now().isoformat(),
            'subject': email_data['subject'],
            'content': email_data['content'],
            'response': response
        })
        self.save_history()

    def _get_relevant_history(self, sender: str) -> str:
        """Get relevant conversation history for a sender."""
        if sender not in self.history:
            return "No previous conversations found."

        # Get last 5 conversations
        recent_history = self.history[sender][-5:]
        history_text = ""

        for conv in recent_history:
            history_text += f"Subject: {conv['subject']}\n"
            history_text += f"Original: {conv['content']}\n"
            history_text += f"Response: {conv['response']}\n\n"

        return history_text

    @abstractmethod
    def generate_response(self, email_data: Dict) -> str:
        """Generate response using AI. Must be implemented by child classes."""
        pass

    def run(self, interval: int = 300, search_criteria: str = 'UNSEEN'):
        """Run the email assistant with specified check interval."""
        while True:
            try:
                print(f"Checking for new emails at {datetime.now()}")
                new_emails = self.get_new_emails(search_criteria)

                for email_data in new_emails:
                    try:
                        print(f"Processing email from {email_data['sender']}")
                        response = self.generate_response(email_data)
                        if response and not response.startswith("Error generating"):
                            self.save_draft(email_data, response)
                            self.update_history(email_data, response)

                            if self.config.get('mark_as_read', True):
                                self.mark_as_read(email_data['uid'])

                            print(f"Draft saved for email from {email_data['sender']}")
                        else:
                            print(f"Skipping draft save due to error for {email_data['sender']}")
                    except Exception as e:
                        print(f"Error processing email from {email_data['sender']}: {str(e)}")
                        continue

                time.sleep(interval)
            except Exception as e:
                print(f"Error occurred in main loop: {str(e)}")
                import traceback
                print(f"Full error: {traceback.format_exc()}")
                time.sleep(60)  # Wait a minute before retrying
