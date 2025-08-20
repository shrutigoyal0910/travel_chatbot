const synth = window.speechSynthesis;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognizer = new SpeechRecognition();
recognizer.lang = "en-US";

let voiceEnabled = true;


function appendMessage(sender, text, buttons = []) {
    const chatBox = document.getElementById("chatBox");
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);

    const avatar = document.createElement("img");
    avatar.classList.add("avatar");
    avatar.src = sender === "bot" ? botAvatarUrl : userAvatarUrl;
    avatar.onerror = () => { avatar.src = mediaUrl + "avatars/default.png"; };

    const textDiv = document.createElement("div");
    textDiv.classList.add("message-text");
    textDiv.innerText = text;

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(textDiv);

    if (buttons.length > 0) {
        const buttonContainer = document.createElement("div");
        buttonContainer.className = "button-container";

        buttons.forEach((btn) => {
            const button = document.createElement("button");
            button.className = "chat-button";
            button.innerText = btn.title || btn.payload;

            if (btn.payload.startsWith("test_")) {
                button.onclick = () => {
                    appendMessage("user", btn.title);
                    callTestApi(btn.payload);
                };
            } else if (btn.title === "Search Hotels") {
                button.onclick = () => {
                    appendMessage("user", btn.title);
                    searchHotels();
                };
            } else {
                button.onclick = () => {
                    const label = btn.title || btn.payload;
                    const payload = btn.payload || btn.title;
                    appendMessage("user", label);
                    sendPayloadToBot(payload);
                };
            }

            buttonContainer.appendChild(button);
        });

        msgDiv.appendChild(buttonContainer);
    }

    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    const chatHistory = JSON.parse(localStorage.getItem("chatHistory") || "[]");
    chatHistory.push({ sender, text, buttons });
    localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
}

function showLoader() {
    const chatBox = document.getElementById("chatBox");
    const loader = document.createElement("div");
    loader.classList.add("loader");
    loader.id = "loader";
    chatBox.appendChild(loader);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeLoader() {
    const loader = document.getElementById("loader");
    if (loader) loader.remove();
}

function showTypingIndicator() {
    const chatBox = document.getElementById("chatBox");
    const typingDiv = document.createElement("div");
    typingDiv.className = "typing-indicator";
    typingDiv.id = "typing";
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTypingIndicator() {
    const typingDiv = document.getElementById("typing");
    if (typingDiv) typingDiv.remove();
}

async function searchHotels() {
    showLoader();
    showTypingIndicator();

    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const response = await fetch("/chat/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
            body: JSON.stringify({ message: "search_hotels" }),
            credentials: "include",
        });

        const data = await response.json();
        removeLoader();
        removeTypingIndicator();
        if (data.custom && data.custom.type === "hotel_cards" && data.custom.cards) {
            renderHotelCards(data.custom.cards);
        } else {
            const mockCards = [
                {
                    image: "https://via.placeholder.com/260x140",
                    title: "Hillside Retreat",
                    subtitle: "Shimla, Himachal Pradesh",
                    rating: "4.5",
                    price: "5000",
                    amenities: "Free Wi-Fi, Breakfast",
                    buttons: [{ title: "Book Now", payload: "book_hotel" }],
                },
            ];
            appendMessage("bot", "Here are some hotels I found:");
            renderHotelCards(mockCards);
        }
    } catch (error) {
        removeLoader();
        removeTypingIndicator();
        appendMessage("bot", "Error searching for hotels. Please try again.");
        console.error("Search Hotels error:", error);
    }
}

function handleKeyPress(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    handleSend();
  }
}


function speakText(text) {
    if (!synth) return;
    if (synth.speaking) {
        synth.cancel();
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    synth.speak(utterance);
}

function startVoiceInput() {
  console.log("Voice button clicked");

  if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
    alert("Speech Recognition is not supported in your browser.");
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognizer = new SpeechRecognition();
  recognizer.lang = "en-US";

  try {
    recognizer.start();
    console.log("Recognition started");
  } catch (err) {
    console.error("Recognizer start error:", err);
    alert("Failed to start voice input. Make sure microphone access is allowed.");
    return;
  }

  recognizer.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById("userInput").value = transcript;
    handleSend();
  };

  recognizer.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    alert("Voice input error: " + event.error);
  };
}



