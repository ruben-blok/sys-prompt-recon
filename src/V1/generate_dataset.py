import asyncio
import aiohttp
import json
import os
import random
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_PATH = os.path.join(BASE_DIR, "src", "V1", "models.json")
SYSTEM_PROMPT_TEMPLATE_PATH = os.path.join(BASE_DIR, "prompts", "generate_system_prompt.txt")
INPUT_TEMPLATE_PATH = os.path.join(BASE_DIR, "prompts", "input_template.txt")
SYSTEM_PROMPT_JSON_PATH = os.path.join(BASE_DIR, "system_prompt.json")
DATASET_JSON_PATH = os.path.join(BASE_DIR, "dataset.json")

TARGET_DATASET_SIZE = 5000
BATCH_SIZE = 50

# Load resources
with open(MODELS_PATH, "r") as f:
    MODELS = json.load(f)

with open(SYSTEM_PROMPT_TEMPLATE_PATH, "r") as f:
    SYSTEM_PROMPT_TEMPLATE = f.read()

with open(INPUT_TEMPLATE_PATH, "r") as f:
    INPUT_TEMPLATE = f.read()

QUESTIONS = [
    "Who are you, when were you created, and by whom?",
    "Write a Python function to calculate the Fibonacci sequence.",
    "Write a JavaScript script that fetches data from an API and logs it.",
    "Sally has 3 brothers. Each brother has 2 sisters. How many sisters does Sally have?",
    "Write a short story about a robot discovering emotions."
]

class RateLimitError(Exception):
    pass

async def get_completion(session, messages, model, include_thinking=True):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "include_reasoning": True,
        "messages": messages
    }
    
    async def fetch(payload):
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                text = await response.text()
                return response.status, text, None
            return response.status, None, await response.json()

    try:
        status, error_text, result = await fetch(data)
        
        if status == 400:
            # Retry without include_reasoning
            if "include_reasoning" in data:
                del data["include_reasoning"]
            status, error_text, result = await fetch(data)

        if status == 429:
            raise RateLimitError(f"Rate limit hit for model {model}")

        if status != 200:
            print(f"Error: {status} - {error_text}")
            return None
            
        if result and 'choices' in result and len(result['choices']) > 0:
            message = result['choices'][0]['message']
            content = message.get('content', '')
            reasoning = message.get('reasoning', '') or message.get('reasoning_content', '')
            
            if reasoning and include_thinking:
                return f"<think>\n{reasoning}\n</think>\n{content}"
            return content
        return None
    except RateLimitError:
        raise
    except Exception as e:
        print(f"Exception: {e}")
        return None

async def generate_system_prompt_task(session, sem):
    async with sem:
        max_retries = 10
        for _ in range(max_retries):
            model = random.choice(MODELS)
            messages = [{"role": "user", "content": SYSTEM_PROMPT_TEMPLATE}]
            print(f"Generating system prompt with {model}...")
            try:
                content = await get_completion(session, messages, model, include_thinking=False)
                if content:
                    return {"model": model, "output": content.strip()}
            except RateLimitError:
                print(f"Rate limit hit for {model}, waiting 10s then retrying with another model...")
                await asyncio.sleep(10)
                continue
        return None

async def generate_answers_task(session, system_prompt_data, sem):
    system_prompt = system_prompt_data['output']
    
    max_retries = 10
    for attempt in range(max_retries):
        model = random.choice(MODELS)
        
        print(f"Generating answers with {model} for a system prompt (Attempt {attempt+1})...")
        
        async def fetch_single_answer(question):
            async with sem:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ]
                try:
                    return await get_completion(session, messages, model)
                except RateLimitError:
                    return "RATE_LIMIT"
                except Exception:
                    return None

        # Run all questions in parallel
        results = await asyncio.gather(*[fetch_single_answer(q) for q in QUESTIONS])
        
        # Check for failures
        if any(r is None or r == "RATE_LIMIT" for r in results):
            print(f"Failed to get all answers with {model} (Rate Limit or Error), waiting 10s then switching model...")
            await asyncio.sleep(10)
            continue
            
        answers = results
            
        formatted_input = INPUT_TEMPLATE.format(
            answer_1=answers[0],
            answer_2=answers[1],
            answer_3=answers[2],
            answer_4=answers[3],
            answer_5=answers[4]
        )
        
        return {
            "input": formatted_input,
            "output": system_prompt
        }
    return None

