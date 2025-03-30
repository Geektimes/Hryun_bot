# LLM.py
import os
from openai import OpenAI
import logging
import time
import yaml

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

summary_prompt = config["SUMMARY_PROMPT"]
hryun_promt = config["HRYUN_PROMPT"]

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


class LLM:
  def __init__(self):
    self.API_KEY = os.getenv('API_KEY')
    self.API_URL = os.getenv('API_URL')
    self.model = os.getenv('MODEL_GEMINI_PRO_2_5')
    self.model_qwen = os.getenv('MODEL_QWEN_2_5')

  def make_client(self):
    return OpenAI(
      base_url=self.API_URL,
      api_key=self.API_KEY,
    )

  @staticmethod
  def get_messages(role, msg):
    if role == 'hryn':
      messages = [
        {"role": "system", "content": hryun_promt},
        {"role": "user", "content": [{"type": "text", "text": msg}]}
      ]
    elif role == 'summary':
      # print(f"\n\nROLE:: {role}\n PROMT:: {summary_prompt}\n CONTENT:: {msg}")
      messages = [
        {"role": "system", "content": summary_prompt},
        {"role": "user", "content": [{"type": "text", "text": msg}]}
      ]
    else:
      messages = [
        {"role": "system", "content": "a smart helpful assistant"},
        {"role": "user", "content": [{"type": "text", "text": msg}]}
      ]
    return messages

  def ask(self, msg, role='hryn'):
    # logger.info(f"Отправка запроса к OpenAI. Текст: {msg}, Роль: {role}")
    client = self.make_client()
    messages = LLM.get_messages(role, msg)
    headers = {
      "HTTP-Referer": "<YOUR_SITE_URL>",
      "X-Title": "<YOUR_SITE_NAME>",
    }

    models = [self.model, self.model_qwen]  # Последовательность моделей
    max_retries = 3

    for model in models:
      for attempt in range(1, max_retries + 1):
        try:
          completion = client.chat.completions.create(
            extra_headers=headers,
            extra_body={},
            model=model,
            messages=messages
          )
          response = completion.choices[0].message.content
          logger.info(f"Ответ от OpenAI ({model}): {response}")
          return response  # Успех, возвращаем ответ
        except Exception as e:
          logger.error(f"Ошибка при запросе к {model} (попытка {attempt}): {e}", exc_info=True)
          if attempt < max_retries:
            time.sleep(5)

    return "Мозги не работают, спроси позже"  # Если все попытки провалились

