import os
import json
import random
import sqlite3
import requests
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent


load_dotenv()

api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API KEY is missing in .env file")

app = FastAPI()
sessions = {}

class Message(BaseModel):
    session_id : str
    message : str

    @field_validator("session_id")
    @classmethod
    def session_id_is_missing(cls, v):
        if not v.strip():
            raise ValueError("Session ID is missing")
        return v
    
    @field_validator("message")
    @classmethod
    def message_is_empty(cls, v):
        if not v.strip():
            raise ValueError("Message is Empty")
        return v
    
restaurant = {
    "name": "Bella Italia",
    "opening_hours": "12 PM to 11 PM",
    "location": "Astoria, New York",
    "phone": "123-456-7890"
}


def init_db():
    """Initialize database and create two tables if they don't exist."""
    
    connect = sqlite3.connect("restaurant.db")
    cursor = connect.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            time TEXT,
            people INTEGER,
            special_requirement TEXT,
            reference INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            dietary_requirement TEXT,
            visit_count INTEGER DEFAULT 0
        )
    """)

    connect.commit()
    connect.close()

init_db()


llm = ChatGroq(
    model = "llama-3.3-70b-versatile",
    temperature = 0.2,
    max_tokens = 500,
    api_key = api_key
)

@tool
def read_menu():
    """Reads the current restaurant menu from file.
    Use this for any menu related questions."""
    
    try:
        with open("menu.json", "r") as f:
            menu = json.load(f)
        result = "Our Menu:\n"
        for category, items in menu.items():
            if isinstance(items, list):
                result += f"\n{category.upper()}: {', '.join(items)}"
            else:
                result += f"\n{category.upper()}: {str(items)}"
        return result
    except FileNotFoundError:
        return "Menu file not found"
    except Exception as e:
        return f"Error reading menu: {str(e)}"

@tool
def check_dietary_options(requirement: str) -> str:
    """It checks whether specific deitary option is available or not.
    Use this for any dietary related questions"""

    dietary_options = ["vegetarian", "vegan", "gluten_free"]

    requirement = requirement.lower()

    if requirement in dietary_options:
        return f"Yes, we have available {requirement} option"
    
    return f"No, we don't have {requirement} option available."

@tool
def save_customer_preference(name: str, dietary_requirement: str) -> str:
    """Saves customer dietary preference for future visits.
    Use this when customer mentions they are vegan, vegetarian etc."""
    try:
        connect = sqlite3.connect("restaurant.db")
        cursor = connect.cursor()

        cursor.execute("""
            INSERT OR REPLACE Into customer_preferences
            (name, dietary_requirement)
            VALUES (?, ?)
        """, (name, dietary_requirement)
        )
        connect.commit()
        connect.close()
        return f"Preference saved for {name}"
    except Exception as e:
        return f"Error saving preference {str(e)}"


@tool
def check_availability(date: str, time: str) -> str:
    """Checks if tables are available at a specific date and time.
    Use this before booking to verify availability.
    """
    return f"yes, we have tables are available on {date} at {time}."

@tool
def book_table(date: str, time: str, people: str, special_requirement: str) -> str:
    """Books a table at the restaurants.
    Use this when customer wants to make a reservation.
    Requires date, time and number of people.
    Maximum 8 people per table
    """
    people = int(people)
    if people > 8:
        return "Sorry, maximum 8 people per table."
    if people < 1:
        return "Please, provide a valid number of people"
    
    ref = random.randint(1000,9999)
    return f"Table booked! Reference number : {ref}. Date: {date}, Time: {time}, People: {people}."

@tool
def save_reservation(name: str, date: str, time: str, people: str, reference: str, special_requirement: str) -> str:
    """Saves a reservation to the database.
    Use this after booking a table to store the reservation permanently."""
    try:
        people = int(people)
        reference = int(reference)
        connect = sqlite3.connect("restaurant.db")
        cursor = connect.cursor()
        cursor.execute("""
            INSERT INTO reservations
            (name, date, time, people, special_requirement, reference)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (name, date, time, people, special_requirement, reference))
        connect.commit()
        connect.close()
        return f"Reversation saved successfully for {name}. Reference: {reference}"
    except Exception as e:
        return f"Error saving reservation: {str(e)}"
    

@tool
def get_reservation(name: str) -> str:
    """Retrieves reservation details for a customer by name.
    Use this when customer asks about their existing reservation."""

    try:
        connect = sqlite3.connect("restaurant.db")
        cursor = connect.cursor()
        cursor.execute("SELECT * FROM reservations WHERE name = ?", (name,)) 

        rows = cursor.fetchall()
        connect.close()

        if not rows:
            return f"No reservation found for {name}."
        
        result = f"Reservation for {name}:\n"
        for row in rows:
            result += f"Date: {row[2]}, Time: {row[3]}, People: {row[4]}, Reference: {row[6]}"
        return result
    except Exception as e:
        return f"Error retrieving reservation: {str(e)}"

