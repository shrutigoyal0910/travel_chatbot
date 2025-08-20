# 🌍 Qyra – Travel Assistant Chatbot  

An **AI-powered travel assistant chatbot** built with **Django + Rasa + OpenRouter API**.  
Qyra helps users explore flights, hotels, and travel tips while supporting natural conversations powered by **DeepSeek AI model**.  

---

## ✨ Features  
- 🤖 **AI-Powered Conversations** using OpenRouter API with DeepSeek model  
- 🛫 **Flight Booking Suggestions** with example options  
- 🏨 **Hotel Booking Guidance** and recommendations  
- 🌍 **Travel Tips & Itinerary Ideas**  
- 👩‍💻 **User Authentication** – logged-in users’ chats are saved in the database  
- 📝 **Fallback Responses** if AI API fails, ensuring reliability  

---

## 🛠️ Tech Stack  
- **Backend:** Django (Python)  
- **Chat Engine:** Rasa + OpenRouter API (DeepSeek model)  
- **Database:** SQLite (default, can switch to PostgreSQL)  
- **Frontend:** HTML, CSS, JavaScript  
- **APIs:** OpenRouter (DeepSeek AI)  
- **Authentication:** Django’s built-in auth system  

---

## 📂 Project Structure  
```
Chatbot_project/
│── actions/          # Custom Rasa actions
│── data/             # NLU, stories, and rules
│── mysite/           # Django project
│ ├── chatbot/        # Django app
│ ├── templates/      # HTML files
│ ├── static/         # CSS, JS, images
│── tests/            # Rasa test stories
│── domain.yml        # Rasa domain file
│── endpoints.yml     # Rasa endpoints
│── config.yml        # Rasa pipeline & policies
│── requirements.txt  # Dependencies
│── .gitignore
│── README.md
```

---

## 🚀 Installation & Setup  

### 1️⃣ Clone Repository  
```bash
git clone https://github.com/shrutigoyal0910/travel_chatbot.git
cd travel_chatbot
```
### 2️⃣ Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```
### 3️⃣ Set Environment Variables
Create a .env file inside the project root:

```env
DEEPSEEK_API_KEY=your_openrouter_api_key_here
```
### 4️⃣ Run Django Server
```bash
cd mysite
python manage.py migrate
python manage.py runserver
```
👉 Access at: http://127.0.0.1:8000/

### 5️⃣ Run Rasa Server (in a new terminal)
```bash
rasa train
rasa run actions
rasa run --enable-api
```
### 💬 Usage
Open http://127.0.0.1:8000/ in your browser.
Login/Signup to your account.
Start chatting with Qyra – your travel assistant 🚀

#### Example Messages:
- "hello" → AI greeting + travel suggestions
- "book flight from Delhi to Goa" → Flight booking flow
- "find hotels in Manali" → Hotel search
- "show me travel packages" → Package browsing
- "cancel my booking 1234" → Cancels booking with ID
