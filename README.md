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

    - `PROJECT_ID`: Your Google Cloud project ID.
    - `LOCATION`: The region for your project (e.g., `us-central1`).
    - `VERTEX_AI_GEMINI_MODEL_NAME`: The name of your Gemini model on Vertex AI (e.g. `gemini-2.5-flash`).
    - `VERTEX_AI_ENDPOINT_ID`: The ID of your custom model on a Vertex AI Endpoint. You can find this in the Cloud Console.
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
gradio src/app.py
```

Alternatively, you can run the application using the standard Python interpreter:

```bash
python src/app.py
```

### 3. Access the Interface

Once the application is running, you will see output in your terminal similar to this:

```
Running on local URL:  http://127.0.0.1:7860
```

Open the local URL in your web browser to access the chat interface. You can now select a model backend from the radio buttons and start a conversation.

### Updating Sample Questions

The sample questions that appear in the Gradio user interface can be customized.
To change them, edit the `src/sample_questions.txt` file. Each question should be on its own line.

The application will automatically load these questions on startup. If the file is not found or is empty, it will fall back to a default set of questions defined in `src/config.py`.

## Troubleshooting

Here are a few common issues you might encounter:

*   **Authentication Errors**: If you see errors related to permissions or credentials (e.g., `PermissionDenied: 403`), it usually means your local environment is not authenticated correctly with Google Cloud.
    *   **Solution**: Re-run `gcloud auth application-default login` and ensure you are logged in with an account that has the "Vertex AI User" role on your GCP project.

*   **Model Not Found / Endpoint Not Found**: If you get an error saying a model or endpoint could not be found, double-check your `.env` file.
    *   **Solution**: Ensure that `PROJECT_ID`, `VERTEX_AI_ENDPOINT_ID`, and other configuration variables are correct and do not have any typos.

*   **Incorrect API Response**: If the application runs but you get unexpected output or errors when you chat with a custom model, it's likely that the API payload in `app.py` does not match what your model expects.
    *   **Solution**: As mentioned in the "Configuration" section, you must adapt the `instances` payload and the response parsing logic in the `chat_with_vertex_custom_model` and `chat_with_gke_model` functions to match your specific model's API contract.

## Deploying to Cloud Run

Deploying to Cloud Run provides a scalable, serverless environment for your application. Below are two common methods for deployment.

# Make sure to set these environment variables first

```
export PROJECT_ID=$(gcloud config get-value project)
export LOCATION="us-central1" # Or your preferred region
```

### 1. One-Time Setup: Granting IAM Permissions

Before your first deployment, you must grant the default Compute Engine service account the necessary permissions to interact with Vertex AI. This allows your Cloud Run service to call the Gemini and custom model APIs.

```bash
# The $PROJECT_ID variable should be set to your Google Cloud Project ID
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### 2. Choose a Deployment Method

You can deploy directly from your local machine or automate the process using Cloud Build.

#### Option A: Direct Deployment from Source

This method builds and deploys your application in a single step, which is ideal for quick tests and iterative development.

The `gcloud run deploy` command with the `--source` flag tells Cloud Run to take your current directory, build a container image from it using the `Dockerfile`, and deploy that image to a new service.

```bash
gcloud run deploy math-tutor-service \
  --source ./ \
  --region $LOCATION \
  --port 7860 \
  --allow-unauthenticated \
  --set-env-vars=PROJECT_ID=$PROJECT_ID,LOCATION=$LOCATION,VERTEX_AI_ENDPOINT_ID=682668627744260096,GKE_INFERENCE_ENDPOINT_URL=http://127.0.0.1:8000/v1/chat/completions
```
**Note:** The `--allow-unauthenticated` flag makes the service publicly accessible. If you omit this, you will need to manually grant access after deployment.

#### Option B: Automated Deployment with Cloud Build

This method uses a `cloudbuild.yaml` configuration file to define a repeatable, automated build and deployment pipeline. This is the recommended approach for production environments.

`gcloud builds submit` sends your code to Cloud Build, which then executes the steps in your `cloudbuild.yaml` file. This process builds the Docker image, pushes it to Artifact Registry for storage, and then deploys it to Cloud Run, ensuring a consistent deployment every time.

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_LOCATION="us-central1",_SERVICE_NAME="math-tutor-service"
```
This command will use the substitutions defined in the `cloudbuild.yaml` file by default, but you can override them here if needed. You can also edit the `substitutions` block in `cloudbuild.yaml` directly to set default values.

Once complete, Cloud Build will output the URL of your deployed service.
