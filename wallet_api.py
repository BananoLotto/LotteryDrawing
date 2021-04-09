import requests
import settings
import uuid
import json

def get_balance(account):
    d = {
        "action": "account_balance",
        "account": account
    }
    data = json.dumps(d)
    return requests.post(settings.wallet_api, data)

def receive_pending(account):
    d = {
        "action": "receive_all",
        "wallet": settings.wallet_id
    }
    data = json.dumps(d)
    return requests.post(settings.wallet_api, data)

def get_transactions(account, count):
    d = {
        "action": "account_history",
        "account": account,
        "count": count
    }
    data = json.dumps(d)
    return requests.post(settings.wallet_api, data)

def send_banano(address, amount):
    d = {
        "action": "send",
        "wallet": settings.wallet_id,
        "source": settings.ban_account,
        "destination": address,
        "amount": amount,
        "id": str(uuid.uuid1())
    }
    data = json.dumps(d)
    return requests.post(settings.wallet_api, data)
