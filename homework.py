import os
import logging
import requests
import sys
import time

import telegram

from dotenv import load_dotenv

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
    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


class ApiStatusCodeException(Exception):
    """Ошибка запроса к основному API:
    статус-код не равен 200."""
    pass


class HomeWorkIsNoneException(Exception):
    """Отсутствует значение homework_name."""
    pass


class HomeworkStatusIsNoneException(Exception):
    """У домашней работы отсутствует статус."""
    pass


def send_message(bot, message):
    """Отправка сообщения."""
    ...


def get_api_answer(current_timestamp):
    """Получение данных от API Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
            )
        if homework_statuses.status_code != 200:
            error_message = (
                f'Ошибка при запросе к основному API.'
                f'Статус-код API: {homework_statuses.status_code}.'
            )
            logger.error(error_message)
            raise ApiStatusCodeException(error_message)
        return homework_statuses.json()
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')


def check_response(response):
    
    ...


def parse_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        error_message = 'Значение homework_name не найдено.'
        logger.error(error_message)
        raise HomeWorkIsNoneException(error_message)
    if homework_status is None:
        error_message = 'У домашней работы отсутствует статус.'
        logger.error(error_message)
        raise HomeworkStatusIsNoneException(error_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    token = True
    if PRACTICUM_TOKEN is None:
        token = False
        logger.critical('Отсутствует PRACTICUM_TOKEN')
    if TELEGRAM_TOKEN is None:
        token = False
        logger.critical('Отсутствует TELEGRAM_TOKEN')
    if TELEGRAM_CHAT_ID is None:
        token = False
        logger.critical('Отсутствует TELEGRAM_CHAT_ID')
    return token


def main():
    """Основная логика работы бота."""

    ...

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    ...

    while True:
        try:
            response = get_api_answer(current_timestamp)
            checked_homework = check_response(response)

            ...

            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()
