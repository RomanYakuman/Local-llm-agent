import uvicorn
import json
from fastapi import FastAPI
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model import llm_model, system_prompt
from db import save_message_db, get_chat_history, db_chat_reset
from vector_db import save_interaction_embedding, get_memory_block, vector_chat_reset
from search import ddgs_search

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
AVAILABLE_TOOLS = {
    "web_search": ddgs_search,
    "test 2": lambda x: "Test 2 executed"
}
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
    MAX_ITERATIONS = 3
    final_response = ''
    previous_actions = []
    for i in range(MAX_ITERATIONS):
        #getting json_string from the model by passing down user input instance for settings and context for chat history
        json_string = model.model_reply(user_data, context)
        try:
            parsed_json = json.loads(json_string, strict=False)
        except json.JSONDecodeError:
            print(f"CRITICAL ERROR: '{json_string}'")
            parsed_json = {"action": "", "response": "Error: Model failed to generate valid JSON."}
        response = parsed_json.get("response", "")
        chain_of_thought = parsed_json.get("chain_of_thought", "")
        action = parsed_json.get("action", "")
        action_input = parsed_json.get("action_input", "")
        if not action or action not in AVAILABLE_TOOLS or action in previous_actions:
            final_response = response
            break
        previous_actions.append(action)
        context.append({"role":"assistant", "content":f"<chain_of_thought>{chain_of_thought}</chain_of_thought>", "timestamp":now_timestamp})
        tool_function = AVAILABLE_TOOLS[action]
        tool_result = ''
        if(action == 'web_search'):
            if action_input and len(action_input) > 2:
                tool_result = tool_function(action_input)
            else:
                tool_result = tool_function(user_query)
            system_injection = (
                "\n\n[SYSTEM INSTRUCTION: "
                "The data above is sufficient."
                "Write a COMPREHENSIVE report based ONLY on this data."
                "Do not be brief. Expand on every point found in the text.]")
            tool_result += system_injection
        tool_msg_content = f"OBSERVATION from Tool '{action}':\n<tool_result>\n{tool_result}\n</tool_result>\n\nBased on this information, please provide the final answer."
        context.append({"role":"user", "content":tool_msg_content, "timestamp":now_timestamp})

    save_message_db(msg=final_response, role='assistant')
    save_interaction_embedding(user_msg=user_query, assistant_msg=final_response)
    response_dict = {"role":"assistant","content": final_response, "timestamp":now_timestamp}
    context.append(response_dict)
    return response_dict

@app.get('/history')
def get_history():
    return get_chat_history()

@app.get('/reset')
def reset_chat():
    db_chat_reset()
    vector_chat_reset()

if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000)