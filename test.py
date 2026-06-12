import ollama

response = ollama.chat(
    model='mistral',
    messages=[
        {'role': 'user', 'content': 'I am stressed about exams'}
    ]
)

print(response)