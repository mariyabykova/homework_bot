import logging
import os
import sys
import time
from http import HTTPStatus

from dotenv import load_dotenv
import telegram
import requests

from exceptions import RequestApiException

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'В Телеграм отправлено сообщение: {message}')
    except Exception as telegram_error:
        logger.error(
            f'Ошибка: {telegram_error}. В Телеграм не отправлено сообщение.'
        )


def get_api_answer(current_timestamp):
    """Получение данных от API Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except Exception as error:
        error_message = f'Ошибка при запросе к основному API: {error}'
        logger.error(error_message)
        raise RequestApiException(error_message)
    else:
        if homework_statuses.status_code != HTTPStatus.OK:
            error_message = (
                f'Ошибка при запросе к API.'
                f'Статус-код API: {homework_statuses.status_code}.'
            )
            logger.error(error_message)
            raise RequestApiException(error_message)
    return homework_statuses.json()


def check_response(response):
    """Проверка ответа от API."""
    if not isinstance(response, dict):
        error_message = 'Ответ от API имеет некорректный тип.'
        logger.error(error_message)
        raise TypeError(error_message)
    if 'homeworks' not in response.keys():
        error_message = 'Ответ от API не содержит ключа homeworks.'
        logger.error(error_message)
        raise KeyError(error_message)
    if not isinstance(response.get('homeworks'), list):
        error_message = (
            'Под ключом homeworks в ответе от API приходит не словарь.'
        )
        logger.error(error_message)
        raise TypeError(error_message)
    return response['homeworks']


def parse_status(homework):
    """Извлечение информации о домашней работе."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    check_key(homework_status, 'status')
    check_key(homework_name, 'homework_name')
    if homework_status not in HOMEWORK_STATUSES:
        error_message = 'Ошибка: недокументированный статус домашней работы.'
        logger.error(error_message)
        raise KeyError(error_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_key(dict_value, dict_key):
    """Проверка наличия значений ключей словаря."""
    if not dict_value:
        error_message = f'Ошибка. Значение {dict_key} не найдено.'
        logger.error(error_message)
        raise KeyError(error_message)


def check_tokens():
    """Проверка токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Токены не найдены. Программа прервана.')
        raise ValueError('Токены не найдены.')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    initial_status = ''
    initial_error_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            checked_homework = check_response(response)
            if checked_homework:
                homework_status = parse_status(checked_homework[0])
                if homework_status != initial_status:
                    send_message(bot, homework_status)
                    initial_status = homework_status
            else:
                logger.debug('В ответе нет новых статусов.')
                send_message(bot, 'В ответе нет новых статусов.')
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != initial_error_message:
                send_message(bot, message)
                initial_error_message = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
