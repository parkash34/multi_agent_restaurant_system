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
