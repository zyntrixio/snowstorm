import requests

from snowstorm.settings import settings

api_key = settings.freshservice_api_key
r = requests.get("https://bink.freshservice.com/api/v2/tickets", params={"per_page": 100}, auth=(api_key, "X"))
