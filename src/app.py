import asyncio
import os
from typing import AsyncGenerator, List

import gradio as gr
import httpx
from dotenv import load_dotenv
from google.cloud.aiplatform import Endpoint
import vertexai
from vertexai.generative_models import Content, GenerativeModel, Part

import config

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
PROJECT_ID = os.getenv("PROJECT_ID", "YOUR_GCP_PROJECT_ID_HERE")
REGION = os.getenv("REGION", "us-central1")
VERTEX_AI_GEMINI_MODEL_NAME = os.getenv("VERTEX_AI_GEMINI_MODEL_NAME", "gemini-2.5-flash")
VERTEX_AI_ENDPOINT_ID = os.getenv("VERTEX_AI_ENDPOINT_ID", "YOUR_VERTEX_AI_ENDPOINT_ID_HERE")
GKE_INFERENCE_ENDPOINT_URL = os.getenv("GKE_INFERENCE_ENDPOINT_URL", "http://your-gke-service.example.com/v1/chat/completions")

# --- Initialization ---
if PROJECT_ID != "YOUR_GCP_PROJECT_ID_HERE":
    vertexai.init(project=PROJECT_ID, location=REGION)
else:
    print("⚠️ WARNING: PROJECT_ID is not set. The application will not work correctly.")

# --- Helper Function for History ---
def format_gemini_history(history: List[List[str]]):
    """Converts Gradio's history format to Gemini's format."""
    gemini_history = []
    for user_msg, model_msg in history:
        gemini_history.append(Content(role="user", parts=[Part.from_text(user_msg)]))
        gemini_history.append(Content(role="model", parts=[Part.from_text(model_msg)]))
    return gemini_history

# --- Model Backend Logic ---
async def chat_with_vertex_gemini(message: str, history: List[List[str]]):
    """Handles chat with a standard Gemini model on Vertex AI, maintaining history."""
    try:
        model = GenerativeModel(VERTEX_AI_GEMINI_MODEL_NAME)

        gemini_history = format_gemini_history(history)
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(message, stream=True)

        response_so_far = ""
        for chunk in response:
            if chunk.text:
                response_so_far += chunk.text

                yield history + [[message, response_so_far]]

    except Exception as e:
        error_msg = f"An error occurred with the Vertex AI Gemini model: {e}"
        yield history + [[message, error_msg]]

async def chat_with_vertex_custom_model(message: str, history: List[List[str]]):
    """Handles chat with a custom model on a Vertex AI Endpoint."""
    if VERTEX_AI_ENDPOINT_ID == "YOUR_VERTEX_AI_ENDPOINT_ID_HERE":
        yield history + [[message, "🚨 Please configure the VERTEX_AI_ENDPOINT_ID."]]
        return

    try:
        endpoint = Endpoint(VERTEX_AI_ENDPOINT_ID)
        instances = [{"prompt": message, "max_tokens": 512}]

        response = await asyncio.to_thread(endpoint.predict, instances=instances)

        full_response = ""
        for prediction in response.predictions:
            if isinstance(prediction, str):
                full_response += prediction

        yield history + [[message, full_response]]

    except Exception as e:
        error_msg = f"An error occurred with the Vertex AI custom model: {e}"
        yield history + [[message, error_msg]]

async def chat_with_gke_model(message: str, history: List[List[str]]):
    """Handles chat with a self-hosted model on GKE."""
    if GKE_INFERENCE_ENDPOINT_URL == "http://your-gke-service.example.com/v1/chat/completions":
        yield history + [[message, "🚨 Please configure the GKE_INFERENCE_ENDPOINT_URL."]]
        return

    payload = {"messages": [{"role": "user", "content": message}]}
    headers = {"Content-Type": "application/json"}
    final_response = ""

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(GKE_INFERENCE_ENDPOINT_URL, json=payload, headers=headers)
            response.raise_for_status()
            response_json = response.json()
            final_response = response_json["choices"][0]["message"]["content"]

        yield history + [[message, final_response]]

    except httpx.HTTPStatusError as e:
        final_response = f"Error: Received status {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        final_response = f"Error: Could not connect to GKE model: {e}"
    except (KeyError, IndexError):
        final_response = f"Error: Unexpected response format from GKE model."


# --- Main Chat Dispatcher ---
MODEL_DISPATCHER = {
    "Vertex AI (Gemini)": chat_with_vertex_gemini,
    "Vertex AI (self-hosted)": chat_with_vertex_custom_model,
    "GKE (self-hosted)": chat_with_gke_model,
}

async def chat_handler(message: str, history: List[List[str]], model: str):
    if PROJECT_ID == "YOUR_GCP_PROJECT_ID_HERE":
        yield history + [[message, "🚨 ERROR: GCP Project ID is not configured."]]
        return

    chat_function = MODEL_DISPATCHER.get(model)
    if chat_function:
        async for response in chat_function(message, history):
            yield response
    else:
        yield history + [[message, "🚨 Invalid model selection."]]

# --- Gradio UI Layout ---
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky"), css=config.CSS) as demo:
    gr.Markdown(
        """
        # ✨ Intelli Demo App
        Select a model backend and start a conversation.
        """
    )
    with gr.Row():
        model_choice = gr.Radio(
            list(MODEL_DISPATCHER.keys()),
            label="Choose a Model Backend",
            value="Vertex AI (Gemini)",
        )

    chatbot = gr.Chatbot(label="Conversation")

    msg_textbox = gr.Textbox(placeholder="Type your question here...", label="Message")

    with gr.Row():
        submit_btn = gr.Button(value="▶️ Submit", variant="primary")
        clear_btn = gr.ClearButton([msg_textbox, chatbot], value="🗑️ Clear Conversation")

    gr.Examples(examples=config.SAMPLE_QUESTIONS, inputs=[msg_textbox], label="Example Questions")

    # --- Event Handling Logic ---
    submit_triggers = [msg_textbox.submit, submit_btn.click]
    for trigger in submit_triggers:
        trigger(
            chat_handler,
            [msg_textbox, chatbot, model_choice],
            [chatbot],
        ).then(lambda: gr.update(value=""), None, [msg_textbox], queue=False)

# --- Application Entry Point ---
if __name__ == "__main__":
    server_port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=server_port, share=True)
