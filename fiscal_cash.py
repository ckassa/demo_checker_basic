from src import config
from requests.auth import HTTPBasicAuth
import json
import requests
import time
from loguru import logger

logger.add(f'extentions/demo_checker/src/log/{__name__}.log', format='{time} {level} {message}', level='DEBUG', rotation='10 MB', compression='zip')
auth = HTTPBasicAuth(config.shopToken, config.sec_key)
s = requests.Session()
user = {'fiscal_retry': 0}


def create_anonimus_pay():
    print('/do/payment/anonymous...', end='')
    url = config.anonimus_pay_url
    payload = {
        "serviceCode": "15636-15727-1",
        "amount": "2500",
        "comission": "0",
        "payType": "fiscalCash",
        "properties": [
            {
                "name": "Л_СЧЕТ",
                "value": "9523238186"
            },
            {
                "name": "automatNumber",
                "value": "Тест"
            },
            {
                "name": "settlementPlace",
                "value": "Тестовый адрес"
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0",
    }
    r = s.post(url, data=json.dumps(payload), headers=headers, auth=auth)
    response = r.json()
    #logger.info(f'response: {response}')
    # Сначала зачистим переменную с кол-вом попыток выгрузки фискального чека.
    # Подход костыльный, его надо поправить.
    user['fiscal_retry'] = 0
    #logger.info(f'response: {response}')
    try:
        regPayNum = response['regPayNum']
        user['regPayNum'] = regPayNum
        if regPayNum != '':
            print('OK')
        else:
            print(f'Something wrong! Key Error. Url: {url}, response: {response}')
    except KeyError:
        print(f'Something wrong! Key Error. Url: {url}, response: {response}')


def check_pay_status():
    url = config.payment_state_url
    print('Check payment state...', end='')
    try:
        payload = {
            "regPayNum": f"{user['regPayNum']}"
        }
        headers = {
            "Content-Type": "application/json"
        }
        r = s.post(url, data=json.dumps(payload), headers=headers, auth=auth)
        response = r.json()
        #logger.info(f'response: {response}')
        payment_state = response['state']
        if payment_state == 'payed':
            print('OK')
        elif payment_state == 'created':
            #logger.info(f'retry: {user["fiscal_retry"]}')
            if user['fiscal_retry'] <= 3:
                print(f' Warn: Payment state: {payment_state}. Retry...')
                time.sleep(5)
                user['fiscal_retry'] += 1
                check_pay_status()
            else:
                logger.error(f'Платеж {user["regPayNum"]} висит в статусе created')
                print(f'Платеж {user["regPayNum"]} висит в статусе created')
        else:
            # print(f'Something wrong! payment state: {payment_state} Request: {}')
            print(f'Something wrong! payment state: {payment_state} response: {response}')
    except KeyError:
        logger.error('Unable to send : KeyError in response')
        print('Key error')


def get_fiscal_check():
    url = config.fiscal_check_url
    headers = {
        "Content-Type": "application/json"
    }
    try:
        payload = {
            "regPayNum": f"{user['regPayNum']}"
        }
        print('/receipt-fiscal...', end='')
        r = s.post(url, data=json.dumps(payload), headers=headers, auth=auth)
        response = r.json()
        #logger.info(f'response: {response}')
        fiscal_url = response['fiscalUrl']
        if fiscal_url:
            print('OK')
        else:
            print(f'Something wrong! Key Error. Url: {url}, response: {response}')
    except KeyError:
        logger.error('Unable to send response: KeyError in payload')
        print('Key error')
