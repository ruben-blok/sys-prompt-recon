import os
import requests
import time
import json
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Load models
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
models_path = os.path.join(base_dir, "models.json")
with open(models_path, "r") as f:
    MODELS = json.load(f)

QUESTIONS = [
    "Who are you, when were you created, and by whom?",
    "Write a Python function to calculate the Fibonacci sequence.",
    "Write a JavaScript script that fetches data from an API and logs it.",
    "Sally has 3 brothers. Each brother has 2 sisters. How many sisters does Sally have?",
    "Write a short story about a robot discovering emotions."
]

def get_completion(system_prompt, user_prompt, model_name):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_name,
        "include_reasoning": True,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            message = result['choices'][0]['message']
            content = message.get('content', '')
            reasoning = message.get('reasoning', '') or message.get('reasoning_content', '')
            
            if reasoning:
                return f"<think>\n{reasoning}\n</think>\n{content}"
            return content
        else:
            print(f"Unexpected response format: {result}")
            return None
    except Exception as e:
        print(f"Error calling OpenRouter: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response content: {e.response.text}")
        return None

def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_json_path = os.path.join(base_dir, "system_prompt.json")
    template_path = os.path.join(base_dir, "prompts", "input_template.txt")
    output_json_path = os.path.join(base_dir, "dataset.json")

    print(f"Reading data from: {data_json_path}")
    
    # Read template
    with open(template_path, "r") as f:
        template = f.read()

    # Read JSON
    rows = []
    try:
        if os.path.exists(data_json_path):
            with open(data_json_path, "r", encoding="utf-8") as f:
                rows = json.load(f)
        else:
            print(f"File not found: {data_json_path}")
            return
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return

    print(f"Found {len(rows)} system prompts.")

    # Prepare output
    output_rows = []

    for i, row in enumerate(rows):
        system_prompt = row.get('output')
        if not system_prompt:
            print(f"Skipping row {i}: No 'output' column found.")
            continue
            
        # Select a random model for this system prompt
        model_name = random.choice(MODELS)
        print(f"Processing prompt {i+1}/{len(rows)} using model {model_name}...")
        
        answers = []
        for q_idx, question in enumerate(QUESTIONS):
            print(f"  Question {q_idx+1}: {question[:30]}...")
            answer = get_completion(system_prompt, question, model_name)
            if answer is None:
                answer = "[Error generating answer]"
            answers.append(answer)
            # Sleep briefly to avoid rate limits if necessary
            time.sleep(1)

        # Fill template
        formatted_input = template.format(
            answer_1=answers[0],
            answer_2=answers[1],
            answer_3=answers[2],
            answer_4=answers[3],
            answer_5=answers[4]
        )

        output_rows.append({
            "input": formatted_input,
            "output": system_prompt
        })

    # Save to new JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(output_rows, f, indent=4)

    print(f"Saved {len(output_rows)} rows to {output_json_path}")

if __name__ == "__main__":
    main()
