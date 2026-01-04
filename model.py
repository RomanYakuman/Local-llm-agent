import json
import os
import sys
from llama_cpp import Llama

CONFIG_FILE = 'config.json'
print('\ninitializing model\n')

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print('Config file not found')
        sys.exit(1)
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print('Syntax error in json')
        sys.exit(1)


def model_init():
    config = load_config()
    settings = config.get('model_settings', {})
    
    model_path = settings.get('model_path')
    if not os.path.exists(model_path):
        print(f'Model not found by the path: {model_path}')
        sys.exit(1)
    
    llm = Llama(
        model_path=model_path,
        n_ctx=settings.get('n_ctx', 8192),
        n_gpu_layers=settings.get('n_gpu_layers', -1),
        verbose=settings.get('varbose', False)
    )
    return llm