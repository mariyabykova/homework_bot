import logging
from msilib.schema import Error
import os
import sys
import time

from dotenv import load_dotenv
import telegram
import requests

# from .exceptions import (
#     ApiStatusCodeException, 
# )


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
    # timestamp = current_timestamp
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
            raise Exception(error_message)
        return homework_statuses.json()
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')


def check_response(response):
    """Проверка ответа от API."""
    if response.get('homeworks') is None:
        error_message = 'Ответ от API не содержит ключа homeworks.'
        logger.error(error_message)
        raise KeyError(error_message)
    if type(response) is not dict:
        error_message = 'Ответ от API имеет некорректный тип.'
        logger.error(error_message)
        raise TypeError(error_message)
    if type(response.get('homeworks')) is not list:
        error_message = (
            'Под ключом homeworks в ответе от API приходит не словарь.'
        )
        logger.error(error_message)
        raise TypeError(error_message)
    if response['homeworks'] == []:
        return {}
    return response['homeworks'][0]       


def parse_status(homework):
    """Извлечение информации о домашней работе."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_name is None:
        error_message = 'Ошибка: значение homework_name не найдено.'
        logger.error(error_message)
        raise KeyError(error_message)
    if homework_status is None:
        error_message = 'Ошибка: у домашней работы отсутствует статус.'
        logger.error(error_message)
        raise KeyError(error_message)
    if homework_status not in HOMEWORK_STATUSES:
        error_message = 'Ошибка: недокументированный статус домашней работы.'
        logger.error(error_message)
        raise KeyError(error_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    if PRACTICUM_TOKEN is None:
        logger.critical('Отсутствует PRACTICUM_TOKEN')
        return False
    if TELEGRAM_TOKEN is None:
        logger.critical('Отсутствует TELEGRAM_TOKEN')
        return False
    if TELEGRAM_CHAT_ID is None:
        logger.critical('Отсутствует TELEGRAM_CHAT_ID')
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        exit()
        # logger.critical('Токены не найдены.')
        # raise Exception('Токены не найдены. Программа прервана.')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp =int(time.time())
    send_message(bot, 'Бот включился.')
    # response = get_api_answer(current_timestamp)
    # checked_homework = check_response(response)
    # status = parse_status(checked_homework)
    # send_message(bot, status)
    # print(status)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            checked_homework = check_response(response)
            if checked_homework:
                homework_status = parse_status(checked_homework)
                send_message(bot, homework_status)
                if homework_status is None:
                    send_message(bot, 'Нет новых статусов')
            else:
                logger.debug('В ответе нет новых статусов.')
                send_message(bot, 'В ответе нет новых статусов.')
                current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.critical(message)
            time.sleep(RETRY_TIME)
        finally:
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)



if __name__ == '__main__':
    main()