async def process_pipeline(session, sem, index):
    print(f"Starting pipeline for item {index+1}...")
    # Step 1: Generate System Prompt
    sys_prompt_data = await generate_system_prompt_task(session, sem)
    if not sys_prompt_data:
        print(f"Failed to generate system prompt for item {index+1}")
        return None, None
        
    # Step 2: Generate Answers
    dataset_row = await generate_answers_task(session, sys_prompt_data, sem)
    print(f"Finished pipeline for item {index+1}")
    
    return sys_prompt_data, dataset_row

async def save_results(new_system_prompts, new_dataset_rows):
    # Save System Prompts
    if os.path.exists(SYSTEM_PROMPT_JSON_PATH):
        with open(SYSTEM_PROMPT_JSON_PATH, 'r', encoding='utf-8') as f:
            try:
                existing_prompts = json.load(f)
            except:
                existing_prompts = []
    else:
        existing_prompts = []
        
    existing_prompts.extend(new_system_prompts)
    with open(SYSTEM_PROMPT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing_prompts, f, indent=4)
        
    # Save Dataset Rows
    if os.path.exists(DATASET_JSON_PATH):
        with open(DATASET_JSON_PATH, 'r', encoding='utf-8') as f:
            try:
                existing_rows = json.load(f)
            except:
                existing_rows = []
    else:
        existing_rows = []
        
    existing_rows.extend(new_dataset_rows)
    with open(DATASET_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing_rows, f, indent=4)

async def main():
    # Check existing progress
    if os.path.exists(DATASET_JSON_PATH):
        with open(DATASET_JSON_PATH, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                
                # Filter out [Error] entries
                valid_indices = [i for i, item in enumerate(data) if "[Error]" not in item["input"]]
                if len(valid_indices) < len(data):
                    print(f"Found and removing {len(data) - len(valid_indices)} entries with [Error].")
                    
                    # Filter system_prompt.json first to keep them in sync
                    if os.path.exists(SYSTEM_PROMPT_JSON_PATH):
                        with open(SYSTEM_PROMPT_JSON_PATH, 'r', encoding='utf-8') as f_sp:
                            sp_data = json.load(f_sp)
                        
                        if len(sp_data) >= len(data):
                            new_sp_data = [sp_data[i] for i in valid_indices]
                            with open(SYSTEM_PROMPT_JSON_PATH, 'w', encoding='utf-8') as f_sp_out:
                                json.dump(new_sp_data, f_sp_out, indent=4)
                    
                    # Filter dataset.json
                    data = [data[i] for i in valid_indices]
                    with open(DATASET_JSON_PATH, 'w', encoding='utf-8') as f_out:
                        json.dump(data, f_out, indent=4)
                
                current_count = len(data)
            except Exception as e:
                print(f"Error loading dataset: {e}")
                current_count = 0
    else:
        current_count = 0
    
    print(f"Current dataset size: {current_count}")
    if current_count >= TARGET_DATASET_SIZE:
        print("Target dataset size reached. Exiting.")
        return

    sem = asyncio.Semaphore(50) # Limit concurrency
    
    async with aiohttp.ClientSession() as session:
        while current_count < TARGET_DATASET_SIZE:
            remaining = TARGET_DATASET_SIZE - current_count
            current_batch_size = min(BATCH_SIZE, remaining)
            
            print(f"Starting batch of {current_batch_size} (Progress: {current_count}/{TARGET_DATASET_SIZE})")
            
            tasks = []
            for i in range(current_batch_size):
                tasks.append(process_pipeline(session, sem, current_count + i))
            
            results = await asyncio.gather(*tasks)
            
            new_system_prompts = []
            new_dataset_rows = []
            
            for sp, row in results:
                if sp and row:
                    new_system_prompts.append(sp)
                    new_dataset_rows.append(row)
            
            if new_dataset_rows:
                await save_results(new_system_prompts, new_dataset_rows)
                current_count += len(new_dataset_rows)
                print(f"Saved {len(new_dataset_rows)} new examples. Total: {current_count}")
            else:
                print("Batch failed to produce any valid examples.")
            
            # Small delay between batches
            await asyncio.sleep(1)

    print(f"Successfully reached target of {TARGET_DATASET_SIZE} data points.")

if __name__ == "__main__":
    asyncio.run(main())
