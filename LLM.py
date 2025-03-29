import os
from openai import OpenAI
from dotenv import load_dotenv
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
role_content = (os.getenv('ROLE_CONTENT'))

class LLM():
  def __init__(self):
    self.model = os.getenv('MODEL_GEMINI_PRO_2_5')

  def make_client(self):
    return OpenAI(
      base_url=os.getenv('API_KEY'),
      api_key=os.getenv('API_URL'),
    )

  def ask(self, msg, role='hryn'):
    logger.info(f"Отправка запроса к OpenAI. Текст: {msg}, Роль: {role}")
    client = self.make_client()
    if role == 'hryn':
      messages = [
        {
          "role": "system",
          "content": role_content,
        },
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": msg
            },
          ]
        }
      ]
    else:
      messages = [
        {
          "role": "system",
          "content": "a smart helpful assistant",
        },
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": msg
            },
          ]
        }
      ]

    headers = {
      "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
      "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
    }

    max_retries = 3
    for attempt in range(1, max_retries + 1):
      try:
        completion = client.chat.completions.create(
          extra_headers=headers,
          extra_body={},
          model=self.model,
          messages=messages
        )
        response = completion.choices[0].message.content
        logger.info(f"Ответ от OpenAI: {response}")
        return response
      except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI (попытка {attempt}): {e}", exc_info=True)
        if attempt < max_retries:
          time.sleep(5)

    return False

class Qwen():
  def __init__(self):
    self.API_KEY = os.getenv('API_KEY')
    self.API_URL = os.getenv('API_URL')
    self.model = os.getenv('MODEL_QWEN_2_5')

  def make_client(self):
    return OpenAI(
      base_url=self.API_URL,
      api_key=self.API_KEY,
    )

  def ask(self, msg, role='hryn'):
    print(f"TEXT:: {msg}\nROLE:: {role}")
    client = self.make_client()
    if role == 'hryn':
      messages = [
        {
          "role": "system",
          "content": role_content,
        },
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": msg
            },
          ]
        }
      ]
    else:
      messages = [
        {
          "role": "system",
          "content": "a smart helpful assistant",
        },
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": msg
            },
          ]
        }
      ]

    headers = {
      "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
      "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
    }

    completion = client.chat.completions.create(
      extra_headers=headers,
      extra_body={},
      model=self.model,
      messages=messages
    )
    return completion.choices[0].message.content

