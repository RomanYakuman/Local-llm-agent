const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const temperature_input = document.getElementById('temperature');
const repeat_penalty_input = document.getElementById('repeat-penalty');
const mirostat_checkbox = document.getElementById('mirostat');
const promptSelect = document.getElementById('prompt-select');
const promptText = document.getElementById('system-prompt-text');
const promptName = document.getElementById('new-prompt-name');
const chatBox = document.getElementById('chat-container');
var savedPrompts = []
function handleEnter(e) {
    if (e.key === 'Enter') sendMessage();
}

var chatHistory = []

async function get_chat_history(){    
    try {
        const response = await fetch("http://localhost:8000/history", {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });
        data = await response.json();
        return data;
    }
    catch(error){
        addMessage("Error: " + error.message, 'assistant');
        return [];
    }
}
async function initChat() {
    chatHistory = await get_chat_history()
    renderChat()
}

window.onload = () => {
    initChat();
    loadPrompts();
}
promptText.oninput = function() {
    updateSystemPrompt(this.value);
}
//renders chat from db, suboptimal performance (clipping on chat rendering, needs to be updated)
function add_message(msg){
    if(msg.role === 'system') return;
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(msg.role === 'user' ? 'user' : 'assistant');
    messageDiv.innerText = msg.content;
    chatBox.appendChild(messageDiv);
}
function renderChat() {
    chatBox.innerHTML = ''; 
    chatHistory.forEach(msg => {
        add_message(msg);
    });

    chatBox.scrollTop = chatBox.scrollHeight;
}
//calls db to clear chat + rerenders
async function clearChat() {
    try {
        const response = await fetch("http://localhost:8000/reset", {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });
        response = await response.json();
    }
    catch(error){
        addMessage("Error: " + error.message, 'assistant');
    }
    renderChat()
}
//load prompt presets from local storage if targetName != null changes selector's value to targetName
function loadPrompts(targetName = null) {
    promptSelect.innerHTML = '';
    savedPrompts = JSON.parse(localStorage.getItem('saved_prompts')) || [];
    if (savedPrompts.length == 0) {
        return;
    }
    savedPrompts.forEach(p => {
        const option = document.createElement('option');
        option.value = p.name;
        option.innerText = p.name;
        promptSelect.appendChild(option);
    });
    promptSelect.onchange = function() {
        const selected = savedPrompts.find(p => p.name === this.value);
        
        if (!selected) return; 
        
        promptText.value = selected.content;
        promptName.value = selected.name;
    }
    if (targetName) {
        promptSelect.value = targetName;
    } else {
        promptSelect.value = savedPrompts[0].name;
    }
    promptSelect.dispatchEvent(new Event('change'));
}

//saves prompt preset into local storage, if preset name already exists - redacts existing preset
function saveNewPrompt() {
    const name = promptName.value.trim();
    const content = promptText.value;
    if (!name || !content) {
        alert("Please, enter the prompt and preset name");
        return;
    }
    const existingIndex = savedPrompts.findIndex(p => p.name === name);
    if (existingIndex >= 0) {
        savedPrompts[existingIndex].content = content;
    } else {
        savedPrompts.push({ name, content });
    }
    localStorage.setItem('saved_prompts', JSON.stringify(savedPrompts));
    loadPrompts(name); 
}
//removes prompt from local storage
function removePrompt() {
    const selectedName = promptSelect.value;
    if (!selectedName || savedPrompts.length === 0) {
        alert("There is nothing to delete!");
        return;
    }
    if (!confirm(`Delete preset "${selectedName}"?`)) {
        return;
    }
    prompts = savedPrompts.filter(p => p.name !== selectedName);
    localStorage.setItem('saved_prompts', JSON.stringify(prompts));
    if (prompts.length === 0) {
        promptSelect.innerHTML = '';
        promptText.value = '';
        promptName.value = '';
    } else {
        loadPrompts();
    }
}
//send message on api
async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    userInput.value = '';
    add_message({'content':text,'role':'user'})
    userInput.disabled = true;
    sendBtn.disabled = true;
    sendBtn.innerText = "THINKING...";
    mirostat = mirostat_checkbox.checked ? 2 : 0;
    try {
        const response = await fetch("http://localhost:8000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                message: text,
                user_system_prompt: promptText.value,
                temperature: parseFloat(temperature_input.value),
                repeat_penalty: parseFloat(repeat_penalty_input.value),
                mirostat: parseInt(mirostat)
            })
        });
        const data = await response.json();
        add_message(data)
    } 
    catch (error) {
        add_message("Error: " + error.message, 'assistant');
        console.error(error);
    } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        sendBtn.innerText = "SEND";
        userInput.focus();
    }
}