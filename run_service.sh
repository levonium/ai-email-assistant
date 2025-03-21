#!/bin/bash

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project directory
cd "$DIR"

# Activate virtual environment
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the email assistant service in the background and redirect output to a log file
python3 email_assistant_service.py > logs/email_assistant.log 2>&1 &

# Save the process ID
echo $! > logs/email_assistant.pid

echo "Email assistant service started with PID $(cat logs/email_assistant.pid)"