function clearChat() {
  const chatBox = document.getElementById("chatBox");
  chatBox.innerHTML = "";
  localStorage.removeItem("chatHistory");

  // Re-show welcome message after clearing
  if (currentMode === "chat") {
    appendMessage("bot", "Hi! I'm Qyra, your personal travel assistant. I can help you with:", [
      { title: "✈️ Book a Flight", payload: "book_flight" },
      { title: "🏨 Search Hotels", payload: "search_hotels" },
      { title: "📦 Travel Packages", payload: "show_packages" },
      { title: "Test API", payload: "test_api" }
    ]);
  } else if (currentMode === "ai") {
    appendMessage("bot", "Hi! I'm your AI assistant. Ask me anything!");
  }
}





async function callTestApi(testCommand = "test_hotels") {
    showLoader();
    showTypingIndicator();
    console.log(`Starting Test API call with command: ${testCommand}`);

    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const response = await fetch('/test-api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ message: testCommand }),
            credentials: 'include'
        });

        const data = await response.json();
        console.log(`Test API response:`, JSON.stringify(data, null, 2));

        if (data.reply) {
            appendMessage('bot', data.reply, data.buttons || []);
            if (voiceEnabled) speakText(data.reply);
        }

        if (data.custom && data.custom.type === "hotel_cards" && data.custom.cards) {
            const seenKeys = new Set();
            const uniqueCards = data.custom.cards.filter(card => {
                const cardKey = `${card.title}-${card.subtitle}`.toLowerCase();
                if (!seenKeys.has(cardKey)) {
                    seenKeys.add(cardKey);
                    return true;
                }
                return false;
            });
            renderHotelCards(uniqueCards);
        }

        removeLoader();
        removeTypingIndicator();
    } catch (error) {
        console.error('Test API error:', error);
        removeLoader();
        removeTypingIndicator();
        appendMessage('bot', 'Error calling test API. Please try again.');
    }
}

function renderHotelCards(cards) {
    const chatBox = document.getElementById("chatBox");
    console.log("Rendering cards:", JSON.stringify(cards, null, 2));

    const container = document.createElement("div");
    container.className = "card-carousel";

    cards.forEach((card, index) => {
        const cardDiv = document.createElement("div");
        cardDiv.className = "hotel-card";
        cardDiv.id = `card-${index}`;

        const image = card.image || `${mediaUrl}hotel_images/default.webp`;
        const title = card.title || "Hotel";
        const subtitle = card.subtitle || "N/A";
        const rating = card.rating || "N/A";
        const price = card.price || "N/A";
        const amenities = card.amenities || "N/A";

        cardDiv.innerHTML = `
            <img class="hotel-image" src="${image}" alt="${title}" onerror="this.src='${mediaUrl}hotel_images/default.webp'; this.onerror=null;" />
            <div class="hotel-details">
                <h3 class="hotel-title">${title}</h3>
                <p class="hotel-location">📍 Location: ${subtitle}</p>
                <p class="hotel-rating">⭐ ${rating}</p>
                <p class="hotel-price">₹${price} / night</p>
                <p class="hotel-amenities">${amenities}</p>
                <div class="hotel-buttons"></div>
            </div>
        `;

        const btnContainer = cardDiv.querySelector(".hotel-buttons");
        (card.buttons || []).forEach((btn) => {
            const button = document.createElement("button");
            button.innerText = btn.title;
            button.onclick = () => {
                appendMessage("user", btn.title);
                sendPayloadToBot(btn.payload);
            };
            btnContainer.appendChild(button);
        });

        container.appendChild(cardDiv);
    });

    const existingCarousel = chatBox.querySelector(".card-carousel");
    if (existingCarousel) {
        chatBox.removeChild(existingCarousel);
    }

    chatBox.appendChild(container);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const userInput = document.getElementById("userInput").value.trim();
    if (!userInput) return;
    appendMessage("user", userInput);
    showTypingIndicator();
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const response = await fetch("/chat/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
            body: JSON.stringify({ message: userInput }),
            credentials: "include",
        });
        const data = await response.json();
        removeTypingIndicator();
        if (data.custom && data.custom.type === "hotel_cards" && data.custom.cards) {
            renderHotelCards(data.custom.cards);
        } else if (data.custom && data.custom.type === "flight_cards" && data.custom.cards) {
            renderFlightCards(data.custom.cards);
        } else if (data.reply) {
            appendMessage("bot", data.reply, data.buttons || []);
            if (voiceEnabled) speakText(data.reply);
        } else {
            appendMessage("bot", "Sorry, I didn't get a response from the server.");
        }
    } catch (error) {
        removeTypingIndicator();
        appendMessage("bot", "Error communicating with the server.");
        console.error("Send message error:", error);
    }
    document.getElementById("userInput").value = "";
}

