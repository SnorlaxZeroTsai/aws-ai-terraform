#!/bin/bash
set -e

echo "Starting AI Agent Platform Orchestrator..."
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${AWS_REGION}"
echo "Port: ${CONTAINER_PORT}"

# Wait for dependencies if needed
# if [ -n "$WAIT_FOR" ]; then
#     echo "Waiting for $WAIT_FOR..."
#     /wait-for-it.sh $WAIT_FOR -t 30
# fi

# Run any startup scripts
if [ -f "/app/scripts/startup.sh" ]; then
    echo "Running startup script..."
    bash /app/scripts/startup.sh
fi

# Execute the main command
exec "$@"
