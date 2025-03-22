import ollama
import sys

client = ollama.Client()

conversation = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"},
]

# Stream the response
print("Streaming response: ", end="", flush=True)
for chunk in client.chat(
    model="llama3.2:3b",
    messages=conversation,
    stream=True
):

    content = chunk.get('message', {}).get('content', '')
    print(content, end='', flush=True)

print()