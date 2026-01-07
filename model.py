import json
import os
import sys
from llama_cpp import Llama

CONFIG_FILE = 'config.json'
print('\ninitializing model\n')
system_prompt = """
<core_instruction>
CRITICAL PROTOCOL:
    1. You are the assistant (role:assistant)
    2. The user sends you requests (role:user)
    3. BOUNDARIES:
       - You MUST ONLY generate text for the assistant.
       - When you have finished your turn, STOP immediately.
       - You must always generate at least one word non-empty string response.
</core_instruction>
<tools_library>
    You have the authority to invoke the following tools to solve user tasks.
    PROTOCOL:
        1. ANALYZE: Determine if the user's request requires external chat_data or file manipulation.
        2. SELECT: Choose the exact [COMMAND] from the list below.
        3. EXECUTE: Output the command in the JSON "action" field.

    1. [COMMAND]: "test1"
       - Description: Test.
       - Trigger: only use test1 function if the user explicitly asks for it.
       - Parameters: No.

    2. [COMMAND]: "test 2"
       - Description: Test 2.
       - Trigger: you don't have enough information to provide answer.
       - Parameters: No.
</tools_library>
<json_formatting_rules>
    You MUST output a JSON object using this schema:
    
    1. "chain_of_thought": 
       - Make an analysis of the request and chat context consisting of at least 3 sentances. 
       - Decision making process regarding the tool if needed.
    2. "action":
       - Only use tools in the situation specified in their Trigger.
       - If no tool applies, output the empty string ''.
    3. "response": 
        - The final natural language reply to the user.
        - User can only see your response.
        - You have to always provide response .
        - Adopt the tone, style, and language provided at the start of the context.
        - If used any tools, specify their usage in the response
</json_formatting_rules>
"""

class llm_model:
    def __init__(self):
        self.model = self.model_init()

    #load config.json for model initialization
    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            print('Config file not found')
            sys.exit(1)
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print('Syntax error in json')
            sys.exit(1)

    #init model from config
    def model_init(self):
        config = self.load_config()
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

    #returns json in the form of a string from a chat chat_data
    def model_reply(self, chat_data, context):
        if(chat_data.mirostat > 0):
            chat_data.mirostat = 2
        else:
            chat_data.mirostat = 0
        stream_response = self.model.create_chat_completion(
            messages = context,
            #Lower the temperature higher the chance of most probable tokens to be selected
            temperature = chat_data.temperature,
            #repeat_penalty > 1 pelizes repetition by making repeated tokens less likely to be selected
            repeat_penalty=chat_data.repeat_penalty,
            #stream true to see the output as a stream in the console
            stream=True,
            max_tokens=2048,
            #mirostat sampler algorithm heighetns the perplexity of the generated text, more perplexity = less repetition, but with more perplexity comes lower stability
            #0 = off, 2 = second version (on)
            mirostat_mode=chat_data.mirostat,
            #target perplexity
            mirostat_tau=4.0,
            #default is 0.1, bigger value = higher rate
            mirostat_eta=0.1,
            response_format={
                "type": "json_object",
                "schema": {
                    "type": "object",
                    "properties": {
                        "chain_of_thought": {"type": "string"},
                        "action":{"type":"string",
                        "enum": [
                            "test1",
                            "test 2",
                            ""
                        ]},
                        "response": {"type":"string"},
                        },
                    "required": ["chain_of_thought", "action", "response" ]
                }
            },
            stop=[
                "<|eot_id|>",
                "<|start_header_id|>",
                "<|end_of_text|>"
            ]
            )
        json_string = ''
        for chunk in stream_response:
            delta = chunk['choices'][0]['delta'].get('content', '')
            if delta:
                print(delta, end='', flush=True)
                json_string += delta
        return json_string