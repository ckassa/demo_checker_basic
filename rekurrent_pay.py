import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth
import json
from src import config
import time
import random
from loguru import logger

logger.add(f'extentions/demo_checker/src/log/{__name__}.log', format='{time} {level} {message}', level='DEBUG', rotation='10 MB', compression='zip')
auth = HTTPBasicAuth(config.shopToken, config.sec_key)
s = requests.Session()
user = {}  # Для записи локальных переменных в глобальную
json_headers = {'Content-Type': 'application/json'}


def user_registration():
    print('\nCheck rekurrent payment methods:\n')
    print('/user/registration...', end='')
    url = config.user_registration_rek_url
    login = '7902' + f'{random.randint(1000000, 9999999)}'
    payload = {
        "login": f"{login}"
    }

    r = s.post(url, data=json.dumps(payload), headers=json_headers, auth=auth)  # тут есть login, userToken
    #logger.info(f'response: {r.json()}')
    if r.status_code == 200:  # !!! этот кусок не пашет. Если демо ляжет, то в предыдущей строке бот крашнется
        request = r.json()
        try:
            print('OK')
            user['login'] = request['login']
        except KeyError:
            print(f'Something wrong! url: {url}, request: {request}\n')
    else:
        print(f'\nuser_registration: http error. request status code: {r.status_code}')
        #logger.error(f'\nuser_registration: http error. request status code: {r.status_code}')
        raise HTTPError


def get_user_status():
    print('/user/status...', end='')
    url = config.user_status_rek_url
    payload = {
        "login": f"{user['login']}"
    }
    r = s.post(url, data=json.dumps(payload), headers=json_headers, auth=auth)
    response = r.json()
    #logger.info(f'response: {r.text}')
    if response['state'] == 'active':
        print('OK')
    else:
        print(f'Something wrong! url: {url}, response: {response}')
    userToken = response['userToken']
    user['userToken'] = userToken  # Записываем в глобальную переменную


def get_cards_rek():
    url = config.get_cards_rek_url
    print('/get/cards...', end='')
    payload = {
        "userToken": f"{user['userToken']}",
    }
    r = s.post(url, data=json.dumps(payload), headers=json_headers, auth=auth)
    response = r.json()
    #logger.info(f'response: {response}')
    cards = response['cards']
    user['cards'] = cards  # Записал в глобальную переменную
    if cards:
        print('OK')
    else:
        print(f'No cards.')


def card_registration():
    print('/card/registration...', end='')
    url = config.card_registration_url_rek
    payload = {
        "userToken": f"{user['userToken']}"
    }
    r = s.post(url, data=json.dumps(payload), headers=json_headers, auth=auth)
    response = r.json()
    #logger.info(f'response: {response}')
    registration_url = response['payUrl']
    order = registration_url.replace('https://demo-acq.bisys.ru/cardpay/card?order=', '')

    # Открываем payUrl чтоб перехватить Cookies
    s.get(registration_url, headers=json_headers)
    cookies = s.cookies.get_dict()

    reg_payload = {
        "form": "default",
        "operation": "checkpay",
        "order": f"{order}",
        "type": "visa",
        "pan": "4000000000000002",
        "exp": "01 21",
        "holder": "hard support",
        "secret": "123"
    }

    reg_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": f"{registration_url}",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0",
        "Cookies": f"{cookies}"
    }
    reg_url = 'https://demo-acq.bisys.ru/cardpay/api/C/rpcheck'
    reg_request = s.post(reg_url, data=reg_payload, headers=reg_headers, auth=auth)
    #logger.info(f'reg_response: {reg_request.text}')
    if reg_request.status_code == 200:
        print('OK')
    else:
        print(f'Something wrong! url: {url} request: {reg_request}')


