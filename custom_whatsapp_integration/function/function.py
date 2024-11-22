
from datetime import datetime,timedelta,date
import json
import requests

import string
import secrets


# def get_credentials():
#     return {
#         'url' : 'https://api.dial.id',
#         'clientSid' : '4450282D1B164D68A6B43AF40F024D52',
#         'key' : '92496e46ca47468',
#         'password' : '73121d14f6af422',
#     }

def generate_refid():
    alphabet = string.ascii_letters + string.digits
    random = ''.join(secrets.choice(alphabet) for i in range(20))
    return random

# def get_list_template():
#     return [
#         'template_po',
#         'template_crm',
#         'template_po2'
#     ]

def encrypt_sha256(text):
    import hashlib
    result = hashlib.sha256(text.encode('UTF-8'))
    return result.hexdigest()

def send_whatsapp_message(credentials, to, template, body_template = {}):
    refId = generate_refid()
    auth =  encrypt_sha256(refId + credentials.get('key') + credentials.get('password'))

    
    url = "{url}//waba/v2/message".format(
        url = credentials.get('url')
    )
    headers = {
        'Content-Type': 'application/json'
    }
    body = {
        "clientSid": credentials.get('clientSid'),
        "refId": refId,
        "key": credentials.get('key'),
        "auth": auth,
        "to": to,
        "template":{
            "name":template,
            "language":"id",
            "body": body_template
        }
    }

    payload = json.dumps(body)
    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()

    return data