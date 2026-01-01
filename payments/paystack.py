# payments/paystack.py
import requests
from django.conf import settings

class Paystack:
    def __init__(self):
        self.headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        self.base_url = settings.PAYSTACK_URL

    def initialize_transaction(self, email, amount, reference, callback_url):
        url = f"{self.base_url}/transaction/initialize"
        
        # Paystack expects amount in Kobo (multiply by 100)
        data = {
            "email": email,
            "amount": int(amount * 100), 
            "reference": reference,
            "callback_url": callback_url
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'status': False, 'message': str(e)}

    def verify_transaction(self, reference):
        url = f"{self.base_url}/transaction/verify/{reference}"
        
        try:
            response = requests.get(url, headers=self.headers)
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'status': False, 'message': str(e)}