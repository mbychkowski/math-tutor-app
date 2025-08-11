# Multi-Backend Gradio Chat Application

This project is a boilerplate for a conversational AI chat application with a Gradio-based web interface. It is designed to be flexible and can connect to multiple model backends, allowing you to easily switch between them.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**
- **pip** (Python package installer)
- **Google Cloud SDK** (the `gcloud` command-line tool)
- **Multiple Backends pre-configured**: This app seamlessly switches between three different model backends:
    1.  A standard **Gemini** model on Vertex AI.
    2.  A custom model deployed to a **Vertex AI Endpoint**.
    3.  A self-hosted model running on **Google Kubernetes Engine (GKE)**.

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
# .venv\Scripts\activate
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

This is the most important step. All configuration is handled via a `.env` file to keep your secrets and settings out of the source code.

1.  **Create your `.env` file**:
    Copy the example file to create your own local configuration file. The `.env` file is listed in `.gitignore` and will not be committed to your repository.
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file**:
    Open the newly created `.env` file and fill in the values for your Google Cloud project and model endpoints.

    - `GCP_PROJECT_ID`: Your Google Cloud project ID.
    - `GCP_LOCATION`: The region for your project (e.g., `us-central1`).
    - `VERTEX_AI_GEMINI_MODEL_NAME`: The name of your Gemini model on Vertex AI (e.g. `gemini-2.5-flash`).
    - `VERTEX_AI_CUSTOM_ENDPOINT_ID`: The ID of your custom model on a Vertex AI Endpoint. You can find this in the Cloud Console.
    - `GKE_MODEL_ENDPOINT_URL`: The full prediction URL for your model hosted on GKE.

### **IMPORTANT: Adapt API Payloads**

The boilerplate code includes placeholder logic for sending data to your custom models. **You must modify `app.py` to match the specific API contract of your models.**

-   **For the Vertex AI Custom Model** (in `chat_with_vertex_custom_model`):
    -   Update the `instances` dictionary to match your model's expected input format.
    -   Update the logic that parses the `response` to correctly extract the generated text.
-   **For the GKE Model** (in `chat_with_gke_model`):
    -   Update the `payload` dictionary to match what your model's API expects.
    -   The streaming logic assumes a simple newline-delimited stream. You may need to change this if your model uses a different protocol (e.g., Server-Sent Events).

## Running the Application

Once your configuration is set, you are ready to launch the application.

### 1. Ensure Configuration is Ready

Before you start, double-check that you have:
- Activated your Python virtual environment (`source .venv/bin/activate`).
- Created and correctly filled out your `.env` file with your project and endpoint details.

### 2. Launch the App

We recommend using the `gradio` command to run the application, as it provides helpful features like automatic reloading when you change the code.

```bash
gradio app.py
```

Alternatively, you can run the application using the standard Python interpreter:

```bash
python app.py
```

### 3. Access the Interface

Once the application is running, you will see output in your terminal similar to this:

```
Running on local URL:  http://127.0.0.1:7860
```

Open the local URL in your web browser to access the chat interface. You can now select a model backend from the radio buttons and start a conversation.

## Troubleshooting

Here are a few common issues you might encounter:

*   **Authentication Errors**: If you see errors related to permissions or credentials (e.g., `PermissionDenied: 403`), it usually means your local environment is not authenticated correctly with Google Cloud.
    *   **Solution**: Re-run `gcloud auth application-default login` and ensure you are logged in with an account that has the "Vertex AI User" role on your GCP project.

*   **Model Not Found / Endpoint Not Found**: If you get an error saying a model or endpoint could not be found, double-check your `.env` file.
    *   **Solution**: Ensure that `GCP_PROJECT_ID`, `VERTEX_AI_CUSTOM_ENDPOINT_ID`, and other configuration variables are correct and do not have any typos.

*   **Incorrect API Response**: If the application runs but you get unexpected output or errors when you chat with a custom model, it's likely that the API payload in `app.py` does not match what your model expects.
    *   **Solution**: As mentioned in the "Configuration" section, you must adapt the `instances` payload and the response parsing logic in the `chat_with_vertex_custom_model` and `chat_with_gke_model` functions to match your specific model's API contract.

## Deploying to Cloud Run

This application is configured for automated deployment to Google Cloud Run using Cloud Build.

To build and deploy the application, run the following command from the root of the project directory:

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_LOCATION="us-central1",_REPOSITORY="ai-crash-lab",_IMAGE="math-tutor",_SERVICE_NAME="math-tutor-service",_REGION="us-central1"
```

This command will:
1.  Submit the current directory to Google Cloud Build.
2.  Execute the steps defined in `cloudbuild.yaml`.
3.  Build the Docker container image.
4.  Push the image to Google Artifact Registry.
5.  Deploy the image to a new or existing service on Cloud Run.

Once the deployment is complete, Cloud Build will output the URL of your deployed service.