from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext
)
import os
from typing import Final
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
BOT_USERNAME: Final = os.getenv('Bot')
my_chat_id = os.getenv('my_chat_id')

DB_CONFIG = {
    'dbname': os.getenv('PG_DBNAME'),
    'user': os.getenv('PG_USER'),
    'password': os.getenv('PG_PASSWORD'),
    'host': os.getenv('PG_HOST'),
    'port': os.getenv('PG_PORT')
}
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Only reply to messages from my chat_id
def reply_to_me_only(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id == my_chat_id:
        update.message.reply_text(update.message.text)    

# Time variables
now = datetime.now()
year = now.strftime("%Y")
month = now.strftime("%m")
week = now.strftime("%V")
day = now.strftime("%d")
hour = now.strftime("%H")
minute = now.strftime("%M")
yearmonth = now.strftime("%Y%m")
yearweek = now.strftime("%Y%V")
if month in ['01', '02', '03']:
    quarter = 1
elif month in ['04', '05', '06']:
    quarter = 2
elif month in ['07', '08', '09']:
    quarter = 3
else:
    quarter = 4
all_values = (yearmonth, yearweek, year, quarter, month, week, day, hour, minute)  

# Database gestion
def create_table_if_not_exists(table_name, data=None):
    if data is None:
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, yearmonth INT, yearweek INT, year SMALLINT, quarter SMALLINT, month SMALLINT, week SMALLINT, day SMALLINT, hour SMALLINT, minute SMALLINT)"
        print('data is None')
    else:
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, yearmonth INT, yearweek INT, year SMALLINT, quarter SMALLINT, month SMALLINT, week SMALLINT, day SMALLINT, hour SMALLINT, minute SMALLINT, {data})"
        print('Data is')
    cursor.execute(create_table_query)
    conn.commit()
def insert_data(table_name, data=None):
    if data is None:
        data = all_values
        print('insert_data is none')
    if not isinstance(data, tuple): #convert to a tuple if it's not already
        data = (data,)
        data = all_values + data #all_values and data are compatible as they're both tuples
        print(data)
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'") #query to check number of columns
    columns = [row[0] for row in cursor.fetchall() if row[0] != 'id'] #select all columns except the "id" one
    print(columns)
    placeholders = ', '.join(['%s'] * len(columns)) #create placeholders for all columns except "id"
    insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    print('this is' + insert_query)
    cursor.execute(insert_query, data) 
    conn.commit()


WAKE_UP, ASLEEP_TIME, LATE_REASONS, SLEEP_LATE = range(4)


async def awake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Natural","Bothered","Alarm"]]
    create_table_if_not_exists("awake")
    insert_data("awake")
    await update.message.reply_text(
        "Hello Sunshine\n\n"
        "Send /cancel to stop talking to me.\n\n"
        "Did you wake up by yourself ?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )
    return WAKE_UP

async def asleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.text
    create_table_if_not_exists("way_i_woke_up","type TEXT")
    if user == "Natural" or user == "Bothered" or user == "Alarm":
        insert_data("way_i_woke_up",(user))
        await update.message.reply_text(
        "When did you fall asleep ?",
        reply_markup=ReplyKeyboardRemove())
        return ASLEEP_TIME
    
    await update.message.reply_text("Unknown answer, try again babe")
    return WAKE_UP

async def sleep_late(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("inside sleep_late function")
    user_hour = int(update.message.text)
    answers = {5:"✨",4:"🌿",3:"🐼",2:"👹",1:"⚰️"}
    reply_keyboard = [*[answers.values()]]
    reply_keyboard = [[str(value) for value in answers.values()]]
    context.user_data['answers'] = answers

    create_table_if_not_exists("asleep_time","time TEXT, reason TEXT")
    print("we're here")
    if user_hour>24:
        print("wrong answer")
        await update.message.reply_text("Invalid answer, try again babe")
        return ASLEEP_TIME
    if user_hour not in [20,21,22,23]:
        context.user_data['user_hour'] = user_hour
        await update.message.reply_text("Why ?")
        return LATE_REASONS
    else:
        # user_hour = (user_hour, None)
        # print(user_hour)
        insert_data("asleep_time",(user_hour))
        await update.message.reply_text("Beauty sleep yay.")
        await update.message.reply_text("What's your energy level this morning ?", reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True
        ))

        return SLEEP_LATE
    
async def late_sleep_reasons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = {5:"✨",4:"🌿",3:"🐼",2:"👹",1:"⚰️"}
    reply_keyboard = [*[answers.values()]]
    reply_keyboard = [[str(value) for value in answers.values()]]
    context.user_data['answers'] = answers
    user_hour = context.user_data['user_hour']
    user = update.message.text
    await update.message.reply_text("Noted !")
    await update.message.reply_text("What's your energy level this morning ?", reply_markup=ReplyKeyboardMarkup(
    reply_keyboard, one_time_keyboard=True
    ))
    insert_data("asleep_time",(user_hour, user))
    return SLEEP_LATE


async def energy_levels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    create_table_if_not_exists("energy_levels","level INT")
    answers = context.user_data['answers']
    user = update.message.text
    for key, value in answers.items():
        if user == value:
            level = key
    insert_data("energy_levels",(level))
    await update.message.reply_text(
        "Okay baby, see you later and have a great day !"
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.text
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("awake", awake)],
        states={
            WAKE_UP: [MessageHandler(filters.Regex("^(Natural|Bothered|Alarm)$"), asleep_time)],
            ASLEEP_TIME: [MessageHandler(filters.Regex("^([0-9]|1[0-9]|2[0-4])$"), sleep_late)],
            LATE_REASONS: [MessageHandler(filters.TEXT, late_sleep_reasons)],
            SLEEP_LATE: [
                MessageHandler(filters.Regex("^(✨|🌿|🐼|👹|⚰️)$"), energy_levels)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()