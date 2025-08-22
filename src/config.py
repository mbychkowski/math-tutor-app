import os


SAMPLE_QUESTIONS_FILE = "src/sample_questions.txt"

DEFAULT_QUESTIONS = [
    [
        "What are the main differences between Python 2 and Python 3?",
    ],
    [
        "Explain the concept of inheritance in object-oriented programming.",
    ],
    [
        "How does the Google Kubernetes Engine (GKE) work?",
    ],
]

SAMPLE_QUESTIONS = []

try:
    with open(SAMPLE_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            question=line
            SAMPLE_QUESTIONS.append([question])
except FileNotFoundError:
    pass

if not SAMPLE_QUESTIONS:
    SAMPLE_QUESTIONS = DEFAULT_QUESTIONS

TITLE = None

CSS = """
.gradio-container {
    max-width: 800px; /* Set your desired max-width */
    margin: 0 auto; /* Center the container */
}

.example { border: 1px solid #87CEEB; }
"""