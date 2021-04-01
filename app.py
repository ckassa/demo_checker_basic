import time
import anonimus_pay
import rekurrent_pay
import fiscal_cash
from loguru import logger

logger.add(f'log/{__name__}.log', format='{time} {level} {message}', level='DEBUG', rotation='10 MB', compression='zip')


def autotest_anonimus_pay():
    anonimus_pay.create_anonimus_pay()
    anonimus_pay.payment_created_pay()
    anonimus_pay.check_pay_status()


def autotest_rekurrent_pay():
    rekurrent_pay.user_registration()
    rekurrent_pay.get_user_status()
    rekurrent_pay.card_registration()
    # Если не взять паузу, то autopays может не успеть записать привязанную карту и возвращает пустой массив с картами
    time.sleep(3)
    rekurrent_pay.get_cards_rek()
    rekurrent_pay.do_payment()
    time.sleep(3)
    rekurrent_pay.get_pay_state()
    rekurrent_pay.confirm_pay()
    rekurrent_pay.refund_payment()
    rekurrent_pay.card_deactivation()


def autotest_fiscal_cash_pay():
    fiscal_cash.create_anonimus_pay()
    fiscal_cash.check_pay_status()
    fiscal_cash.get_fiscal_check()


if __name__ == '__main__':
    try:
        autotest_anonimus_pay()
        autotest_rekurrent_pay()
        autotest_fiscal_cash_pay()
    except KeyboardInterrupt:
        logger.info('Program has been stoped manually')