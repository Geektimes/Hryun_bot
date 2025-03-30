import os
import requests
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv('API_KEY')
API_URL = os.getenv('API_URL')

headers = {f"Authorization": f"Bearer {API_KEY}"}  # Укажите ваш API-ключ

response = requests.get(API_URL, headers=headers)

if response.status_code == 200:
    print(f"Response:\n{response.json()}")
    for i in response.json()[0]:
        print(i)

else:
    print("Error:", response.status_code, response.text)
