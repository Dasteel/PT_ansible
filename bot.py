

import logging
import re
import paramiko
import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, \
    CallbackQueryHandler
import psycopg2
from psycopg2 import Error
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler

dotenv_path = Path('../.env')
load_dotenv(dotenv_path=dotenv_path)


TOKEN = os.getenv('BOT_TOKEN')
RM_HOST = os.getenv('RM_HOST')
RM_PORT = os.getenv('RM_PORT')
RM_USER = os.getenv('RM_USER')
RM_PASSWORD = os.getenv('RM_PASSWORD')
HOST = os.getenv('HOST')

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_DATABASE = os.getenv('DB_DATABASE')

GET_ALL_PACKAGES, GET_PACKAGE_INFO = range(2)
GET_PHONE_NUMBERS, CONFIRM_PHONE_NUMBERS = range(2)
GET_EMAILS, CONFIRM_EMAIL_ADDRESSES = range(2)

logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'HELLO {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return GET_PHONE_NUMBERS

def findEmailsCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email адресов: ')

    return GET_EMAILS


def verify_passwordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')

    return 'verify_password'


def findPhoneNumbers(update: Update, context):
    user_input = update.message.text

    phoneNumRegex = re.compile(
        r'(?:\+7|8)[ -]?(?:\(\d{3}\)|\d{3})[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}')

    phoneNumberList = phoneNumRegex.findall(user_input)

    context.user_data['phone_numbers'] = phoneNumberList
    if not phoneNumberList:
        update.message.reply_text('Телефонные номера не найдены')
        return

    phoneNumbers = ''
    for i, phone_number in enumerate(phoneNumberList, start=1):
        phoneNumbers += f'{i}. {phone_number}\n'

    update.message.reply_text(phoneNumbers)

    keyboard = [[KeyboardButton("Записать в базу данных"), KeyboardButton("Отказаться")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    return CONFIRM_PHONE_NUMBERS


def confirmPhoneNumbers(update: Update, context):
    user_input = update.message.text

    if user_input == 'Записать в базу данных':
        try:
            connection = psycopg2.connect(user=DB_USER,
                                          password=DB_PASSWORD,
                                          host=DB_HOST,
                                          port=DB_PORT,
                                          database=DB_DATABASE)

            cursor = connection.cursor()

            phoneNumbers = context.user_data.get('phone_numbers', [])

            for phone_number in phoneNumbers:
                cursor.execute(f"INSERT INTO phone_number (phone) VALUES ('{phone_number}');")
            connection.commit()
            update.message.reply_text('Номера успешно записаны в базу данных!')
            logging.info("SUCCESS Команда успешно выполнена")
        except (Exception, Error) as error:
            logging.error("ERROR Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('ERROR Ошибка при добавлении номеров в базу данных')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
        return ConversationHandler.END

    elif user_input == 'Отказаться':
        update.message.reply_text("Вы отказались от записи номеров в базу данных.")
        return ConversationHandler.END

    else:
        update.message.reply_text("Пожалуйста, используйте кнопки для выбора действия.")
        return CONFIRM_PHONE_NUMBERS


conv_handler_confirm_phone_numbers = ConversationHandler(
    entry_points=[CommandHandler('find_phone_number', findPhoneNumbers)],
    states={
        'confirm_phone_numbers': [MessageHandler(Filters.text & ~Filters.command, confirmPhoneNumbers)],
    },
    fallbacks=[]
)



def findEmails(update: Update, context):
    user_input = update.message.text

    emailRegex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    emailList = emailRegex.findall(user_input)

    context.user_data['email_addresses'] = emailList
    if not emailList:
        update.message.reply_text('Email адреса не найдены')
        return

    emails = ''
    for i, email_address in enumerate(emailList, start=1):
        emails += f'{i}. {email_address}\n'

    update.message.reply_text(emails)

    keyboard = [[KeyboardButton("Записать в базу данных"), KeyboardButton("Отказаться")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    return CONFIRM_EMAIL_ADDRESSES


def confirmEmailAddresses(update: Update, context):
    user_input = update.message.text

    if user_input == 'Записать в базу данных':
        try:
            connection = psycopg2.connect(user=DB_USER,
                                          password=DB_PASSWORD,
                                          host=DB_HOST,
                                          port=DB_PORT,
                                          database=DB_DATABASE)

            cursor = connection.cursor()

            emailAddresses = context.user_data.get('email_addresses', [])

            for email_address in emailAddresses:
                cursor.execute(f"INSERT INTO email (email) VALUES ('{email_address}');")
            connection.commit()
            update.message.reply_text('Email адреса успешно записаны в базу данных!')
            logging.info("Команда успешно выполнена")
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('Ошибка при добавлении email адресов в базу данных')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
        return ConversationHandler.END

    elif user_input == 'Отказаться':
        update.message.reply_text("Вы отказались от записи email адресов в базу данных.")
        return ConversationHandler.END

    else:
        update.message.reply_text("Пожалуйста, используйте кнопки для выбора действия.")
        return CONFIRM_EMAIL_ADDRESSES


conv_handler_confirm_email_addresses = ConversationHandler(
    entry_points=[CommandHandler('find_email', findEmails)],
    states={
        'confirm_email_addresses': [MessageHandler(Filters.text & ~Filters.command, confirmEmailAddresses)],
    },
    fallbacks=[]
)

def verify_password(update: Update, context):
    user_input = update.message.text
    if re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$', user_input):
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')
    return ConversationHandler.END


def echo(update: Update, context):
    update.message.reply_text(update.message.text)



def ssh_command(hostname,port, username, password, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password)
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode()
    client.close()
    return output


def get_release(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'cat /etc/*release')
    update.message.reply_text(output)


def get_uname(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD,  'uname -a')
    update.message.reply_text(output)



def get_uptime(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'uptime')
    update.message.reply_text(output)


def get_df(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'df -h')
    update.message.reply_text(output)


def get_free(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'free -m')
    update.message.reply_text(output)


def get_mpstat(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'mpstat')
    update.message.reply_text(output)


def get_w(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'w')
    update.message.reply_text(output)


def get_auths(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'last -n 10')
    update.message.reply_text(output)


def get_critical(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'grep "CRITICAL" /var/log/syslog -n5')
    update.message.reply_text(output)

def get_ps(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'ps aux | tail -n 20')
    update.message.reply_text(output)


def get_ss(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'ss -tuln')
    update.message.reply_text(output)


def get_apt_list(update: Update, context):
    keyboard = [[InlineKeyboardButton('1. Вывести все пакеты', callback_data='get_all_packages'),
                 InlineKeyboardButton('2. Поиск по названию', callback_data='get_package_info')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите вариант:', reply_markup=reply_markup)
    return GET_ALL_PACKAGES


def get_all_packages(update: Update, context: CallbackContext):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'dpkg -l | tail -n 20')
    update.callback_query.edit_message_text(text=output)
    return GET_ALL_PACKAGES

def get_package_info(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text('Введите название пакета:')
    return GET_PACKAGE_INFO


def search_package_info(update: Update, context: CallbackContext):
    package_name = update.message.text
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, f'dpkg -l | grep {package_name}')
    update.message.reply_text(output)
    return GET_ALL_PACKAGES


def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    choice = query.data
    if choice == 'get_all_packages':
        get_all_packages(update, context)
    elif choice == 'get_package_info':
        get_package_info(update, context)


def get_services(update: Update, context):
    output = ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, 'systemctl list-units --type=service | tail -n 20')
    update.message.reply_text(output)


def get_emails(update: Update, context):
    connection = None
    try:
        connection = psycopg2.connect(user=DB_USER,
                                          password=DB_PASSWORD,
                                          host=DB_HOST,
                                          port=DB_PORT,
                                          database=DB_DATABASE)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM email;")
        data = cursor.fetchall()
        for row in data:
            print(row)
        update.message.reply_text(data)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
        return ConversationHandler.END


def get_phone_numbers(update: Update, context):
    connection = None
    try:
        connection = psycopg2.connect(user=DB_USER,
                                          password=DB_PASSWORD,
                                          host=DB_HOST,
                                          port=DB_PORT,
                                          database=DB_DATABASE)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phone_number;")
        data = cursor.fetchall()
        for row in data:
            print(row)
        update.message.reply_text(data)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
        return ConversationHandler.END


def get_repl_logs(update: Update, context):
    try:
        log_lines = get_log_lines(20)
        update.message.reply_text(log_lines)
        return ConversationHandler.END
    except Exception as e:
        update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END

def get_log_lines(limit):
    connection = None
    try:
        connection = psycopg2.connect(user=DB_USER,
                                      password=DB_PASSWORD,
                                      host=DB_HOST,
                                      port=DB_PORT,
                                      database=DB_DATABASE)

        cursor = connection.cursor()
        cursor.execute("SELECT pg_read_file('/var/log/postgresql/postgresql.log') AS log_content;")
        result = cursor.fetchone()
        if result:
            log_content = result[0]
            # Split log content into lines
            lines = log_content.split('\n')
            # Filter lines containing "replication" (case insensitive)
            replication_lines = [line for line in lines if 'replication' in line.lower()]
            # Return only the first 'limit' lines
            return '\n'.join(replication_lines[:limit])
        else:
            return "File content not found"
    except (Exception, Error) as error:
        return f"Error retrieving file content: {error}"
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    convHandlerpassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_passwordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )

    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            GET_PHONE_NUMBERS: [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            CONFIRM_PHONE_NUMBERS: [MessageHandler(Filters.text & ~Filters.command, confirmPhoneNumbers)],
        },
        fallbacks=[]
    )


    conv_handler_email = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            GET_EMAILS: [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            CONFIRM_EMAIL_ADDRESSES: [MessageHandler(Filters.text & ~Filters.command, confirmEmailAddresses)],
        },
        fallbacks=[]
    )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(conv_handler_email)
    dp.add_handler(convHandlerpassword)
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler('get_apt_list', get_apt_list))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, search_package_info))
    dp.add_handler(CommandHandler('get_repl_logs', get_repl_logs))
    dp.add_handler(CommandHandler('get_emails', get_emails))
    dp.add_handler(CommandHandler('get_phone_numbers', get_phone_numbers))


    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
