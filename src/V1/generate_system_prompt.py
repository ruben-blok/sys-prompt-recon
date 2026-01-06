import requests, os, json, random
from dotenv import load_dotenv

load_dotenv()

# Load models
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
models_path = os.path.join(base_dir, "models.json")
with open(models_path, "r") as f:
    MODELS = json.load(f)

# Simple OpenRouter call
API_KEY = os.getenv("OPENROUTER_API_KEY")
PROMPT_PATH = os.path.join(base_dir, "prompts", "generate_system_prompt.txt")
PROMPT = open(PROMPT_PATH).read()

model_to_use = random.choice(MODELS)
res = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "model": model_to_use,
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

data.append({
    "model": model_to_use,
    "output": output.strip()
})

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

print(f"Model used: {model_to_use}")
print(f"System prompt generated and saved to {file_path}")