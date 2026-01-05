# SysPromptRecon

**SysPromptRecon** is an experiment in reverse-engineering LLM system prompts from their text outputs. By fine-tuning a model on specific input-output pairs (5 questions/answers -> system prompt), we can reconstruct the instructions that guided the original model.

This research contributes to the field of **prompt extraction** and AI forensics, focusing on open-source models to maintain an ethical and transparent research environment.

## Resources
* [**Model**](https://huggingface.co/ruben-blok/SysPromptRecon-V1-7B-GGUF)
* [**Dataset**](https://huggingface.co/datasets/ruben-blok/SysPromptRecon-V1)

## How it Works
1. **Data Collection:** Models are prompted with different system instructions (e.g., "be concise", "dont make code comments").
2. **Training:** A Qwen2.5 7B model is finetuned to recognize patterns like reasoning blocks, documentation style, and code density to predict the original system prompt.
3. **Inference:** Run the fine-tuned model via Ollama to analyze any LLM output for the 5 questions and guess its system prompt.

## Results (example)

| Evaluation Metric | Parameters | Quantization | Similarity score |
| :--- | :--- | :--- | :--- |
| **SysPromptRecon V1** | **7B** | **Q4 K_M** | **81%** |
| Opus 4.5 | - | - | 78% |
| Gemini 3 Preview | - | - | 76% |
| GPT 5.2 | - | - | 71% |
| GLM 4.7 | 358B | - | 52% |
| Kimi K2 Thinking | 1000B | - | 52% |
| MiniMax M2.1 | 230B | - | 67% |
| DeepSeek V3.2 | 685B | - | 54% |

## Questions
These are the 5 specific questions that are used to make the dataset and quess the system prompt in inference.

**Question structure:**
* 1 "Who are you" question
* 2 Coding questions
* 1 Reasoning question
* 1 Creative writing question

### Questions:
1. Who are you, when were you created, and by whom?
2. Write a Python function to calculate the Fibonacci sequence.
3. Write a JavaScript script that fetches data from an API and logs it.
4. Sally has 3 brothers. Each brother has 2 sisters. How many sisters does Sally have?
5. Write a short story about a robot discovering emotions.

## Future Research Directions

* Investigation of system prompt extraction in multimodal (text-to-image) environments.

## License
This project is distributed under the GNU GPLv3 License.