const chatInput = document.querySelector("#chat-input");
const sendButton = document.querySelector("#send-btn");
const chatContainer = document.querySelector(".chat-container");
const themeButton = document.querySelector("#theme-btn");
const deleteButton = document.querySelector("#delete-btn");

let userText = null;

const loadDataFromLocalStorage = () => {
    const themeColor = localStorage.getItem("themeColor");

    document.body.classList.toggle("dark-mode", themeColor === "dark_mode");
    themeButton.innerText = document.body.classList.contains("dark-mode") ? "light_mode" : "dark_mode";

    const defaultText = `<div class="default-text">
                            <h1>Chikista.AI</h1>
                            <p>Start a conversation and explore the power of AI.<br>Your chat history will be displayed here.</p>
                        </div>`;

    chatContainer.innerHTML = localStorage.getItem("all-chats") || defaultText;
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
};

const createChatElement = (content, className) => {
    const chatDiv = document.createElement("div");
    chatDiv.classList.add("chat", className);
    chatDiv.innerHTML = content;
    return chatDiv;
};

const getChatResponse = async (incomingChatDiv) => {
    const response = await fetch('/chatbot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            user_input: userText,
        }),
    });

    const data = await response.json();

    incomingChatDiv.querySelector(".typing-animation").remove();

    const chatDetailsContent = document.createElement("div");
    chatDetailsContent.classList.add("chat-details-content");
    chatDetailsContent.innerHTML = `<img src="static/images/health_bot.jpg" alt="chatbot-img">
                                    <p>${data.response}</p>`;
    
    const chatDetails = incomingChatDiv.querySelector(".chat-details");
    chatDetails.innerHTML = ''; // Clear existing content
    chatDetails.appendChild(chatDetailsContent);

    localStorage.setItem("all-chats", chatContainer.innerHTML);
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
};

const showTypingAnimation = () => {
    const html = `<div class="chat-content">
                    <div class="chat-details">
                        <img src="static/images/health_bot.jpg" alt="chatbot-img">
                        <div class="typing-animation">
                            <div class="typing-dot" style="--delay: 0.2s"></div>
                            <div class="typing-dot" style="--delay: 0.3s"></div>
                            <div class="typing-dot" style="--delay: 0.4s"></div>
                        </div>
                    </div>
                    <span onclick="copyResponse(this)" class="material-symbols-rounded">content_copy</span>
                </div>`;

    const incomingChatDiv = createChatElement(html, "incoming");
    chatContainer.appendChild(incomingChatDiv);
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
    setTimeout(() => {
        getChatResponse(incomingChatDiv);
    }, 2000);
};

const handleOutgoingChat = () => {
    userText = chatInput.value.trim();

    if (!userText) return;

    chatInput.value = "";
    chatInput.style.height = `${initialInputHeight}px`;

    const html = `<div class="chat-content">
                    <div class="chat-details">
                        <img src="static/images/gojo.jpg" alt="user-img">
                        <p>${userText}</p>
                    </div>
                </div>`;

    const outgoingChatDiv = createChatElement(html, "outgoing");
    chatContainer.querySelector(".default-text")?.remove();
    chatContainer.appendChild(outgoingChatDiv);
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
    setTimeout(showTypingAnimation, 500);

    // Remove the default text after adding the outgoing chat
    const defaultTextDiv = chatContainer.querySelector(".default-text");
    if (defaultTextDiv) {
        defaultTextDiv.remove();
    }
};


deleteButton.addEventListener("click", () => {
    if (confirm("Are you sure you want to delete all the chats?")) {
        localStorage.removeItem("all-chats");
        loadDataFromLocalStorage();
    }
});

themeButton.addEventListener("click", () => {
    document.body.classList.toggle("light-mode");
    localStorage.setItem("themeColor", themeButton.innerText);
    themeButton.innerText = document.body.classList.contains("light-mode") ? "dark_mode" : "light_mode";
});

const initialInputHeight = chatInput.scrollHeight;

chatInput.addEventListener("input", () => {
    chatInput.style.height = `${initialInputHeight}px`;
    chatInput.style.height = `${chatInput.scrollHeight}px`;
});

chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
        e.preventDefault();
        handleOutgoingChat();
    }
});

loadDataFromLocalStorage();
sendButton.addEventListener("click", handleOutgoingChat);
