let history = [];


const messageInput =
    document.getElementById("messageInput");

const messages =
    document.getElementById("messages");

const welcomeScreen =
    document.getElementById("welcomeScreen");

const sendButton =
    document.getElementById("sendButton");


/* ======================================
   SEND MESSAGE
====================================== */

async function sendMessage() {

    const message =
        messageInput.value.trim();


    if (!message || sendButton.disabled) {
        return;
    }


    hideWelcome();


    addMessage(
        "user",
        message
    );


    messageInput.value = "";

    autoResize();


    sendButton.disabled = true;


    const typingId =
        showTyping();


    try {

        const response =
            await fetch("/api/chat", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    message: message,

                    history: history

                })

            });


        const data =
            await response.json();


        removeTyping(typingId);


        if (!response.ok) {

            addMessage(
                "assistant",
                data.error ||
                "Something went wrong. Please try again."
            );

            return;
        }


        const answer =
            data.reply ||
            "I couldn't generate a response.";


        addMessage(
            "assistant",
            answer
        );


        history.push({

            role: "user",

            content: message

        });


        history.push({

            role: "assistant",

            content: answer

        });


    }

    catch (error) {

        console.error(error);


        removeTyping(typingId);


        addMessage(
            "assistant",
            "Unable to connect to the catering assistant. Please check that the Flask server is running."
        );

    }

    finally {

        sendButton.disabled = false;

        messageInput.focus();

    }

}


/* ======================================
   ADD MESSAGE
====================================== */

function addMessage(role, text) {

    const wrapper =
        document.createElement("div");


    wrapper.className =
        "message " + role;


    const content =
        document.createElement("div");


    content.className =
        "message-content";


    content.textContent = text;


    wrapper.appendChild(content);


    messages.appendChild(wrapper);


    scrollToBottom();

}


/* ======================================
   TYPING
====================================== */

function showTyping() {

    const id =
        "typing-" + Date.now();


    const wrapper =
        document.createElement("div");


    wrapper.className =
        "message assistant";


    wrapper.id = id;


    const content =
        document.createElement("div");


    content.className =
        "message-content";


    const typing =
        document.createElement("div");


    typing.className =
        "typing";


    for (let i = 0; i < 3; i++) {

        const dot =
            document.createElement("span");

        typing.appendChild(dot);

    }


    content.appendChild(typing);

    wrapper.appendChild(content);

    messages.appendChild(wrapper);


    scrollToBottom();


    return id;

}


function removeTyping(id) {

    const element =
        document.getElementById(id);


    if (element) {

        element.remove();

    }

}


/* ======================================
   QUICK PROMPT
====================================== */

function quickPrompt(text) {

    messageInput.value = text;

    autoResize();

    messageInput.focus();

    sendMessage();

}


/* ======================================
   NEW CHAT
====================================== */

function newChat() {

    history = [];

    messages.innerHTML = "";

    welcomeScreen.style.display = "";

    messageInput.value = "";

    autoResize();

    messageInput.focus();

}


/* ======================================
   CLEAR CHAT
====================================== */

function clearChat() {

    if (history.length === 0) {
        return;
    }


    if (
        confirm(
            "Are you sure you want to clear this conversation?"
        )
    ) {

        newChat();

    }

}


/* ======================================
   KEYBOARD
====================================== */

function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();

    }

}


/* ======================================
   AUTO RESIZE
====================================== */

messageInput.addEventListener(
    "input",
    autoResize
);


function autoResize() {

    messageInput.style.height =
        "auto";


    messageInput.style.height =
        Math.min(
            messageInput.scrollHeight,
            120
        ) + "px";

}


/* ======================================
   HIDE WELCOME
====================================== */

function hideWelcome() {

    welcomeScreen.style.display =
        "none";

}


/* ======================================
   SCROLL
====================================== */

function scrollToBottom() {

    const chatArea =
        document.getElementById("chatArea");


    setTimeout(() => {

        chatArea.scrollTo({

            top: chatArea.scrollHeight,

            behavior: "smooth"

        });

    }, 60);

}


/* ======================================
   MOBILE SIDEBAR
====================================== */

function toggleSidebar() {

    const sidebar =
        document.getElementById("sidebar");


    sidebar.classList.toggle("open");

}