import uvicorn
import json
from fastapi import FastAPI
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model import llm_model, system_prompt
from db import save_message_db, get_chat_history, chat_reset
from vector_db import save_interaction_embedding, get_memory_block

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
    user_query = user_data.message
    #getting rag memory
    rag_db_memory = get_memory_block(user_query)
    #concatenating system prompt from backend with system prompt from frontend and context from rag_db
    final_system_prompt = f'{user_data.user_system_prompt} \n\n{system_prompt} \n\n{rag_db_memory}'
    now_timestamp = datetime.now().timestamp()
    #creating context with system prompt
    context = [{"role":"system", "content":final_system_prompt, "timestamp": datetime.now().timestamp()}]
    #saving last user message to db
    save_message_db(msg=user_query, role='user')
    #getting chat history from db in the form of the list of dictionaries
    history = get_chat_history()
    #extending context with chat history from db
    context.extend(history)
    #getting json_string from the model by passing down user input instance for settings and context for chat history
    json_string = model.model_reply(user_data, context)
    parsed_json = json.loads(json_string, strict=False)
    response = parsed_json.get("response", "")
    save_message_db(msg=response, role='assistant')
    save_interaction_embedding(user_msg=user_query, assistant_msg=response)
    response_dict = {"role":"assistant","content": response, "timestamp":now_timestamp}
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