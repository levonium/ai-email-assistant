# Email Assistant Bot

An intelligent email assistant that processes incoming emails and generates responses using AI (OpenAI GPT or Anthropic Claude). The bot reads emails via IMAP, generates appropriate responses, and saves them as drafts. It features a learning system that improves responses based on your instructions and examples.

## Features

- **Email Processing**:
  - Monitors inbox for new unread emails
  - Filters emails using customizable blacklist
  - Supports different IMAP search criteria
  - Marks emails as read/unread
  - Saves generated responses as drafts

- **AI Integration**:
  - Supports both OpenAI GPT and Anthropic Claude
  - Customizable system prompts
  - Temperature and token limit controls
  - Conversation history tracking

- **Learning Capabilities**:
  - Persistent training context
  - Add new instructions while running
  - Learn from your final edited responses
  - Maintains conversation history per sender

## Prerequisites

- Python 3.7+
- Email account with IMAP access
- API key from OpenAI or Anthropic

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd email-assistant
```

2. Install required packages:
```bash
# For OpenAI version
pip install openai pyyaml

# For Claude version
pip install anthropic pyyaml
```

3. Create a configuration file `config.yaml`:
```yaml
# For OpenAI version
email: "your.email@example.com"
password: "your-email-password"
imap_server: "imap.gmail.com"
openai_api_key: "your-openai-api-key"
model_name: "gpt-4-turbo-preview"  # or "gpt-3.5-turbo"
max_tokens: 1000
temperature: 0.7
mark_as_read: true
blacklist:
  - "spam@example.com"
  - "newsletter@"
  - "noreply@"
system_prompt: |
  Your initial system prompt here...

# For Claude version
email: "your.email@example.com"
password: "your-email-password"
imap_server: "imap.gmail.com"
anthropic_api_key: "your-anthropic-api-key"
model_name: "claude-3-opus-20240229"
max_tokens: 1000
temperature: 0.7
mark_as_read: true
blacklist:
  - "spam@example.com"
  - "newsletter@"
  - "noreply@"
system_prompt: |
  Your initial system prompt here...
```

## Usage

### Basic Usage

1. Start the assistant:
```bash
# For OpenAI version
python email_assistant_oai.py

# For Claude version
python email_assistant_claude.py
```

2. The bot will:
   - Check for new unread emails every 5 minutes (configurable)
   - Generate responses using the AI model
   - Save responses as drafts
   - Mark processed emails as read (configurable)

### Advanced Usage

#### Adding New Instructions

You can add new instructions while the bot is running:

```python
assistant = EmailAssistant()
assistant.add_instruction("When responding to technical questions, include code examples.")
```

#### Adding Final Responses for Learning

After editing and sending a final response:

```python
assistant.add_example_response(
    email_data,  # Original email data
    "Your final edited and sent response"
)
```

#### Customizing Search Criteria

You can customize how the bot searches for emails:

```python
# Check only unread emails (default)
assistant.run(search_criteria='UNSEEN')

# Check unread emails from a specific sender
assistant.run(search_criteria='UNSEEN FROM "important@example.com"')

# Check unread emails since a specific date
assistant.run(search_criteria='UNSEEN SINCE "01-Jan-2024"')
```

## File Structure

- `email_assistant_oai.py`: OpenAI version of the assistant
- `email_assistant_claude.py`: Claude version of the assistant
- `config.yaml`: Configuration file
- `training_context.json`: Stores learning context (created automatically)
- `conversation_history.json`: Stores conversation history (created automatically)

## Gmail Setup

For Gmail accounts, you'll need to:
1. Enable IMAP in Gmail settings
2. Create an App Password if using 2FA
3. Use the App Password in your config.yaml

## Security Notes

- Store your API keys and email credentials securely
- Never commit config.yaml with real credentials
- Consider using environment variables for sensitive data
- Review generated responses before sending

## Contributing

Feel free to submit issues and pull requests for:
- Bug fixes
- New features
- Documentation improvements
- Code optimization

## License

MIT License - feel free to use and modify as needed.
