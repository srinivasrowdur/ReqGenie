FROM python:3.11-slim

WORKDIR /app

# Install git for swarm installation
RUN apt-get update && apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application (will exclude files in .dockerignore)
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 8080

# Run streamlit directly
CMD streamlit run --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.serverAddress=0.0.0.0 \
    genie.py