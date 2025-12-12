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
    GEMINI_TOKEN: str = os.getenv('GEMINI_TOKEN')
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BOT_USERNAME: str = os.getenv('BOT_USERNAME')
    BOT_NAME: str = os.getenv('BOT_NAME')
    BOT_LAST_NAME: str = os.getenv('BOT_LAST_NAME')
    BOT_TG_ID: int = os.getenv('BOT_TG_ID')
    SRC_PATH: str = os.path.join(BASE_DIR, "source")
    ANEKDOTS_FILE: str = os.path.join(BASE_DIR, "source", "anekdots.yaml")
    GREETING: str = config["GREETING"]
    SUMMARY_PROMPT = config["SUMMARY_PROMPT"]
    HRYUN_PROMPT = config["HRYUN_PROMPT"]
    OWNER_BRO_ID = os.getenv('OWNER_BRO_ID')
    OWNER_TIM_ID = os.getenv('OWNER_TIM_ID')

    ## AI
    MODEL = "models/gemma-3-27b-it"

    ## DB
    DB_NAME = os.getenv('DB_NAME')
    DB_PATH = os.path.join(BASE_DIR, DB_NAME)

    ## REDIS
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB: int = int(os.getenv('REDIS_DB', 0))


def load_config():
    return Config()

