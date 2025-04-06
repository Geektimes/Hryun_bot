#config.py
import os
from dataclasses import dataclass
import yaml
from dotenv import load_dotenv

root_path = "D:\\Projects\\Hryun_bot"
file_name = "config.yaml"
file_path = os.path.join(root_path, file_name)

with open(file_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

load_dotenv()

@dataclass
class Config:
    TOKEN: str = os.getenv('BOT_TOKEN')
    DB_NAME = os.getenv('DB_NAME')
    ROOT_PATH = os.getenv('ROOT_PATH')
    DB_FILE_PATH = os.path.join(ROOT_PATH, DB_NAME)
    BOT_USERNAME: str = os.getenv('BOT_USERNAME')
    BOT_NAME: str = "Хрюн",
    BOT_LAST_NAME: str = "Моржов"
    BOT_TG_ID: int = 7858823954
    GREETING: str = config["GREETING"]
    source_path: str = os.path.join(ROOT_PATH, "source")
    ANEKDOTS_FILE: str = os.path.join(ROOT_PATH, "source", "anekdots.yaml")


def load_config():
    return Config()

