import logging
import sqlite3
import datetime

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Application, MessageHandler, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    global username
    user = update.effective_user
    username = update.message.from_user.username
    cur.execute(f"""INSERT INTO users(user) VALUES({username})""")

    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я дз-бот. Я помогу тебе не забыть ни про одно дз.", reply_markup=markup)


async def get_dz_subject(update, username):
    """Отправляет дз по предмету когда получена команда /get_dz_subject"""
    await update.message.reply_text('''Выбери предмет из списка ниже и напиши только его номер''')
    text = update.message.text
    not_done = "не сделано"
    result = cur.execute(f"""SELECT date, text FROM dz
                WHERE subgect_id={int(text)} and state={not_done} and user_id=(SELECT id FROM users WHERE user={username})""").fetchall()
    result = [' '.join(list(i)) for i in result]

    await update.message.reply_text('\n'.join(result), reply_markup=markup)


async def get_dz_day(update, context):
    """Отправляет дз на день когда получена команда /get_dz_day"""
    await update.message.reply_text('''введите пожалуйста дату в формате dd-mm-yyyy''')
    text = update.message.text
    not_done = "не сделано"
    result = cur.execute(f"""SELECT subgect_id, text FROM dz
                    WHERE date={text} and state={not_done} and user_id=(SELECT id FROM users WHERE user={username})""").fetchall()
    for i in range(len(result)):
        date = cur.execute(f"""SELECT subgect FROM subgects
                    WHERE id={result[0]} and user_id=(SELECT id FROM users WHERE user={username})""").fetchall()
        result[i] = [date, result[i][1]]
    result = [' '.join(list(i)) for i in result]

    await update.message.reply_text('\n'.join(result), reply_markup=markup)




async def get_dz_week(update, context):
    """Отправляет дз на неделю когда получена команда /get_dz_week"""
    newdate = datetime.now()
    newdate = newdate.strptime("%d.%m.%Y")
    date_dz = {}
    not_done = "не сделано"
    for i in range(7):
        dz = cur.execute(f"""SELECT subgect, text FROM dz
                            WHERE date={newdate} and state={not_done} and user_id=(SELECT id FROM users WHERE user={username})""").fetchall()
        for i in range(len(dz)):
            date = cur.execute(f"""SELECT subgect FROM subgects
                        WHERE id={dz[0]} and user_id=(SELECT id FROM users WHERE user={username})""").fetchall()
            dz[i] = [date, dz[i][1]]
        date_dz[newdate] = '\n'.join([': '.join(list(i)) for i in dz])
    res = '\n...\n'.join(['\n'.join([i, date_dz[i]])for i in date_dz.keys()])
    await update.message.reply_text(res, reply_markup=markup)



async def add_dz(update, context):
    """Заносит новое дз в бд когда получена команда /add_dz"""
    await update.message.reply_text('')
    date = update.message.text
    await update.message.reply_text('')
    subject = update.message.text
    await update.message.reply_text('')
    text = update.message.text

    user_id = cur.execute(f"""SELECT id FROM users WHERE user={username}""").fetchall()
    not_done = "не сделано"

    cur.execute(f"""INSERT INTO dz(user_id, subgect_id, date, text, state) VALUES({user_id}, {subject}, {date}, {text}, {not_done})""")
    await update.message.reply_text('', reply_markup=markup)



async def check_done(update, context):
    """Отмечает выполненное дз когда получена команда /check_done"""
    await update.message.reply_text('введите пожалуйста дату в формате dd-mm-yyyy')
    date = update.message.text
    await update.message.reply_text('выберите нужный предмет из списка и введите только его номер')
    subject = update.message.text
    await update.message.reply_text('введите текст задания')
    # можно предложить список на выбор текстов задани чтобы исключить ошибки и неточности
    text = update.message.text
    done = "сделано"
    cur.execute(f"""UPDATE dz SET state={done} WHERE date={date} and subject_id={subject} and twxt={text}""").fetchall()
    await update.message.reply_text('', reply_markup=markup)

async def help(update, context):
    """Отправляет сообщение когда получена команда /help"""
    await update.message.reply_text('''/stop – прервать диалог.
/add_dz – добавить домашнее задание.
/check_done – отметить выполненное домашнее задание.
/get_dz_day – показать домашнее задание на определённую дату.
/get_dz_subgect – показать домашнее задание по определённому предмету.
/get_dz_week – показать домашнее задание на неделю.
/help – показать список всех функций.
''', reply_markup=markup)


async def stop(update, context):
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


def main():
    application = Application.builder().token("5946162651:AAECc0zeiX_7CYpzer6ZPEK7kZZOt62rIIE").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("add_dz", add_dz))
    application.add_handler(CommandHandler("get_dz_week", get_dz_week))
    application.add_handler(CommandHandler("get_dz_day", get_dz_day))
    application.add_handler(CommandHandler("get_dz_subject", get_dz_subject))
    application.add_handler(CommandHandler("check_done", check_done))

    application.run_polling()


if __name__ == "__main__":
    reply_keyboard = [['/help', '/stop'],
                      ['/add_dz', '/check_done'],
                      ['/get_dz_day', '/get_dz_subject'],
                      ['/get_dz_week']]

    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    username = ''

    con = sqlite3.connect("bot_db.sqlite")
    cur = con.cursor()

    main()