async function sendAiMessage() {
    const userInput = document.getElementById("userInput").value.trim();
    if (!userInput) {
        console.log("No input");
        return;
    }
    appendMessage("user", userInput);
    showTypingIndicator();
    console.log("AI Send with:", userInput);

    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        console.log("CSRF:", csrfToken ? "Present" : "Missing", csrfToken);
        if (!csrfToken) {
            appendMessage("bot", "CSRF missing");
            removeTypingIndicator();
            return;
        }

        const response = await fetch("/chat/ai/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
            body: JSON.stringify({ message: userInput }),
            credentials: "include",
        });
        console.log("Status:", response.status);
        console.log("Headers:", Object.fromEntries(response.headers.entries()));
        const data = await response.json();
        console.log("Data:", data);
        removeTypingIndicator();

        if (data.reply) appendMessage("bot", data.reply);
        else if (data.error) appendMessage("bot", `Error: ${data.error}`);
        else appendMessage("bot", "No valid response");
    } catch (error) {
        removeTypingIndicator();
        console.error("Error:", error, error.message, error.stack);
        appendMessage("bot", "Communication failed");
    }
    document.getElementById("userInput").value = "";
}

function renderFlightCards(cards) {
    const chatBox = document.getElementById("chatBox");
    const container = document.createElement("div");
    container.className = "card-carousel";
    cards.forEach((card, index) => {
        const cardDiv = document.createElement("div");
        cardDiv.className = "flight-card";
        cardDiv.id = `card-${index}`;
        const title = card.title || "Flight";
        const subtitle = card.subtitle || "N/A";
        const price = card.price || "N/A";
        const departure = card.departure || "N/A";
        const seats = card.seats || "N/A";
        cardDiv.innerHTML = `
            <div class="flight-details">
                <h3 class="flight-title">${title}</h3>
                <p class="flight-route">✈️ Route: ${subtitle}</p>
                <p class="flight-price">₹${price}</p>
                <p class="flight-departure">🕒 Departure: ${departure}</p>
                <p class="flight-seats">💺 Seats: ${seats}</p>
                <div class="flight-buttons"></div>
            </div>
        `;
        const btnContainer = cardDiv.querySelector(".flight-buttons");
        (card.buttons || []).forEach((btn) => {
            const button = document.createElement("button");
            button.innerText = btn.title;
            button.onclick = () => {
                appendMessage("user", btn.title);
                sendPayloadToBot(btn.payload);
            };
            btnContainer.appendChild(button);
        });
        container.appendChild(cardDiv);
    });
    const existingCarousel = chatBox.querySelector(".card-carousel");
    if (existingCarousel) chatBox.removeChild(existingCarousel);
    chatBox.appendChild(container);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendPayloadToBot(payload) {
    showTypingIndicator();
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const response = await fetch("/chat/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
            body: JSON.stringify({ message: payload }),
            credentials: "include",
        });
        const data = await response.json();
        removeTypingIndicator();
        if (data.custom && data.custom.type === "hotel_cards" && data.custom.cards) {
            renderHotelCards(data.custom.cards);
        } else if (data.custom && data.custom.type === "flight_cards" && data.custom.cards) {
            renderFlightCards(data.custom.cards);
        } else if (data.reply) {
            appendMessage("bot", data.reply, data.buttons || []);
            if (voiceEnabled) speakText(data.reply);
        } else {
            appendMessage("bot", "Sorry, I didn't get a response from the server.");
        }
    } catch (error) {
        removeTypingIndicator();
        appendMessage("bot", "Error communicating with the server.");
        console.error("Send payload error:", error);
    }
}