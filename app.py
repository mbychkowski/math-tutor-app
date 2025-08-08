"""
A multi-backend Gradio boilerplate for conversational AI.

This application can connect to:
1. A standard Gemini model on Vertex AI.
2. A custom model deployed to a Vertex AI Endpoint.
3. A self-hosted model running on Google Kubernetes Engine (GKE).

It demonstrates best practices such as:
- Dynamic model switching via a UI component.
- Modular functions for each backend.
- Streaming responses where available.
- Configuration-driven setup for endpoints and keys.
"""

import os
import gradio as gr
import httpx
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud.aiplatform import Endpoint

# --- General Configuration ---
# IMPORTANT: Set these values to your Google Cloud project and location.
GCP_PROJECT_ID = "YOU_GCP_PROJECT"
GCP_LOCATION = "us-central1"  # e.g., "us-central1"

# --- Vertex AI Custom Endpoint Configuration ---
# The ID of your deployed custom model endpoint in Vertex AI
VERTEX_AI_CUSTOM_ENDPOINT_ID = "YOUR_VERTEX_AI_ENDPOINT_ID_HERE"

# --- GKE Self-Hosted Model Configuration ---
# The full URL of your model's prediction endpoint on GKE
GKE_MODEL_ENDPOINT_URL = "http://your-gke-service.example.com/predict"
# An optional API key for your GKE service (leave as None if not needed)
GKE_MODEL_API_KEY = os.getenv("GKE_MODEL_API_KEY", None)


# --- Initialization ---
if GCP_PROJECT_ID == "YOUR_GCP_PROJECT_ID_HERE":
    # This will be caught by the chat handler to display a nice error in the UI
    # instead of crashing the application on startup.
    print("🔴 WARNING: GCP_PROJECT_ID is not set. The application will not work correctly.")
    print("Please update the GCP_PROJECT_ID in your app.py file.")

# Initialize the Vertex AI client
vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)

# --- Model Backend Logic ---

async def chat_with_vertex_gemini(message: str):
    """Handles chat with a standard Gemini model on Vertex AI."""
    model = GenerativeModel("gemini-2.5-pro")
    chat = model.start_chat()
    response = chat.send_message(message, stream=True)
    for chunk in response:
        if chunk.text:
            yield chunk.text

async def chat_with_vertex_custom_model(message: str):
    """Handles chat with a custom model on a Vertex AI Endpoint."""
    if VERTEX_AI_CUSTOM_ENDPOINT_ID == "YOUR_VERTEX_AI_ENDPOINT_ID_HERE":
        yield "🔴 Please configure the VERTEX_AI_CUSTOM_ENDPOINT_ID."
        return

    try:
        endpoint = Endpoint(VERTEX_AI_CUSTOM_ENDPOINT_ID)
        # IMPORTANT: The 'instances' payload structure depends entirely on your
        # custom model's expected input format. You must modify this.
        # This example assumes a JSON structure that includes the history.
        instances = [{"prompt": message, "history": gemini_history}]

        # Use stream_predict for streaming responses. If your model doesn't
        # support streaming, use endpoint.predict() instead.
        response_stream = endpoint.stream_predict(instances=instances)
        for response in response_stream:
            # IMPORTANT: The response structure is also specific to your model.
            # Modify this line to correctly extract the text from the response.
            yield response.text
    except Exception as e:
        yield f"Error calling Vertex AI Endpoint: {e}"

async def chat_with_gke_model(message: str):
    """
    Handles chat with a self-hosted model on GKE using an async HTTP client.
    """
    if GKE_MODEL_ENDPOINT_URL == "http://your-gke-service.example.com/predict":
        yield "🔴 Please configure the GKE_MODEL_ENDPOINT_URL."
        return

    headers = {"Content-Type": "application/json"}
    if GKE_MODEL_API_KEY:
        headers["Authorization"] = f"Bearer {GKE_MODEL_API_KEY}"

    # IMPORTANT: The payload structure depends on your GKE model's API. Modify
    # this to match what your model expects.
    payload = {"prompt": message, "stream": True}

    try:
        # Use an async client for non-blocking I/O, which is better for Gradio
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", GKE_MODEL_ENDPOINT_URL, json=payload, headers=headers) as response:
                response.raise_for_status()
                # IMPORTANT: How you iterate over a streaming response depends on
                # your model's implementation. This example assumes newline-delimited text.
                async for line in response.aiter_lines():
                    if line:
                        yield line
    except httpx.HTTPStatusError as e:
        yield f"Error calling GKE model: Received status {e.response.status_code}"
    except httpx.RequestError as e:
        yield f"Error calling GKE model: {e}"

# --- Gradio UI and Dispatch Logic ---

# A mapping from the UI choice to the backend function
MODEL_DISPATCHER = {
    "Vertex AI (Gemini)": chat_with_vertex_gemini,
    "Vertex AI (Custom Endpoint)": chat_with_vertex_custom_model,
    "Self-Hosted (GKE)": chat_with_gke_model,
}

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky"),
    css=".gradio-container {max-width: 800px; margin: auto;}"
) as demo:
    gr.Markdown(
        """
        # 🤖 Multi-Backend Chat
        Select a model backend and start a conversation.
        """
    )

    with gr.Row():
        model_choice = gr.Radio(
            list(MODEL_DISPATCHER.keys()),
            label="Choose a Model Backend",
            value="Vertex AI (Gemini)"
        )

    async def chat_handler(message: str, history: list, model: str):
        chat_function = MODEL_DISPATCHER.get(model)
        if chat_function:
            # Use 'async for' since all our chat functions are now async generators
            async for chunk in chat_function(message, history):
                yield chunk
        else:
            yield "🔴 Invalid model selection."

    gr.ChatInterface(
        fn=chat_handler,
        additional_inputs=[model_choice],
        flagging_mode="manual",
        examples=[
            ["What are the main components of a Kubernetes cluster?", "Vertex AI (Gemini)"],
            ["Explain the concept of a Vertex AI Endpoint.", "Vertex AI (Custom Endpoint)"],
        ],
        title="Math Tutor",
    )

# --- Application Entry Point ---
if __name__ == "__main__":
    demo.launch(debug=True)
