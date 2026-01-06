import json

def inspect_dataset(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i, entry in enumerate(data):
            print(f"--- Entry {i+1} ---")
            print("INPUT:")
            print(entry.get('input', ''))
            print("\nOUTPUT:")
            print(entry.get('output', ''))
            print("\n" + "="*50 + "\n")
            
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    inspect_dataset('dataset.json')
