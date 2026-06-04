#!/bin/sh


cat <<EOF > /app/config.json
{
  "SECRET_KEY": "${SECRET_KEY}",
  "db_username": "${DB_USERNAME}",
  "db_password": "${DB_PASSWORD}",
  "db_url": "${DB_URL}",
  "db_name": "${DB_NAME}",
  "ai_api_key": "${AI_API_KEY}",
  "ai_endpoint": "${AI_ENDPOINT}",
  "ai_provider": "openai"
}
EOF

exec gunicorn --bind 0.0.0.0:5000 application:app