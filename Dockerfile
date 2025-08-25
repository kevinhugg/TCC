# Use a specific, slim version of Python for smaller and more predictable images
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by Python packages
# For example, xhtml2pdf needs libraries for font rendering
RUN apt-get update && apt-get install -y \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker's layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application
CMD ["python", "app.py"]
