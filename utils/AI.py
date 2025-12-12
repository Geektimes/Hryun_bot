# AI.py
import os
from openai import OpenAI
import time
import logging

from config import load_config


config = load_config()

logger = logging.getLogger(__name__)


class LLM:
  def __init__(self):
    self.API_KEY = config.API_KEY
    self.API_URL = config.API_URL
    self.model_gemini_pro_2_5 = config.MODEL_GEMINI_PRO_2_5
    self.model_qwen = config.MODEL_QWEN_2_5
    self.model_deepseek = config.MODEL_DEEPSEEK_V3
    self.model_gemma = config.MODEL_GEMMA_3_27B
    self.model_mistral = config.MODEL_MISTRAL_SMALL_3_1

  def make_client(self):
    return OpenAI(
      base_url=self.API_URL,
      api_key=self.API_KEY,
    )

  @staticmethod
  def get_messages(role, msg):
    # logger.info(f"\nrequests_limit к OpenAI.: {requests_limit}\n")
    if role == 'hryn':
      messages = [
        {"role": "system", "content": config.HRYUN_PROMPT},
        {"role": "user", "content": msg}
      ]
    elif role == 'summary':
      # print(f"\n\nROLE:: {role}\n PROMT:: {summary_prompt}\n CONTENT:: {msg}")
      messages = [
        {"role": "system", "content": config.SUMMARY_PROMPT},
        {"role": "user", "content": msg}
      ]
    else:
      messages = [
        {"role": "system", "content": config.ASSISTANT},
        {"role": "user", "content": msg}
      ]
    return messages

  def ask(self, msg, role='hryn', context=None):
    # logger.info(f"Отправка запроса к OpenAI. Текст: {msg}, Роль: {role}")
    client = self.make_client()

    new_message = LLM.get_messages(role, msg)

    # Формируем список сообщений с историей
    messages = context if context else []  # Берём историю, если есть

    # Добавляем текущее сообщение в контекст
    messages.extend(new_message)
    # print(f"\nMESSAGA:: {messages}\n")
    headers = {
      "HTTP-Referer": "<YOUR_SITE_URL>",
      "X-Title": "<YOUR_SITE_NAME>",
    }
    models = ["google/gemma-3-27b-it:free"]
    # models = ["tngtech/deepseek-r1t2-chimera:free"]
    # models = [self.model_gemini_pro_2_5, self.model_gemma]
    # models = [self.model_gemini_pro_2_5]
    # models = [self.model_gemma]
    # models = [self.model_mistral]
    # models = [self.model_deepseek]
    # models = [self.model_qwen]
    max_retries = 1

    for model in models:
      for attempt in range(1, max_retries + 1):
        try:
          logger.info(f"\nСообщения, отправляемые в запрос: {messages}\n")

          completion = client.chat.completions.create(
            extra_headers=headers,
            extra_body={},
            model=model,
            messages=messages
          )
          logger.info(f"Ответ от OpenAI ({model}): {completion}")

          response = completion.choices[0].message.content
          response = response[:4000] if len(response) > 4000 else response

          if response:
            return response
        except Exception as e:
          logger.error(f"Ошибка при запросе к {model} (попытка {attempt}): {e}", exc_info=False)
          if attempt < max_retries:
            time.sleep(11)

    return "ИИ отвалился, спроси потом когда нибудь"  # Если все попытки провалились

