# Use official Python slim image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Prevent Python from writing pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Use the script as the container entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Install system dependencies (needed for some Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .


# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# Copy the rest of the project files
COPY . .

# Expose the port your app will run on
EXPOSE 8000

# Run the app using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]