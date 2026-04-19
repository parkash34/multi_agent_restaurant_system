# Bella Italia — Multi-Agent Restaurant System

A multi-agent AI restaurant system built with FastAPI, LangGraph and Groq AI.
Three specialized agents handle different areas — menu inquiries, table reservations
and general FAQ questions. A smart router directs each customer message to the
right agent automatically.

## Features

- Three specialized agents — Menu, Reservation and FAQ
- LLM powered router — AI decides which agent handles each message
- SQLite database — reservations and customer preferences stored permanently
- File tools — menu from JSON file, FAQs from text file
- API tool — real time weather via wttr.in
- Shared memory — all agents share the same conversation history
- Long term memory — customer dietary preferences saved to database
- Multi-session support — each customer has separate conversation history
- Anti-hallucination — agents use tools instead of guessing
- Guardrails — each agent stays in its area of responsibility

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | Backend web framework |
| LangGraph | Multi-agent framework |
| LangChain | AI tooling |
| Groq API | AI language model provider |
| LLaMA 3.3 70B | AI model |
| SQLite | Reservation and preference database |
| Pydantic | Data validation |
| python-dotenv | Environment variable management |

## Project Structure
```
bella-italia-multi-agent/
│
├── env/
├── main.py
├── menu.json
├── faq.txt
├── restaurant.db      ← created automatically
├── .env
└── requirements.txt
```

## Setup

1. Clone the repository
```
git clone https://github.com/yourusername/bella-italia-multi-agent
```

2. Create and activate virtual environment
```
python -m venv env
env\Scripts\activate
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Create `.env` file and add your Groq API key
```
API_KEY=your_groq_api_key_here
```

5. Run the server
```
uvicorn main:app --reload
```

## API Endpoint

### POST /chat

**Request:**
```json
{
    "session_id": "user_1",
    "message": "Do you have vegan pizza?"
}
```

**Response:**
```json
{
    "output": "Yes we have vegan options! Our Vegetarian pizza is perfect for you.",
    "routed_to": "menu"
}
```

## Agent System

### Menu Agent — Marco
Handles all food and drink related questions.

| Tools | Purpose |
|---|---|
| `read_menu` | Reads menu from menu.json |
| `check_dietary_options` | Checks dietary availability |
| `save_customer_preference` | Saves dietary preference to database |

### Reservation Agent — Sofia
Handles all booking related requests.

| Tools | Purpose |
|---|---|
| `check_availability` | Checks table availability |
| `book_table` | Generates booking reference |
| `save_reservation` | Stores reservation in database |
| `get_reservation` | Retrieves reservation by name |
| `cancel_reservation` | Cancels reservation by reference |

### FAQ Agent — Luca
Handles general restaurant questions.

| Tools | Purpose |
|---|---|
| `read_faq` | Reads FAQ from faq.txt |
| `get_restaurant_info` | Returns restaurant details |
| `get_weather` | Gets weather from wttr.in |

## Routing System
```
Customer message
↓
LLM Router classifies message
↓
menu        → Marco handles it
reservation → Sofia handles it
faq         → Luca handles it
↓
Response returned with routed_to field
```

## Database Schema

```sql
CREATE TABLE reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    date TEXT,
    time TEXT,
    people INTEGER,
    special_requirement TEXT,
    reference INTEGER
)

CREATE TABLE customer_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    dietary_requirement TEXT,
    visit_count INTEGER DEFAULT 0
)
```

## Memory System
```
Short Term  →  conversation history per session
shared across all three agents
resets on server restart
Long Term   →  customer preferences in database
persists permanently
used to personalize future visits
```

## Files
```

**menu.json** — restaurant menu updated without code changes

**faq.txt** — frequently asked questions updated without code changes
```

## Validation Rules

- Session ID cannot be empty
- Message cannot be empty
- Maximum 8 people per table booking

## Environment Variables
```
API_KEY=your_groq_api_key_here
```

## Notes

- Never commit your .env file to GitHub
- restaurant.db is created automatically on first run
- Menu and FAQ can be updated without changing code
- Session memory resets when server restarts
- Each agent only handles its area of responsibility