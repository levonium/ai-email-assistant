# Email Assistant

An intelligent email assistant that processes incoming emails and generates responses using AI (OpenAI GPT, Anthropic Claude or Google Gemini). The service reads emails through IMAP, generates appropriate responses, and saves them as drafts if necessary. It features a learning system that improves responses based on your instructions and examples.

Cloned from [dmrrlc/ai-email-responder](https://github.com/dmrrlc/ai-email-responder)

## Features

- **Email Processing**:

  - Monitors inbox for new unread emails
  - Filters emails using customizable rules
  - Marks processed emails as read
  - Saves generated responses as drafts

- **AI Integration**:

  - Supports OpenAI GPT, Anthropic Claude and Google Gemini
  - Customizable system prompts
  - Temperature and token limit controls
  - Conversation history tracking
  - Context-aware responses using previous interactions

- **Learning Capabilities**:

  - Persistent training context
  - Add new instructions while running
  - Learn from your final edited responses
  - Maintains conversation history per sender
  - Uses recent examples to improve responses

- **Service Management**:
  - Systemd service integration
  - Automatic restart on failure
  - Rotating log files
  - Health monitoring
  - Graceful shutdown handling

## Requirements

- Python 3.7+
- Email account with IMAP access
- API key from OpenAI, Anthropic or Google

## Installation

1. Clone the repository:

```bash
git clone [repository-url]
cd email-assistant
```

2. Install required packages:

```bash
source ./venv/bin/activate
pip install -r requirements.txt
```

3. Create a configuration file `config.yaml`:

Copy and modify the `config.example.yaml` file.

Keep either OpenAI, Anthropic or Google key and model values in the config file, that's what determines which service will be used.

## Usage

Start the assistant manually:

```bash
source ./venv/bin/activate
python3 email_assistant_service.py
```

Run the service in the background by setting up a cron job or use systemd. Use the `run_service.sh` file.

## File Structure

- `base_email_assistant.py`: Base class with shared functionality
- `email_assistant_anthropic.py`: Anthropic Claude version of the assistant
- `email_assistant_google.py`: Google Gemini version of the assistant
- `email_assistant_openai.py`: OpenAI GPT version of the assistant
- `email_assistant_service.py`: Service management
- `config.yaml`: Configuration file
- `training_context.json`: Stores learning context (created automatically)
- `conversation_history.json`: Stores conversation history (created automatically)

## Error Handling

The assistant includes comprehensive error handling:

- Graceful handling of API failures
- Automatic retry on network issues
- Detailed error logging
- Service health monitoring
- Draft saving fallback mechanisms
- Conversation history backup

## Logging Configuration

The assistant supports two logging configurations:

1. Development Mode (when running directly):

   - Logs are stored in the `logs` directory in the project root
   - Used when running with `run_service.sh`
   - Stores process ID in `logs/email_assistant.pid`
   - Redirects stdout/stderr to `logs/email_assistant.log`

2. Production Mode (when running as systemd service):
   - Logs are stored in `/var/log/email-assistant`
   - Used when running as a systemd service
   - Implements log rotation (10MB max size, 5 backup files)
   - Proper system logging integration
   - Better for production environments

## Security Notes

- Store your API keys and email credentials securely
- Never commit config.yaml with real credentials
- Consider using environment variables for sensitive data
- Review generated responses before sending
- Use App Passwords for Gmail and other accounts with 2FA
- Run service as non-root user
- Keep dependencies updated
