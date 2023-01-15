from registration import CourseDataExtractor
from data import auth, AddCourse, DropCourse, CourseDataRetriever, CourseSeatUpdater
import logging
import time
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ChatAction, ForceReply
from telegram.ext import Updater, MessageHandler,  ConversationHandler, Filters
from telegram.ext import CommandHandler, ContextTypes, CallbackContext
from queue import Queue
from threading import Thread
from flask import Flask
import os

## Logging Configuration
logging.basicConfig(
    format="%(message)s,%(asctime)s", level=logging.ERROR, filename="log.csv", encoding="utf-8"
)

telegram_bot_token = os.environ.get('telegram-token')

app = Flask(__name__)

SERVICE, ADD_SEMESTER, ADD_YEAR, ADD_CRN, CONFIRM_ADD_SELECTION, DROP_COURSES, CONFIRM_DROP_COURSE =range(7)

def start(update: Update, context) -> int:
    global chat_id
    chat_id = update.message.chat.id
    reply_keyboard = [["Add Course(s)"],["Drop Course(s)"]]
    msg = """Aloha!
Welcome to Regnify AUC Bot, your gateway to course notification.
Please select your service from the list.

*Note: The bot only notifies for changes in courses' capacity. It does not register the course. Select /help to know more"""
    update.message.reply_chat_action(action = ChatAction.TYPING)
    time.sleep(1)
    update.message.reply_text(msg,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Add or Drop Courses"
        ),
    )
    return SERVICE

def service(update: Update, context) -> int:
    service_choice = update.message.text
    if service_choice == "Add Course(s)":
        msg = "Please select the semester from the list."
        reply_keyboard = [["Fall"], ["Summer"], ["Spring"], ["Winter"]]
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="Semester"
            ),
        )           
        return ADD_SEMESTER
    elif service_choice == "Drop Course(s)":
        global DropIndex
        global drop_keyboard
        global drop_options

        PrevCRN, DropIndex = CourseDataRetriever(chat_id=chat_id)
        msg = "Please select the course you wish to drop. If you want to drop all, select Drop All"
        drop_keyboard = []
        drop_options = []
        drop_keyboard.append(["Drop All"])
        for n in range(len(PrevCRN)):
            drop_keyboard.append([f"{n + 1}. {PrevCRN[n][2]} ({PrevCRN[n][6]}) - Section {PrevCRN[n][5]}"])
            drop_options.append(f"{n + 1}. {PrevCRN[n][2]} ({PrevCRN[n][6]}) - Section {PrevCRN[n][5]}")
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg,
            reply_markup=ReplyKeyboardMarkup(
                drop_keyboard, one_time_keyboard=True, input_field_placeholder="Course To Be Dropped"
            ),
        )           

        return DROP_COURSES 
    else:
        
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        msg = "Please choose from the below list."
        reply_keyboard = [["Add Course(s)"],["Drop Course(s)"]]
        update.message.reply_text(msg,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="Add Or Drop Courses"
            ),
        )
        return SERVICE

def add_semester(update: Update, context) -> int:
    global semester
    semester = update.message.text
    if semester in "Fall" or semester in "Summer" or semester in "Winter" or semester in "Spring":
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        msg = """Please enter the year of the course.
Note that Spring courses are in the following year."""
        update.message.reply_text(msg)
        return ADD_YEAR
    else:
        msg = "Please select the semester from the list."
        reply_keyboard = [["Fall"], ["Summer"], ["Spring"], ["Winter"]]
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="Semester"
            ),
        )           
        return ADD_SEMESTER

