import uvicorn
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
@app.post('/chat')
def chat(data: UserInput):
    if(data.mirostat > 0):
        data.mirostat = 2
    else:
        data.mirostat = 0
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
        mirostat_tau=5.0,
        #default is 0.1, bigger value = higher rate
        mirostat_eta=0.1
        )
    full_text = ''
    for chunk in stream_response:
        delta = chunk['choices'][0]['delta'].get('content', '')
        if delta:
            print(delta, end='', flush=True)
            full_text += delta

    return {'role':'assistant','content': full_text}

if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000)