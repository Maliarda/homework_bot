# Бот-ассистент для студента Яндекс.Практикума
## Что делает бот?

- раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверяет статус отправленной на ревью домашней работы;
- при обновлении статуса анализирует ответ API и отправляет студенту соответствующее уведомление в Telegram;
- логирует свою работу и сообщаем студенту о важных проблемах сообщением в Telegram.
 
## Технологии

[Telegram Bot API](https://core.telegram.org/bots/api) - The Bot API is an HTTP-based interface created for developers keen on building bots for Telegram.
[Python Telegram Bot](https://github.com/python-telegram-bot/python-telegram-bot) - This library provides a pure Python interface for the Telegram Bot API.
