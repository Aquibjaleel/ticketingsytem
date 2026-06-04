#!/bin/sh

# Ensure variables are available to the shell
export SECRET_KEY=${SECRET_KEY}
export DB_USERNAME=${DB_USERNAME}
export DB_PASSWORD=${DB_PASSWORD}
export DB_URL=${DB_URL}
export DB_NAME=${DB_NAME}
export AI_API_KEY=${AI_API_KEY}
export AI_ENDPOINT=${AI_ENDPOINT}

# Create the file
cat <<EOF > /app/config.json
{
  "SECRET_KEY": "$SECRET_KEY",
  "db_username": "$DB_USERNAME",
  "db_password": "$DB_PASSWORD",
  "db_url": "$DB_URL",
  "db_name": "$DB_NAME",
  "ai_api_key": "$AI_API_KEY",
  "ai_endpoint": "$AI_ENDPOINT",
  "ai_provider": "openai"
}
EOF

# Verify it was created
if [ ! -f /app/config.json ]; then
    echo "Error: config.json was not created!"
    exit 1
fi

echo "Config file created successfully. Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 application:app