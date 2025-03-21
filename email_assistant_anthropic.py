from anthropic import Anthropic
from typing import Dict
from datetime import datetime
import time
from base_email_assistant import BaseEmailAssistant

class EmailAssistant(BaseEmailAssistant):
    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize the email assistant with Anthropic configuration."""
        super().__init__(config_path)
        self.anthropic = Anthropic(api_key=self.config['anthropic_api_key'])

    def generate_response(self, email_data: Dict) -> str:
        """Generate response using Claude API with full training context."""
        try:
            # Combine all instructions
            full_system_prompt = self.training_context['system_prompt'] + "\n\n"
            if self.training_context['additional_instructions']:
                full_system_prompt += "Additional Instructions:\n"
                for inst in self.training_context['additional_instructions']:
                    full_system_prompt += f"- {inst['instruction']}\n"

            # Create context from examples
            example_context = ""
            if self.training_context['example_responses']:
                recent_examples = sorted(
                    self.training_context['example_responses'],
                    key=lambda x: x['timestamp'],
                    reverse=True
                )[:5]  # Get 5 most recent examples

                example_context = "Recent example responses:\n\n"
                for ex in recent_examples:
                    example_context += f"Subject: {ex['subject']}\n"
                    example_context += f"Original: {ex['original_content']}\n"
                    example_context += f"Response: {ex['response']}\n\n"

            # Current email context
            email_context = f"""
            From: {email_data['sender']}
            Subject: {email_data['subject']}
            Content: {email_data['content']}
            """

            # Get conversation history for this sender
            history_context = self._get_relevant_history(email_data['sender'])

            # Combine all context
            full_context = f"{example_context}\n\nPrevious conversations with this sender:\n{history_context}\n\nNew email to respond to:\n{email_context}"

            response = self.anthropic.messages.create(
                model=self.config['claude_model_name'],
                system=full_system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": full_context
                    }
                ],
                max_tokens=self.config.get('max_tokens', 1000),
                temperature=self.config.get('temperature', 0.7)
            )

            # Extract the response content safely
            if hasattr(response, 'content'):
                if isinstance(response.content, list):
                    # If content is a list, join all text parts
                    return ' '.join(item.text for item in response.content if hasattr(item, 'text'))
                return str(response.content)
            else:
                # Fallback for different response structure
                return str(response.messages[0].content)

        except Exception as e:
            print(f"Error generating response: {str(e)}")
            # Log the full error details
            import traceback
            print(f"Full error: {traceback.format_exc()}")
            return "Error generating response. Please check the logs for details."

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

if __name__ == "__main__":
    assistant = EmailAssistant()

    # Example of how to add new instructions
    # assistant.add_instruction("When responding to technical questions, include code examples.")

    # Example of how to add a final response for learning
    # email_data = {...}  # Your email data
    # final_response = "Your actual sent response"
    # assistant.add_example_response(email_data, final_response)

    assistant.run()
