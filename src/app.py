import os
import gradio as gr
import httpx
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud.aiplatform import Endpoint

# --- Load Environment Variables ---
# Load variables from a .env file if it exists
load_dotenv()

# --- General Configuration ---
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "YOUR_GCP_PROJECT_ID_HERE")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# --- Vertex AI Custom Endpoint Configuration ---
# The ID of your deployed custom model endpoint in Vertex AI
VERTEX_AI_CUSTOM_ENDPOINT_ID = os.getenv("VERTEX_AI_CUSTOM_ENDPOINT_ID", "YOUR_VERTEX_AI_ENDPOINT_ID_HERE")

# --- Vertex AI Gemini Model Configuration ---
VERTEX_AI_GEMINI_MODEL_NAME = os.getenv("VERTEX_AI_GEMINI_MODEL_NAME", "gemini-2.5-flash")

# --- GKE Self-Hosted Model Configuration ---
# The full URL of your model's prediction endpoint on GKE
GKE_MODEL_ENDPOINT_URL = os.getenv("GKE_MODEL_ENDPOINT_URL", "http://127.0.0.1:8000/v1/chat/completions")
VLLM_MODEL_NAME = os.getenv("VLLM_MODEL_NAME", "<your model name>")


# --- Initialization ---
if GCP_PROJECT_ID == "YOUR_GCP_PROJECT_ID_HERE":
    # This will be caught by the chat handler to display a nice error in the UI
    # instead of crashing the application on startup.
    print("🔴 WARNING: GCP_PROJECT_ID is not set. The application will not work correctly.")
    print("Please update the GCP_PROJECT_ID in your .env file.")

# Initialize the Vertex AI client
vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)

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
    if VERTEX_AI_CUSTOM_ENDPOINT_ID == "YOUR_VERTEX_AI_ENDPOINT_ID_HERE":
        yield "🔴 Please configure the VERTEX_AI_CUSTOM_ENDPOINT_ID."
        return

    try:
        endpoint = Endpoint(VERTEX_AI_CUSTOM_ENDPOINT_ID)

        instances = [{"prompt": message}]

        full_response = ""
        response_stream = endpoint.predict(instances=instances)
        for response in response_stream.predictions:
            if response:
                full_response += response
                yield full_response
    except Exception as e:
        yield f"Error calling Vertex AI Endpoint: {e}"


async def chat_with_gke_model(message: str, history: list):
    """
    Handles chat with a self-hosted model on GKE using an async HTTP client.
    """
    if GKE_MODEL_ENDPOINT_URL == "http://your-gke-service.example.com/predict":
        yield "🔴 Please configure the GKE_MODEL_ENDPOINT_URL."
        return

    messages = [{"role": "user", "content": message}]

    payload = {
        "model": VLLM_MODEL_NAME,
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
    "Vertex AI (Fine Tuned)": chat_with_vertex_custom_model,
    "GKE (Fine Tuned)": chat_with_gke_model,
}


async def chat_handler(message: str, history: list, model: str):
    chat_function = MODEL_DISPATCHER.get(model)
    if chat_function:
        # Use 'async for' since all our chat functions are now async generators
        async for chunk in chat_function(message, history):
            yield chunk
    else:
        yield "🔴 Invalid model selection."


# --- Gradio UI Layout ---
with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky"),
    css=".gradio-container {max-width: 800px; margin: auto;}",
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
        flagging_mode="manual",
        examples=[
            [
                "Expand and simplify the following polynomial expression: (2x−3)^2(x+4). Please show the steps of your expansion and combination of like terms.",
                "Vertex AI (Gemini)",
            ],
            [
                "Given the following two data vectors, A = [3, 8, 5, 12] and B = [4, 6, 7, 9], Calculate the dot product of A and B.",
                "Vertex AI (Fine Tuned)",
            ],
            [
                "I'm looking for a number with the following properties: (1) It is a prime number between 60 and 90. (2) The sum of its digits is 13. (3) If you reverse its digits, the new number is also a prime number. What is the number?",
                "GKE (Fine Tuned)",
            ],
        ],
        title="🎓 Math Tutor",
    )

# --- Application Entry Point ---
if __name__ == "__main__":
    server_port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=server_port, share=True)