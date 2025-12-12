# google_LLM.py
import google.generativeai as genai
from config import load_config

config = load_config()

GEMINI_TOKEN = config.GEMINI_TOKEN

# Настройка Google Gemini
genai.configure(api_key=GEMINI_TOKEN)
google_model = genai.GenerativeModel("models/gemma-3-27b-it")



