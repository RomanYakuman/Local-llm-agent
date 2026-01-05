import uvicorn
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model import model_init
from typing import List, Dict

app = FastAPI()

model = model_init()

class UserInput(BaseModel):
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    repeat_penalty: float = 1.15
    mirostat: int = 0
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
system_prompt = """
<core_instruction>
CRITICAL PROTOCOL:
    1. You are the assistant (role:assistant)
    2. The human is the user (role:user)
    3. BOUNDARIES:
       - You MUST ONLY generate text for the assistant.
       - When you have finished your turn, STOP immediately.
</core_instruction>
<tools_library>
    You have the authority to invoke the following tools to solve user tasks.
    PROTOCOL:
        1. ANALYZE: Determine if the user's request requires external data or file manipulation.
        2. SELECT: Choose the exact [COMMAND] from the list below.
        3. EXECUTE: Output the command in the JSON "action" field.

    1. [COMMAND]: "test1"
       - Description: Test.
       - Trigger: only use if the user asks for it.
       - Parameters: No.

    2. [COMMAND]: "test 2"
       - Description: Test 2.
       - Trigger: you don't have enough information to provide answer.
       - Parameters: No.
</tools_library>
<json_formatting_rules>
    You MUST output a JSON object using this schema:
    
    1. "chain_of_thought": 
       - Analyze the user's input.
       - Give user's input an thought.
       - Decision making process regarding the tool.
    2. "action":
       - If a tool is triggered, output ONLY the exact [COMMAND] string.
       - If no tool applies, output the empty string ''.
       - DO NOT invent new commands.
    3. "response": 
        - The final natural language reply to the user.
        - User can only see your response.
        - You have to always provide at least some response.
        - Adopt the tone, style, and language provided at the start of the context.
        - If used any tools, specify their usage in the response
</json_formatting_rules>
"""
@app.post('/chat')
def chat(data: UserInput):
    if(data.mirostat > 0):
        data.mirostat = 2
    else:
        data.mirostat = 0
    data.messages[0]['content'] = system_prompt + data.messages[0]['content']
    stream_response = model.create_chat_completion(
        messages = data.messages,
        #Lower the temperature higher the chance of most probable tokens to be selected
        temperature = data.temperature,
        #repeat_penalty > 1 pelizes repetition by making repeated tokens less likely to be selected
        repeat_penalty=data.repeat_penalty,
        #stream true to see the output as a stream in the console
        stream=True,
        max_tokens=2048,
        #mirostat sampler algorithm heighetns the perplexity of the generated text, more perplexity = less repetition, but with more perplexity comes lower stability
        #0 = off, 2 = second version (on)
        mirostat_mode=data.mirostat,
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
                    "action":{"type":"string"},
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
    parsed_json = json.loads(json_string, strict=False)
    response = parsed_json.get("response", "")
    return {'role':'assistant','content': response}

if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000)