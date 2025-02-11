# Use official Python image
FROM python:3.9

# Set working directory inside the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script into the container
COPY ig404.py .

# Run the script
CMD ["python", "ig404.py"]