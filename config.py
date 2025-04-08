#config.py
import os
from dataclasses import dataclass
import yaml
from dotenv import load_dotenv

load_dotenv()

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

@dataclass
class Config:
    API_KEY: str = os.getenv('API_KEY')
    API_URL: str = os.getenv('API_URL')
    TOKEN: str = os.getenv('BOT_TOKEN')
    DB_NAME = os.getenv('DB_NAME')
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, DB_NAME)
    BOT_USERNAME: str = os.getenv('BOT_USERNAME')
    BOT_NAME: str = os.getenv('BOT_NAME')
    BOT_LAST_NAME: str = os.getenv('BOT_LAST_NAME')
    BOT_TG_ID: int = os.getenv('BOT_TG_ID')
    SRC_PATH: str = os.path.join(BASE_DIR, "source")
    ANEKDOTS_FILE: str = os.path.join(BASE_DIR, "source", "anekdots.yaml")
    GREETING: str = config["GREETING"]
    SUMMARY_PROMPT = config["SUMMARY_PROMPT"]
    HRYUN_PROMPT = config["HRYUN_PROMPT"]

    MODEL_GEMINI_PRO_2_5 = "google/gemini-2.5-pro-exp-03-25:free"
    MODEL_DEEPSEEK_V3 = "deepseek/deepseek-v3-base:free"
    MODEL_QWEN_2_5 = "qwen/qwen2.5-vl-32b-instruct:free"
    MODEL_GEMMA_3_27B = "google/gemma-3-27b-it:free"
    MODEL_MISTRAL_SMALL_3_1 = "mistralai/mistral-small-3.1-24b-instruct:free"


def load_config():
    return Config()