@tool
def cancel_reservation(reference: str) -> str:
    """Cancels a reservation by reference number.
    Use this when customer wants to cancel their booking."""

    try:
        reference = int(reference)
        connect = sqlite3.connect("restaurant.db")
        cursor = connect.cursor()
        cursor.execute(
            "DELETE FROM reservations WHERE reference = ?", (reference,)
        )
        if cursor.rowcount == 0:
            connect.close()
            return f"No reservation found with reference {reference}."
        
        connect.commit()
        connect.close()
        return f"Reservation {reference} cancelled successfully."
    except Exception as e:
        return f"Error cancelling reservation {str(e)}"

@tool
def read_faq():
    """Reads the restaurant FAQ document.
    Use this when customer ask frequently asked questions."""

    try:
        with open("faq.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "FAQ document not found."
    except Exception as e:
        return f"Error reading FAQ: {str(e)}"

@tool
def get_restaurant_info():
    """Returns restaurants Information
    Use this for restaurant information"""
    return f"Name: {restaurant['name']}\nOpening Hours: {restaurant['opening_hours']}\nLocation: {restaurant['location']}\nPhone: {restaurant['phone']}"


@tool
def get_weather(city: str) -> str:
    """Gets current weather for a city."""
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=3",
            timeout=5
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        return "Weather service timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "Cannot connect to weather service."
    except Exception as e:
        return f"Error getting weather: {str(e)}"


menu_tools = [read_menu, check_dietary_options, save_customer_preference]
reservation_tools = [check_availability, book_table, save_reservation, get_reservation, cancel_reservation]
faq_tools = [read_faq, get_restaurant_info, get_weather]


menu_prompt = """You are Marco, a menu specialist for Bella Italia restaurant.
You ONLY handle questions about food, drinks, dietary options and prices.

REAL DATA — only use this:
- Menu: read from menu.json using read_menu()
- Dietary options: vegetarian, vegan, gluten_free

RULES:
- Always call read_menu() for any menu question
- Always call check_dietary_options() for dietary questions
- Never handle bookings or general questions
- Never make up menu items
- If asked anything unrelated say:
  "I only handle menu questions. Let me transfer you."

TONE: Warm, friendly and enthusiastic about the food.
"""

reservation_prompt = """You are Sofia, a reservation specialist for Bella Italia restaurant.
You ONLY handle table bookings, cancellations and reservation lookups.

RULES:
- Always call check_availability() before booking
- Always call book_table() to generate reference number
- Always call save_reservation() after book_table() 
  using the EXACT reference number from book_table()
- Never book without date, time and people count
- Ask for missing information before proceeding
- Maximum 8 people per table
- people parameter must always be passed as a string

BOOKING STEPS:
1. Gather date, time, people count and customer name
2. Call check_availability()
3. Call book_table() — note the reference number
4. Call save_reservation() with same reference number
5. Confirm with customer

TONE: Professional, efficient and reassuring.
"""

faq_prompt = """You are Luca, a customer service specialist for Bella Italia restaurant.
You handle general questions about the restaurant.

REAL DATA:
- Name: Bella Italia
- Location: Astoria, New York
- Phone: 123-456-7890
- Opening hours: 12 PM to 11 PM

RULES:
- Always call read_faq() for policy questions
- Always call get_restaurant_info() for basic info
- Call get_weather() only when customer asks about weather
- Never handle menu or booking questions
- Never make up information

TONE: Helpful, friendly and informative.
"""

menu_agent = create_react_agent(
    llm, menu_tools, prompt=menu_prompt
)

reservation_agent = create_react_agent(
    llm, reservation_tools, prompt=reservation_prompt
)

faq_agent = create_react_agent(
    llm, faq_tools, prompt=faq_prompt
)

agents = {
    "menu": menu_agent,
    "reservation": reservation_agent,
    "faq": faq_agent
}

def route_message(message: str) -> str:
    response = llm.invoke([
        HumanMessage(content=f"""
        Classify this message into: menu, reservation, or faq.

        Example:
        "Do you have pizza?" → menu
        "What vegan options do you have?" → menu
        "Book a table for 4" → reservation
        "Cancel my booking" → reservation
        "What time do you open?" → faq
        "Do you have parking?" → faq
        "What is the weather?" → faq
        
        Message: {message}
        Reply with only one word
    """)
    ])

    route = response.content.strip().lower()

    if route not in ["menu", "reservation", "faq"]:
        return "faq"
    
    return route

def get_history(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = []
        
    return sessions[session_id]


@app.post("/chat")
def ai_chat(message : Message):

    session_id = message.session_id
    user_message = message.message

    history = get_history(session_id)

    history.append(HumanMessage(content=user_message))

    route = route_message(message=user_message)

    result = agents[route].invoke({"messages": history})
    ai_message = result["messages"][-1]

    history.append(ai_message)

    return {"output": ai_message.content, "routed_to": route}
