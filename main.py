import uvicorn
import json
from fastapi import FastAPI
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model import llm_model, system_prompt
from db import save_message_db, get_chat_history, chat_reset

app = FastAPI()
#creates llm_model instance that stores llm model created using llama-cpp-python and settings from config.json
model = llm_model()

class UserInput(BaseModel):
    message: str
    user_system_prompt: str
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

#chat completition endpoint
@app.post('/chat')
def chat(user_data: UserInput):
    #concatenating system prompt from backend with system prompt from frontend
    final_system_prompt = user_data.user_system_prompt + system_prompt
    #creating context with system prompt
    context = [{"role":"system", "content":final_system_prompt, "timestamp": datetime.now().timestamp()}]
    #saving last user message to db
    save_message_db(msg=user_data.message, role='user')
    #getting chat history from db in the form of the list of dictionaries
    history = get_chat_history()
    #extending context with chat history from db
    context.extend(history)
    #getting json_string from the model by passing down user input instance for settings and context for chat history
    json_string = model.model_reply(user_data, context)
    parsed_json = json.loads(json_string, strict=False)
    response = parsed_json.get("response", "")
    save_message_db(msg=response, role='assistant')
    response_dict = {"role":"assistant","content": response, "timestamp":datetime.now().timestamp()}
    context.append(response_dict)
    return response_dict

@app.get('/history')
def get_history():
    return get_chat_history()

@app.get('/reset')
def reset_chat():
    chat_reset()
    
if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000)