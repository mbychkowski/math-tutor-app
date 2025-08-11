# Use an official Python runtime as a parent image
FROM python:3.9-slim

ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT=7860

# Set the working directory in the container
WORKDIR /app

# Copy the source code into the container
# This assumes you have moved your app and requirements into a 'src' directory
COPY src/ /app/src/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /app/src/requirements.txt

# Cloud Run automatically sets the PORT environment variable
# and expects the container to listen on that port.
# We will configure this in app.py.
EXPOSE $GRADIO_SERVER_PORT

# Run the application
CMD ["python", "src/app.py"]
