import telebot
import time
import requests
import json
import pandas as pd
import numpy as np
import re
import yagmail


bot_token='1936282467:AAGM5X1pR7XzhYa-xD2Q5Dx9GK3ViqIshwI'
bot = telebot.TeleBot(bot_token)

#start
@bot.message_handler(commands=['start'])
def send_command(message):
    bot.send_message(message.chat.id,"Use any of the commands to get started:\n/ihavesymptoms: When you are experiencing common symptoms\n/symptoms: Shows a list of symptoms of covid\n/contacts: Shows a list of important contact information\n/class_status: Shows a status update of whether or not a class had a report of covid\n/statusupdate: Shows the current COVID data of the country\n/class_status: Shows a status update of whether or not a class had a report of covid\n/keepsafe: Ways to keep  safe")

#SOMEONE HAS SYMPTOMS//IHAVESYMPTOMS COMMAND
#bot will ask for your id number
@bot.message_handler(commands=['ihavesymptoms'])
def with_covid(message):
    bot.send_message(message.chat.id,'What is your ID number?\nReply with the format: "cov-id [ID Number]"\n\nExample reply:   cov-id 123456')

#sample student data
studentdata_df=pd.read_csv('Sample_Student_Data.csv')

#function to get dataframe of all classmates of covid student
def classmate_emails(cov_id):

    df = pd.read_csv("sample_student_data.csv")
    df = df.set_index("id_number")
    classes_list = df.loc[int(cov_id), "classes"].split(",")

    df['classmates'] = df.apply(lambda row: True if any([item in row['classes'] for item in classes_list]) else False, axis = 1)
    df['classmates'] = df['classmates']*df['obf_email']
    df = df.replace(r'', np.nan, regex=True)
    df = df.dropna()
    df = df[["name","obf_email"]]

    filename = f"{cov_id}_classmates_list.csv"
    df.to_csv(filename)


#function to mailmerge(send out emails to all classmates)
def message(row):
    time_now=time.strftime("%B %d, %Y %I:%M %p", time.localtime())
    return f"""
    Dear {row.name},

    As of {time_now}, one of your classmates has notified us that they have been experiencing symptoms of COVID-19. If you are experiencing any symptoms, please let us know immediately through our Telegram bot (@ADMUCovidBot). You may also contact the bot to for other pertinent information.

    ADMUCovidBot accepts the following commands:
        /ihavesymptoms - When you are experiencing common symptoms
        /symptoms - Shows a list of symptoms of covid
        /contacts - Shows a list of important contact information
        /class_status - Shows a status update of whether or not a class had a report of covid
        /statusupdate - Shows the current COVID data of the country
        /keepsafe - Ways to keep safe from the COVID virus


    In service,
    ADMU COVID-19 Contact Tracing Team
    [{time_now}]
    """

def send_email(cov_id):
    yag = yagmail.SMTP(user='admucontacttracing@gmail.com',password='ADMUCT2021')
    recipient_details = pd.read_csv(f"{cov_id}_classmates_list.csv")

    for row in recipient_details.itertuples():
        yag.send(to=row.obf_email,
                 subject="ADMU Contact Tracing",
                 contents = message(row))

#bot function that gets the id number of covid student and sends out email if id is valid
def covid_request(message):
    message_words=message.text.split()
    if len(message_words)==2 and message_words[0].lower()=='cov-id' and message_words[1].isdigit():
        return True
    else:
        return False

@bot.message_handler(func=covid_request)
def covid_getter(message):
    message_words=message.text.split()
    cov_student=message_words[1]
    if int(message_words[1]) in list(studentdata_df['id_number']):
        bot.send_message(message.chat.id,"Thank you for informing us! For everyone's safety, we will be informing all your classmates of your current condition. Rest assured we will not disclose your identity. Please contact healthservices.ls@ateneo.edu or visit https://bit.ly/LS-OHS if you wish for medical advisment and assistance.")
        classmate_emails(cov_student)
        send_email(cov_student)
    else:
        bot.send_message(message.chat.id, "You have entered an invalid ID. Please try again.")



#STATUSUPDATE COMMAND
@bot.message_handler(commands=['statusupdate'])
def ph_status(message):
    r=requests.get("https://api.apify.com/v2/key-value-stores/lFItbkoNDXKeSWBBA/records/LATEST?disableRedirect=true")
    data_dict=eval(r.text)
    data_text=f'''Infected: {data_dict['infected']}
Tested: {data_dict['tested']}
Recovered: {data_dict['recovered']}
Deceased: {data_dict['deceased']}
Active Cases: {data_dict['activeCases']}
Data updated as of {data_dict['lastUpdatedAtApify'][0:10]}
Data from https://ncovtracker.doh.gov.ph/'''
    bot.send_message(message.chat.id,data_text)

#to make sure the bot runs forever
while True:
    try:
        bot.polling()
    except:
        time.sleep(15)