def do_payment():

    url = config.do_payment_rek_url
    print('/do/payment...', end='')
    # Сначала запишем действующие карты по клиенту
    get_cards_rek()
    try:
        cardToken = user['cards'][0]['cardToken']  # Берем первую привязанную карту
    except IndexError:
        print('IndexError... No cards. Start method /card/registration...')
        card_registration()  # пробуем повторно зарегать карту
        try:
            cardToken = user['cards'][0]['cardToken']
        except IndexError:
            print('IndexError... No cards. Stop method.')
            return
    payload = {
        "serviceCode": f"{config.service_code}",
        "userToken": f"{user['userToken']}",
        "amount": "2500",
        "comission": "0",
        "cardToken": f"{cardToken}",  # берем первую привязанную карту
        "holdTtl": "345600",
        "properties": [
            {
                "name": "ПОЗЫВНОЙ",
                "value": f"{random.randint(10, 20)}"
            }
        ]
    }
    r = s.post(url, data=json.dumps(payload), headers=json_headers, auth=auth)
    response = r.json()
    #logger.info(f'response: {response}')
    regPayNum = response['regPayNum']
    user['regPayNum'] = regPayNum  # Записал в глобальную переменную
    if regPayNum:
        print('OK')
    else:
        print(f'Something wrong! url: {url} response: {response}')


def confirm_pay():
    url = config.confirm_pay_rek_url
    print('/provision-services/confirm...', end='')
    try:
        regPayNum = user['regPayNum']
    except KeyError:
        print('No regPayNum. Stop Method')
        return
    payload = {
        "regPayNum": f"{regPayNum}",
        "orderId": f"{random.randint(1000000, 2000000)}"  # Рандом потому что тут номер заказа в системе клиента
    }
    r = s.post(url, data=json.dumps(payload), headers=json_headers, auth=auth)
    response = r.json()
    #logger.info(f'response: {response}')
    try:
        result = response['resultState']
        if result == 'success':
            user['payment_state'] = result
            print('OK')
        else:
            print(f'Something wrong! url: {url} response: {response}')
    except KeyError:
        print(f'Response key error. url: {url} response: {response}')
        logger.error(f'Response key error. url: {url} response: {response}')


def get_pay_state():
    url = config.get_pay_state_url
    print('/payment/state...', end='')
    try:
        regPayNum = user['regPayNum']
    except KeyError:
        print('No regPayNum. Stop Method')
        return
    payload = {
        "regPayNum": f"{regPayNum}"
    }
    r = s.post(url, data=json.dumps(payload), headers=json_headers, auth=auth)
    response = r.json()
    #logger.info(f'response: {response}')
    try:
        payment_state = response['state']
        if payment_state:
            print('OK')
            user['payment_state'] = payment_state
        else:
            print(f'Something wrong! url: {url} response: {response}')
    except KeyError:
        print(f'Response key error. url: {url} response: {response}')
        logger.error(f'Response key error. url: {url} response: {response}')


def refund_payment():
    url = config.refund_rek_url
    # Сначала выполняем функцию создания платежа с указанием holdttl
    # будет новый regPayNum, он перезапишется в глобальный словарь user
    do_payment()
    # таймаут 3 секунды, иначе возвращается статус created
    time.sleep(3)
    print('/provision-services/refund...', end='')
    try:
        regPayNum = user['regPayNum']
    except KeyError:
        print('No regPayNum. Stop Method')
        return
    payload = {
        "regPayNum": f"{regPayNum}",
        "orderId": f"{random.randint(10, 20)}",
    }
    r = s.post(url, data=json.dumps(payload), headers=json_headers, auth=auth)
    response = r.json()
    #logger.info(f'response: {response}')
    try:
        result = response['resultState']
        if result == 'success':
            print('OK')
        else:
            print(f'Something wrong! url: {url} response: {response}')
    except KeyError:
        print(f'Response key error. url: {url} response: {response}')
        logger.error(f'Response key error. url: {url} response: {response}')


def card_deactivation():
    url = config.card_deactivation_url
    print('/card/deatcivation...', end='')
    try:
        cardToken = user['cards'][0]['cardToken']  # Берем первую карту
    except IndexError:
        print('No cards. Stop method')
        return
    payload = {
        "userToken": f"{user['userToken']}",
        "cardToken": f"{cardToken}"
    }
    r = s.post(url, data=json.dumps(payload), headers=json_headers, auth=auth)
    response = r.json()
    #logger.info(f'response: {response}')
    result = response['resultState']
    if result == 'success':
        print('OK')
    else:
        print(f'Something wrong! url: {url} response: {response}')