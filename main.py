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
    """Initialize database and create tables if they don't exist."""

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
    connect.commit()
    connect.close()

def init_db():
    """Initialize database and create two tables if they don't exist."""
    
    connect = sqlite3.connect("restaurant.db")
    cursor1 = connect.cursor()
    cursor2 = connect.cursor()

    cursor1.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            time, TEXT,
            people INTEGER,
            special_requirement TEXT,
            reference INTEGER
        )
    """)

    cursor2.execute("""
        CREATE TABLE IF NOT EXISTS customer_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT
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

