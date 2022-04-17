import json
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s, %(levelname)s, %(message)s",
    filename="my_log.txt",
)


handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info("Сообщение отправлено в Telegram")
    except telegram.TelegramError:
        logger.error("Произошел сбой при отправке сообщения в Telegram")


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    try:
        hw_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as e:
        message = f"Яндекс.Практикум вернул ошибку: {e}"
        logging.error(message, exc_info=True)
    if hw_statuses.status_code != HTTPStatus.OK:
        message = "Сбой при запросе к API-сервису"
        logger.error(message, exc_info=True)
        raise exceptions.APINoResponseException(message)
    try:
        return hw_statuses.json()
    except json.JSONDecodeError:
        message = "Ответ сервера не преобразовался в json"
        logging.error(message)


def check_response(response):
    """Проверяет ответ API на корректность."""
    try:
        homeworks_list = response["homeworks"]
    except KeyError as e:
        message = f"Ожидаемые ключи отсутствуют: {e}"
        logger.error(message)
        raise exceptions.CheckResponseException(message)
    if not isinstance(homeworks_list, list):
        message = "Ответ не в виде списка домашних работ"
        logger.error(message)
        raise exceptions.HwNotListException(message)
    if len(homeworks_list) == 0:
        message = "Домашних работ на проверке не обнаружено"
        logger.error(message)
        raise exceptions.CheckResponseException(message)
    return homeworks_list


def parse_status(homework):
    """Извлекает из запроса статус домашней работы."""
    try:
        homework_name = homework["homework_name"]
    except KeyError as e:
        message = f"Ошибка доступа по ключу homework_name: {e}"
        logger.error(message)
    homework_status = homework.get("status")
    if (homework_status is None) or (homework_status == ""):
        logging.error(f"Статус работы некорректен: {homework_status}")
    verdict = HOMEWORK_STATUSES[homework_status]
    if homework_status not in HOMEWORK_STATUSES:
        message = "Неизвестный статус домашней работы"
        logger.error(message)
        raise exceptions.UnknownHwStatusException(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = "В наличии не все обязательные переменные окружения"
        logger.critical(message)
        raise exceptions.MissingTokenException(message)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previous_status = None
    previous_error = None

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = int(time.time())
            homeworks = check_response(response)
            hw_status = homeworks[0].get("status")
            if hw_status != previous_status:
                previous_status = hw_status
                message = parse_status(homeworks[0])
                send_message(bot, message)
                logger.info(f"Отправлено сообщение: {message}")
            else:
                logger.debug("Обновления статуса нет")

            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            if previous_error != str(error):
                previous_error = str(error)
                send_message(bot, message)
            logger.error(message)
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    main()
