Local llm agent with web interface.

Functionality:
1. Chat completition
2. RAG for long-term memory
3. Basic Duck Duck Go search
User can tweak following response generating parameters:
1. Temperature
2. Repeat penalty
3. User's system prompt
4. Mirostat

How to use:
Path to model in .gguf extension is specified in config.json file (there is an template, just change the name to config.json and specify parameters suitable to your's machine)
Package requierements for app building specified in requirements.txt
Right now there are many critical parameters that are hardcoded with accordance to my device and the model i use, so it's practically unusable until this issue solved.
To install llama-cpp-python follow instruction from repository: https://github.com/abetlen/llama-cpp-python/tree/main

Docker file will be added after there is at least some features
