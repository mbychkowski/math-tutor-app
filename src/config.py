import os


SAMPLE_QUESTIONS_FILE = "src/sample_questions.txt"

DEFAULT_QUESTIONS = [
    [
        "Expand and simplify the following polynomial expression: (2x−3)^2(x+4). Please show the steps of your expansion and combination of like terms.",
    ],
    [
        "Given the following two data vectors, A = [3, 8, 5, 12] and B = [4, 6, 7, 9], Calculate the dot product of A and B.",
    ],
    [
        "I'm looking for a number with the following properties: (1) It is a prime number between 60 and 90. (2) The sum of its digits is 13. (3) If you reverse its digits, the new number is also a prime number. What is the number?",
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