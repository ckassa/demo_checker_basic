import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth
import json
from src import config
import time
import random
from loguru import logger

logger.add(f'extentions/demo_checker/src/log/{__name__}.log', format='{time} {level} {message}', level='DEBUG', rotation='10 MB', compression='zip')
s = requests.Session()
# Приватный ключ через тектсовик я вытащил из серта pem, затем командой
# "openssl rsa -in my.key_encrypted -out my.key_decrypted" (со вводом пароля) расшифровал закрытый ключ
# s.cert = (config.sert_path, config.key_path)
auth = HTTPBasicAuth(config.shopToken, config.sec_key)
user = {'fiscal_retry': 0}


#@logger.catch()
def create_anonimus_pay():
    #logger.info('Check method /do/payment/anonymous...')
    print('\nCheck anonimus payment methods:\n')
    print('/do/payment/anonymous...', end='')
    url = config.anonimus_pay_url
    payload = {
        "serviceCode": f"{config.service_code}",
        "amount": "2500",
        "comission": "0",
        "properties": [
            {
                "name": "ПОЗЫВНОЙ",
                "value": f"{random.randint(10, 20)}"
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0",
    }
    r = s.post(url, data=json.dumps(payload), headers=headers, auth=auth)
    #logger.info(f'responce: {r.text}')
    if r.status_code == 200:
        request = r.json()
    else:
        print(f'\ncreate_anonimus_pay: http error. request status code: {r.status_code}')
        logger.error(f'\ncreate_anonimus_pay: http error. request status code: {r.status_code}')
        raise HTTPError

    try:
        user['regPayNum'] = request['regPayNum']
        user['payUrl'] = request['payUrl']
        user['methodType'] = request['methodType']
    except KeyError:
        print(f'Something wrong! Key Error. Url: {url}, request: {request}')

    if user['methodType'] == 'GET' and 'https://demo-acq.bisys.ru/cardpay/card?order=' in user['payUrl'] and user['regPayNum']:
        print('OK')
    else:
        print(f'Something wrong!\nrequest_status_code: {r.status_code}\nrequest: {request}\n')
    # Открываем полученную ссылку, чтоб перехватить Cookies
    s.get(user['payUrl'], headers=headers)
    user['cookies'] = s.cookies.get_dict()


def payment_created_pay():
    #logger.info('Trying to payment created pay')
    print('Trying to payment created pay...\nSend a POST request...', end='')
    order = user['payUrl'].replace('https://demo-acq.bisys.ru/cardpay/card?order=', '')
    payload = {
        "form": "default",
        "operation": "pay",
        "order": f"{order}",
        "type": "visa",
        "pan": "4000000000000002",
        "exp": "01 21",
        "holder": "hard support",
        "secret": "123"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": f"{user['payUrl']}",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0",
        "Cookies": f"{user['cookies']}"
    }

    url = config.acq_pay_url
    r = s.post(url, data=payload, headers=headers, auth=auth)
    if r.status_code == 200:
        print('Response code == 200 OK')
    else:
        print(f'Something wrong!\nrequest_status_code: {r.status_code}\nrequest_text: {r.text}\n')


def check_pay_status():
    url = config.payment_state_url
    #logger.info('Check payment state...')
    print('Check payment state...', end='')
    payload = {
        "regPayNum": f"{user['regPayNum']}"
    }
    headers = {
        "Content-Type": "application/json"
    }
    r = s.post(url, data=json.dumps(payload), headers=headers, auth=auth)
    #logger.info(f'response: {r.text}')
    request = r.json()
    payment_state = request['state']
    if payment_state == 'payed':
        print('OK\n')
    elif payment_state == 'created':
        if user['fiscal_retry'] <= 3:
            print(f'Payment state: {payment_state}. Retry...')
            time.sleep(3)
            user['fiscal_retry'] += 1
            check_pay_status()
    else:
        print(f'Something wrong! payment state: {payment_state}\n')