def add_year(update: Update, context) -> int:
    global year
    try:
        year = int(update.message.text)
        if year > 2099 or year < 2023:
            update.message.reply_chat_action(action = ChatAction.TYPING)
            time.sleep(1)
            msg = """Please enter the year of the course.
    Note that Spring courses are in the following year."""
            update.message.reply_text(msg)
            return ADD_YEAR
        else:
            msg = "Please enter the CRNs of the courses separated by a comma. For ex: 357462,69451,54524"
            update.message.reply_chat_action(action = ChatAction.TYPING)
            time.sleep(1)
            update.message.reply_text(msg)
            return ADD_CRN
    except:
        msg = "Please enter the CRNs of the courses separated by a comma. For ex: 357462,69451,54524"
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg)
        return ADD_CRN


def add_crn(update: Update, context) -> int:
    global CourseInfo
    crns = update.message.text
    CourseInfo, Seats, Waitlist = CourseDataExtractor(crns= crns, Semester=semester,Year=year)
    if "error1515" not in Seats:
        for m in range(len(CourseInfo)):
            msg = f""" Course NO. {m+ 1}:
Course Name: {CourseInfo[m][0]}
Course ID: {CourseInfo[m][2]}
Section: {CourseInfo[m][3]}
CRN: {CourseInfo[m][1]}

Total Seats: {Seats[m]["Total"]}
Remaining Seats: {Seats[m]["Remaining"]}

Remaining Waitlist Seats: {Waitlist[m]["Remaining"]}"""
            update.message.reply_text(msg)
            update.message.reply_chat_action(action = ChatAction.TYPING)
            time.sleep(0.5)
        msg = """Check the courses.
Are these the ones wanted? Please Select"""
        reply_keyboard = [["Yes"], ["No"]]
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="Yes/No"
            ),
        )           
        return CONFIRM_ADD_SELECTION
    
    else:
        i = Seats.index("error1515")
        msg = f"""The following CRN is incorrect: {CourseInfo[i]}. Please enter all the CRNS again. 
If the issue is persistent, ensure that you selected the correct semester and year."""
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg)
        return ADD_CRN

def confirm_add_selection(update: Update, context) -> int:
    answer = update.message.text
    if answer in "Yes":
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(0.5)
        stat = AddCourse(chat_id= chat_id, Course_Info= CourseInfo, Semester= semester, Year= year)
        if stat == "Success":

            msg = """Thank you for using Regnify Bot. Your registration is completed successfully.
You will be notified once a change happens in the course seating.
If you wish to drop your courses or add additional courses; select /start """
            update.message.reply_text(msg)

            return ConversationHandler.END
        else:
            
            msg = """Sorry. I faced an internal error. Please Try again later.
If you wish to drop your courses or add additional courses; select /start """
            update.message.reply_text(msg)

            return ConversationHandler.END
        
    else:
        msg = "Please enter the CRNs of the courses separated by a comma. For ex: 357462,69451,54524"
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg)
        return ADD_CRN

def drop_courses(update: Update, context) -> int:
    global dropped_course
    dropped_course = update.message.text
    if dropped_course == "Drop All":
        msg = f"Are you sure you want to drop all registered courses?"
        reply_keyboard = [["Yes"], ["No"]]
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="Yes/No"
            ),)
        return CONFIRM_DROP_COURSE

    elif dropped_course in drop_options:
        msg = f"Are you sure you want to drop {dropped_course[2:]}"
        reply_keyboard = [["Yes"], ["No"]]
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="Yes/No"
            ),)
        return CONFIRM_DROP_COURSE
    else:
        msg = "Please select the course you wish to drop. If you want to drop all, select Drop All"
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg,
            reply_markup=ReplyKeyboardMarkup(
                drop_keyboard, one_time_keyboard=True, input_field_placeholder="Course To Be Dropped"
            ),
        )           

        return DROP_COURSES
        
