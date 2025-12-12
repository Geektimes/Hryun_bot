# utils/AI_model.py
import logging

from config import load_config
from utils.google_model import google_model

logger = logging.getLogger(__name__)
config = load_config()

class AI_model:
    def __init__(self):        
        self.model = google_model


    @staticmethod
    def make_message_for_g_model(role_is, message):
        if role_is == 'hryn':
            role = config.HRYUN_PROMPT
        elif role_is == 'summary':
            role = config.SUMMARY_PROMPT
        else:
            role = config.ASSISTANT
        
        return [
            {
                "role": "user",
                "parts": [{"text": role}]
            },
            {
                "role": "user",
                "parts": [{"text": message}]
            }
        ]
    

    def ask(self, message, role='hryn', context=None):
        new_message = AI_model.make_message_for_g_model(role, message)

        # Формируем список сообщений с историей
        messages = context if context else []  # Берём историю, если есть

        # Добавляем текущее сообщение в контекст
        messages.extend(new_message)
        
        models = [self.model]
        max_retries = 1

        for model in models:
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"\nСообщения, отправляемые в запрос: {messages}\n")
                    response = model.generate_content(messages).text
                    answer = response[:4000] if len(response) > 4000 else response
                    logger.info(f"Ответ от AI ({model}): {answer}")
                    if response:
                        return response
                except Exception as e:
                    logger.error(f"Ошибка при запросе к {model} (попытка {attempt}): {e}", exc_info=False)
                   

        return "ИИ отвалился, спроси потом когда нибудь"  # Если все попытки провалились