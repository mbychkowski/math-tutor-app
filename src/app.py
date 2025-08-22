import os
import gradio as gr
import httpx
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel
import config
from google.cloud.aiplatform import Endpoint

# --- Load Environment Variables ---
# Load variables from a .env file if it exists
load_dotenv()

# --- General Configuration ---
PROJECT_ID = os.getenv("PROJECT_ID", "YOUR_GCP_PROJECT_ID_HERE")
LOCATION = os.getenv("LOCATION", "us-central1")

# --- Vertex AI Gemini Model Configuration ---
VERTEX_AI_GEMINI_MODEL_NAME = os.getenv("VERTEX_AI_GEMINI_MODEL_NAME", "gemini-2.5-flash")

# --- Vertex AI Custom Endpoint Configuration ---
# The ID of your deployed custom model endpoint in Vertex AI
VERTEX_AI_ENDPOINT_ID = os.getenv("VERTEX_AI_ENDPOINT_ID", "YOUR_VERTEX_AI_ENDPOINT_ID_HERE")

# --- GKE Self-Hosted Model Configuration ---
# The full URL of your model's prediction endpoint on GKE
GKE_MODEL_ENDPOINT_URL = os.getenv("GKE_MODEL_ENDPOINT_URL", "http://127.0.0.1:8000/v1/chat/completions")

# --- Initialization ---
if PROJECT_ID == "YOUR_GCP_PROJECT_ID_HERE":
    # This will be caught by the chat handler to display a nice error in the UI
    # instead of crashing the application on startup.
    print("🔴 WARNING: PROJECT_ID is not set. The application will not work correctly.")
    print("Please update the PROJECT_ID in your .env file.")

# Initialize the Vertex AI client
vertexai.init(project=PROJECT_ID, location=LOCATION)

# --- Model Backend Logic ---
async def chat_with_vertex_gemini(message: str, history: list):
    """Handles chat with a standard Gemini model on Vertex AI."""
    try:
        model = GenerativeModel(VERTEX_AI_GEMINI_MODEL_NAME)
        chat = model.start_chat()  # History removed
        response = chat.send_message(message, stream=True)

        full_response = ""
        for chunk in response:
            if chunk.text:
                full_response += chunk.text
                yield full_response
    except Exception as e:
        yield f"An error occurred with the Vertex AI Gemini model: {e}"

async def chat_with_vertex_custom_model(message: str, history: list):
    """Handles chat with a custom model on a Vertex AI Endpoint."""
    if VERTEX_AI_ENDPOINT_ID == "YOUR_VERTEX_AI_ENDPOINT_ID_HERE":
        yield "🔴 Please configure the VERTEX_AI_ENDPOINT_ID."
        return

    try:
        endpoint = Endpoint(VERTEX_AI_ENDPOINT_ID)

        # Use a dictionary for instances
        instances = [{"prompt": message, "max_tokens": 512}]

        # Make the prediction (no await here)
        response = endpoint.predict(instances=instances)

        full_response = ""
        for prediction in response.predictions:
            if isinstance(prediction, str):
                full_response += prediction

                output_split = full_response.split("Output:")
                final_answer_split = output_split[1].split("Final Answer:")

                yield final_answer_split[0]

    except Exception as e:
        print(f"An error occurred: {e}")
        yield f"An error occurred with the Vertex AI custom model: {e}"

async def chat_with_gke_model(message: str, history: list):
    """
    Handles chat with a self-hosted model on GKE using an async HTTP client.
    """
    if GKE_MODEL_ENDPOINT_URL == "http://your-gke-service.example.com/predict":
        yield "🔴 Please configure the GKE_MODEL_ENDPOINT_URL."
        return

    messages = [{"role": "user", "content": message}]

    payload = {
        "messages": messages,
    }
    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                GKE_MODEL_ENDPOINT_URL, json=payload, headers=headers
            )
            response.raise_for_status()
            response_json = response.json()
            content = response_json["choices"][0]["message"]["content"]
            yield content

    except httpx.HTTPStatusError as e:
        yield f"Error calling GKE model: Received status {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        yield f"Error calling GKE model: {e}"
    except (KeyError, IndexError) as e:
        yield f"Error: Unexpected response format from GKE model: {response.text}"


# A mapping from the UI choice to the backend function
MODEL_DISPATCHER = {
    "Vertex AI (Gemini)": chat_with_vertex_gemini,
    "Vertex AI (self-hosted)": chat_with_vertex_custom_model,
    "GKE (self-hosted)": chat_with_gke_model,
}


async def chat_handler(message: str, history: list, model: str):
    chat_function = MODEL_DISPATCHER.get(model)
    if chat_function:
        async for chunk in chat_function(message, history):
            yield chunk
    else:
        yield "🔴 Invalid model selection."


# --- Gradio UI Layout ---
with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky"),
    css=config.CSS,
) as demo:
    gr.Markdown(
        """
        # Crash Courses in AI
        Select a model backend and start a conversation.
        """
    )

    with gr.Row():
        model_choice = gr.Radio(
            list(MODEL_DISPATCHER.keys()),
            label="Choose a Model Backend",
            value="Vertex AI (Gemini)",
        )

    gr.ChatInterface(
        fn=chat_handler,
        additional_inputs=[model_choice],
        examples=config.SAMPLE_QUESTIONS,
        title=config.TITLE if config.TITLE else "✨ Intelli Demo App",
    )

# --- Application Entry Point ---
if __name__ == "__main__":
    server_port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=server_port, share=True)