def confirm_drop_course(update: Update, context) -> int:
    global dropped_course
    answer = update.message.text
    if answer in "Yes":
        if dropped_course == "Drop All":
            DropCourse(chat_id= chat_id, index= DropIndex, all= "yes")
            msg = f"""All your courses are dropped. I hope that you have the registered all of them.
See you soon. You could press /start to register new courses or drop the ones you added."""
            update.message.reply_chat_action(action = ChatAction.TYPING)
            time.sleep(0.5)
            update.message.reply_text(msg)
            return ConversationHandler.END
        else:
            dropped_course = dropped_course.split(". ")
            DropCourse(chat_id= chat_id, index= DropIndex[int(dropped_course[0])-1], all= "no")
            msg = f"""The course {dropped_course[1]} is finally dropped. I hope that you have the registered the course.
See you soon. You could press /start to register new courses or drop the ones you added."""
            update.message.reply_chat_action(action = ChatAction.TYPING)
            time.sleep(0.5)
            update.message.reply_text(msg)
            return ConversationHandler.END
    else:
        msg = "Please select the course you wish to drop. If you want to drop all, select Drop All"
        update.message.reply_chat_action(action = ChatAction.TYPING)
        time.sleep(1)
        update.message.reply_text(msg,
            reply_markup=ReplyKeyboardMarkup(
                drop_keyboard, one_time_keyboard=True, input_field_placeholder="Course To Be Dropped"
            ),
        )           

        return DROP_COURSES

def notifier(context: CallbackContext):
    AllCrns, indexes = CourseSeatUpdater()
    for index in indexes:
        chat_ids = AllCrns[index][4].split(",")
        for chat_id in chat_ids:
            if int(AllCrns[index][3]) == 0:
                msg = f""" Unfortunately there are no seats remaining in the course {AllCrns[index][5]} ({AllCrns[index][7]}) with section number {AllCrns[index][6]}. However, there is still hope do not worry."""
            else:
                msg = f""" {AllCrns[index][3]} Seats are now available in the course {AllCrns[index][5]} ({AllCrns[index][7]}) with section number {AllCrns[index][6]}. Hurry up to reserve the course."""

        context.bot.send_message(chat_id=chat_id, 
                             text=msg)



def end(update: Update, context) -> int:
    msg = """Thank You. I hope I successfully performed your requests.
You could press /start to register new courses or drop the ones you added."""
    update.message.reply_chat_action(action = ChatAction.TYPING)
    time.sleep(1)
    update.message.reply_text(msg)
    return ConversationHandler.END


@app.route("/")
def main(webhook_url=None):
    auth()

    if webhook_url:
        bot = Bot(telegram_bot_token)
        update_queue = Queue()
        dp = Dispatcher(bot, update_queue)        

    else:
        updater = Updater(telegram_bot_token, use_context= True)
        j = updater.job_queue
        bot = updater.bot
        dp = updater.dispatcher
        # job_minute = j.run_repeating(notifier, interval=1800, first=10)
        # job_minute.enabled = True

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={

                SERVICE: [MessageHandler(Filters.text & (~Filters.command), service)],
                ADD_SEMESTER: [MessageHandler(Filters.text & (~Filters.command), add_semester)], 
                ADD_YEAR: [MessageHandler(Filters.text & (~Filters.command), add_year)], 
                ADD_CRN: [MessageHandler(Filters.text & (~Filters.command), add_crn)], 
                CONFIRM_ADD_SELECTION: [MessageHandler(Filters.text & (~Filters.command), confirm_add_selection)],
                DROP_COURSES: [MessageHandler(Filters.text & (~Filters.command), drop_courses)],
                CONFIRM_DROP_COURSE: [MessageHandler(Filters.text & (~Filters.command), confirm_drop_course)],
                
            }, 
            fallbacks=[CommandHandler("end", end),CommandHandler("help", help),  CommandHandler("start", start)],conversation_timeout= 18000
        
        )

        dp.add_handler(conv_handler)

    if webhook_url:
        bot.set_webhook(webhook_url=webhook_url)
        thread = Thread(target=dp.start, name='dispatcher')
        thread.start()
        return update_queue, bot
    else:
        bot.set_webhook()  # Delete webhook
        updater.start_polling()
        updater.idle()


if __name__ == "__main__":
    main()