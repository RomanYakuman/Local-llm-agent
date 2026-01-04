const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const temperature_input = document.getElementById('temperature');
const repeat_penalty_input = document.getElementById('repeat-penalty');
const mirostat_checkbox = document.getElementById('mirostat');
const promptSelect = document.getElementById('prompt-select');
const promptText = document.getElementById('system-prompt-text');
const promptName = document.getElementById('new-prompt-name');
var savedPrompts = []
function handleEnter(e) {
    if (e.key === 'Enter') sendMessage();
}

let chatHistory = JSON.parse(localStorage.getItem('chat')) || [];

window.onload = () => {
    renderChat();
    loadPrompts();
}

promptText.oninput = function() {
    updateSystemPrompt(this.value);
}
//renders chat from history saved in local storage
function renderChat() {
    const chatBox = document.getElementById('chat-container');
    chatBox.innerHTML = ''; 

    chatHistory.forEach(msg => {
        if(msg.role === 'system') return;
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(msg.role === 'user' ? 'user' : 'assistant');
        messageDiv.innerText = msg.content;
        chatBox.appendChild(messageDiv);
    });

    chatBox.scrollTop = chatBox.scrollHeight;
}
//sabes chat into local storage
function saveChat() {
    localStorage.setItem('chat', JSON.stringify(chatHistory));
}
//clears chat from local storage
function clearChat() {
    localStorage.removeItem('chat');
    chatHistory = [{ role: 'system', content: chatHistory[0]['content']}];
    localStorage.setItem('chat', JSON.stringify(chatHistory));
    saveChat();
    messages = document.getElementsByClassName("message");
    Array.from(messages).forEach(msg => {
        msg.remove()
    });
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

function updateSystemPrompt(newPrompt) {
    if (chatHistory.length === 0 || chatHistory[0].role !== 'system') {
        chatHistory.unshift({ role: 'system', content: newPrompt });
    } else {
        chatHistory[0].content = newPrompt;
    }
    saveChat();
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
    chatHistory.push({ role: "user", content: text});
    saveChat();
    renderChat();
    userInput.disabled = true;
    sendBtn.disabled = true;
    sendBtn.innerText = "THINKING...";
    mirostat = mirostat_checkbox.checked ? 2 : 0;
    try {
        const response = await fetch("http://localhost:8000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                messages: chatHistory,
                temperature: parseFloat(temperature_input.value),
                repeat_penalty: parseFloat(repeat_penalty_input.value),
                mirostat: parseInt(mirostat)
            })
        });
        const data = await response.json();
        chatHistory.push(data);
        saveChat();
        renderChat();
    } 
    catch (error) {
        addMessage("Error: " + error.message, 'assistant');
        console.error(error);
    } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        sendBtn.innerText = "SEND";
        userInput.focus();
    }
}