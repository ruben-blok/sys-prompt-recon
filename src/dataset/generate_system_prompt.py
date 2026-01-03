import requests, os, json
from dotenv import load_dotenv

load_dotenv()

# Simple OpenRouter call
API_KEY = os.getenv("OPENROUTER_API_KEY")
PROMPT_PATH = "prompts/generate_system_prompt.txt"
PROMPT = open(PROMPT_PATH).read()

res = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "model": "allenai/olmo-3.1-32b-think:free",
        "messages": [{"role": "user", "content": PROMPT}]
    }
)

output = res.json()['choices'][0]['message']['content']

# Save to JSON
file_path = 'system_prompt.json'
data = []

if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

data.append({"output": output.strip()})

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

print(f"System prompt generated and saved to {file_path}")