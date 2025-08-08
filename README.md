# Multi-Backend Gradio Chat Application

This project is a boilerplate for a conversational AI chat application with a Gradio-based web interface. It is designed to be flexible and can connect to multiple model backends, allowing you to easily switch between them.

## Features

- **Multiple Backends**: Seamlessly switch between three different model backends:
    1.  A standard **Gemini** model on Vertex AI.
    2.  A custom model deployed to a **Vertex AI Endpoint**.
    3.  A self-hosted model running on **Google Kubernetes Engine (GKE)**.
- **Modern UI**: A clean and responsive chat interface powered by Gradio.
- **Streaming Support**: Demonstrates how to handle streaming responses for a real-time chat experience.
- **Secure Authentication**: Uses Google Cloud's Application Default Credentials (ADC) for secure access to Vertex AI.
- **Configuration-Driven**: Easily configure endpoints and project settings in a single file.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**
- **pip** (Python package installer)
- **Google Cloud SDK** (the `gcloud` command-line tool)

## Setup and Installation

Follow these steps to get the application running on your local machine.

### 1. Get the Code

If you are working with a Git repository, clone it. Otherwise, make sure you have the project files (`app.py`, `requirements.txt`) in a dedicated directory.

### 2. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment named 'venv'
python3 -m venv .venv

# Activate the virtual environment
# On macOS and Linux:
source .venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

Install the required Python packages using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Authenticate with Google Cloud

You need to authenticate your local environment to allow the application to access your Google Cloud resources (like Vertex AI).

Run the following command and follow the prompts to log in with your Google account:

```bash
gcloud auth application-default login
```

## Configuration

This is the most important step. You must configure the application to point to your specific models and cloud project.

Open the `app.py` file and edit the configuration variables at the top of the file.

### General Configuration

```python
# The Google Cloud project ID where your models are hosted.
GCP_PROJECT_ID = "your-gcp-project-id-here"

# The Google Cloud location for your project.
GCP_LOCATION = "us-central1"
```

### Vertex AI Custom Endpoint

If you plan to use a custom model deployed on a Vertex AI Endpoint, you must provide its ID. You can find this in the Google Cloud Console under **Vertex AI > Endpoints**.

```python
# The ID of your deployed custom model endpoint in Vertex AI
VERTEX_AI_CUSTOM_ENDPOINT_ID = "1234567890123456789"
```

### GKE Self-Hosted Model

If you are connecting to a model you've deployed on GKE, provide its full prediction URL.

```python
# The full URL of your model's prediction endpoint on GKE
GKE_MODEL_ENDPOINT_URL = "http://your-gke-service.example.com/predict"

# (Optional) If your GKE service requires an API key for authorization,
# set it as an environment variable for security.
# In your terminal:
# export GKE_MODEL_API_KEY="your-secret-key"
```

### **IMPORTANT: Adapt API Payloads**

The boilerplate code includes placeholder logic for sending data to your custom models. **You must modify `app.py` to match the specific API contract of your models.**

-   **For the Vertex AI Custom Model** (in `chat_with_vertex_custom_model`):
    -   Update the `instances` dictionary to match your model's expected input format.
    -   Update the logic that parses the `response` to correctly extract the generated text.
-   **For the GKE Model** (in `chat_with_gke_model`):
    -   Update the `payload` dictionary to match what your model's API expects.
    -   The streaming logic assumes a simple newline-delimited stream. You may need to change this if your model uses a different protocol (e.g., Server-Sent Events).

## Running the Application

Once you have completed the configuration, you can run the application.

```bash
python app.py
```

The application will start, and you will see a local URL in your terminal (e.g., `http://127.0.0.1:7860`). Open this URL in your web browser to access the chat interface. You can now select a model backend from the radio buttons and start a conversation.
