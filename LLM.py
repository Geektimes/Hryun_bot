# LLM.py
import os
from openai import OpenAI
import logging
import time
import yaml

requests_limit = 199

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
    self.model_gemini_pro_2_5 = os.getenv('MODEL_GEMINI_PRO_2_5')
    self.model_qwen = os.getenv('MODEL_QWEN_2_5')
    self.model_deepseek = os.getenv('MODEL_DEEPSEEK_V3')
    self.model_gemma = os.getenv('MODEL_GEMMA_3_27B')
    self.model_mistral = os.getenv('MODEL_MISTRAL_SMALL_3_1')

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
        {"role": "system", "content": hryun_promt},
        {"role": "user", "content": msg}
      ]
    elif role == 'summary':
      # print(f"\n\nROLE:: {role}\n PROMT:: {summary_prompt}\n CONTENT:: {msg}")
      messages = [
        {"role": "system", "content": summary_prompt},
        {"role": "user", "content": msg}
      ]
    else:
      messages = [
        {"role": "system", "content": "a smart helpful assistant"},
        {"role": "user", "content": msg}
      ]
    return messages

  def ask(self, msg, role='hryn', history=None):
    # logger.info(f"Отправка запроса к OpenAI. Текст: {msg}, Роль: {role}")
    client = self.make_client()

    new_message = LLM.get_messages(role, msg)

    # Формируем список сообщений с историей
    messages = history if history else []  # Берём историю, если есть

    # Добавляем текущее сообщение в контекст
    messages.extend(new_message)

    headers = {
      "HTTP-Referer": "<YOUR_SITE_URL>",
      "X-Title": "<YOUR_SITE_NAME>",
    }

    models = [self.model_gemini_pro_2_5, self.model_gemma]
    # models = [self.model_gemini_pro_2_5]
    # models = [self.model_gemma]
    # models = [self.model_mistral]
    # models = [self.model_deepseek]
    # models = [self.model_qwen]
    max_retries = 3

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

          if response:
            return response
        except Exception as e:
          logger.error(f"Ошибка при запросе к {model} (попытка {attempt}): {e}", exc_info=False)
          if attempt < max_retries:
            time.sleep(11)

    return "Мозги не работают, спроси позже"  # Если все попытки провалились

