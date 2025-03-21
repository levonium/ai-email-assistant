#!/usr/bin/env python3
import sys
import logging
from logging.handlers import RotatingFileHandler
import traceback
import time
import signal
import yaml
from typing import Dict, Optional

# Global variables for health check
start_time = time.time()
last_error_time: Optional[float] = None
last_error_message: Optional[str] = None

def validate_config(config: Dict) -> None:
    """Validate required configuration."""
    required_fields = ['email', 'password', 'imap_server']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required configuration: {field}")

    # Validate API keys based on model selection
    if 'openai_model_name' in config and 'openai_api_key' not in config:
        raise ValueError("OpenAI API key is required when using OpenAI models")
    if 'claude_model_name' in config and 'anthropic_api_key' not in config:
        raise ValueError("Anthropic API key is required when using Claude models")
    if 'gemini_model_name' in config and 'google_api_key' not in config:
        raise ValueError("Google API key is required when using Gemini models")

def health_check() -> Dict:
    """Simple health check endpoint."""
    return {
        'status': 'healthy',
        'uptime': time.time() - start_time,
        'last_error': {
            'time': last_error_time,
            'message': last_error_message
        } if last_error_time else None
    }

def setup_logging():
    """Setup logging configuration"""
    logger = logging.getLogger('EmailAssistant')
    logger.setLevel(logging.INFO)

    # Create handlers
    file_handler = RotatingFileHandler(
        '/var/log/email-assistant/email-assistant.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    console_handler = logging.StreamHandler(sys.stdout)

    # Create formatters and add it to handlers
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(log_format)
    console_handler.setFormatter(log_format)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def load_config(config_path: str = 'config.yaml') -> Dict:
    """Load and validate configuration."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        validate_config(config)
        return config
    except Exception as e:
        raise ValueError(f"Configuration error: {str(e)}")

def shutdown_handler(signum: int, frame: Optional[object], logger: logging.Logger, assistant: Optional[object] = None):
    """Handle graceful shutdown."""
    # Prevent multiple shutdown calls
    if hasattr(shutdown_handler, 'called'):
        return
    shutdown_handler.called = True

    logger.info(f"Received shutdown signal {signum}, stopping service...")
    if assistant and hasattr(assistant, 'imap'):
        try:
            assistant.imap.logout()
        except Exception as e:
            logger.error(f"Error during IMAP logout: {str(e)}")
    sys.exit(0)

def main():
    """Main service entry point."""
    global last_error_time, last_error_message

    logger = setup_logging()
    logger.info("Starting Email Assistant service")

    try:
        # Load and validate configuration
        config = load_config()
        logger.info(f"Loaded configuration for email: {config['email']}")
        logger.info(f"Using IMAP server: {config['imap_server']}")

        # Import and initialize the appropriate assistant
        if 'openai_model_name' in config:
            from email_assistant_openai import EmailAssistant as OpenAIEmailAssistant
            assistant = OpenAIEmailAssistant()
            logger.info("Initialized OpenAI Email Assistant")
        elif 'claude_model_name' in config:
            from email_assistant_anthropic import EmailAssistant as ClaudeEmailAssistant
            assistant = ClaudeEmailAssistant()
            logger.info("Initialized Claude Email Assistant")
        elif 'gemini_model_name' in config:
            from email_assistant_google import EmailAssistant as GeminiEmailAssistant
            assistant = GeminiEmailAssistant()
            logger.info("Initialized Google Gemini Email Assistant")
        else:
            raise ValueError("No AI model specified in configuration")

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            shutdown_handler(signum, frame, logger, assistant)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        while True:
            try:
                logger.info("Running Email Assistant main loop")
                assistant.run()
            except Exception as e:
                last_error_time = time.time()
                last_error_message = str(e)
                logger.error(f"Error in main loop: {str(e)}")
                logger.error(traceback.format_exc())
                logger.info("Restarting in 60 seconds...")
                time.sleep(60)

    except Exception as e:
        last_error_time = time.time()
        last_error_message = str(e)
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
