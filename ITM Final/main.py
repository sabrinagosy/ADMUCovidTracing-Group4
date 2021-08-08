import telebot
import time
import requests
import json
import pandas as pd
import numpy as np
import re
import yagmail
import schedule
import threading

#The telebot name is @ADMUCovidBot.
#/start to see the list of commands

bot_token='1936282467:AAGM5X1pR7XzhYa-xD2Q5Dx9GK3ViqIshwI'
bot = telebot.TeleBot(bot_token)

#start
@bot.message_handler(commands=['start'])
def send_command(message):
    bot.send_message(message.chat.id,"Use any of the commands to get started:\n/ihavesymptoms: When you are experiencing common symptoms\n/symptoms: Shows a list of symptoms of covid\n/contacts: Shows a list of important contact information\n/class_status: Shows a status update of whether or not your classes have a report of COVID\n/statusupdate: Shows the current COVID data of the country\n/class_status: Shows a status update of whether or not a class had a report of covid\n/keepsafe: Ways to keep  safe")

#SOMEONE HAS SYMPTOMS//IHAVESYMPTOMS COMMAND
#bot will ask for your id number
@bot.message_handler(commands=['ihavesymptoms'])
def with_covid(message):
    bot.send_message(message.chat.id,'What is your ID number?\nReply with the format: "cov-id [ID Number]"\n\nExample reply:   cov-id 123456')

#data frome for sample student data
studentdata_df=pd.read_csv('Sample_Student_Data.csv')
#data frame for covid tracker
df_covid = pd.read_csv("covid_track.csv")
df_covid = df_covid.set_index('id_number')


#function to get dataframe of all classmates of covid student(reported w/ symptoms, meaning ran the /ihavesymptoms command)
def classmate_emails(cov_id):

    df = pd.read_csv("Sample_Student_Data.csv")
    df = df.set_index("id_number")
    classes_list = df.loc[int(cov_id), "classes"].split(",")

    df['classmates'] = df.apply(lambda row: True if any([item in row['classes'] for item in classes_list]) else False, axis = 1)
    df['classmates'] = df['classmates']*df['obf_email']
    df = df.replace(r'', np.nan, regex=True)
    df = df.dropna()
    df = df[["name","obf_email"]]

    filename = f"{cov_id}_classmates_list.csv"
    df.to_csv(filename) #writes a separate csv with all the classmates of the covid person

    df_covid.loc[int(cov_id),'covid'] = 'yes'#changes status of covid person to yes in covid tracker

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
        /class_status - Shows a status update of whether or not your classes had a report of covid for that week
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
    if int(message_words[1]) in list(studentdata_df['id_number']): #checks if id number is valid
        bot.send_message(message.chat.id,"Thank you for informing us! For everyone's safety, we will be informing all your classmates of your current condition. Rest assured we will not disclose your identity. Please contact healthservices.ls@ateneo.edu or visit https://bit.ly/LS-OHS if you wish for medical advisment and assistance.")
        classmate_emails(cov_student) #calling the function that creates the dataframe of classmates
        send_email(cov_student) #calling the function that sends out mail merge
    #entered invalid id
    else:
        bot.send_message(message.chat.id, "You have entered an invalid ID. Please try again.")

#SYMPTOMS COMMAND
@bot.message_handler(commands=['symptoms'])
def symptoms_info(message):
    bot.send_message(message.chat.id,'''Common symptoms:
- Fever
- Dry cough
- Fatigue
- Less common symptoms:
- Loss of taste or smell,
- Nasal congestion,
- Conjunctivitis (also known as red eyes)
- Sore throat,
- Headache,
- Muscle or joint pain,
- Different types of skin rash,
- Nausea or vomiting,
- Diarrhea,
- Chills or dizziness.
- Symptoms of severe cases:
- Shortness of breath,
- Loss of appetite,
- Confusion,
- Persistent pain or pressure in the chest,
- High temperature (above 38 °C).''')

#CONTACTS COMMAND
@bot.message_handler(commands=['contacts'])
def contacts_info(message):
    bot.send_message(message.chat.id,'''DOH COVID-19 emergency hotlines:
02-894-COVID (02-894-26843)
1555

ATENEO CONTACTS:
Ateneo LS Health Services
- email: healthservices.ls@ateneo.edu
- facebook: @admuLSHS
- contact no: 4266001 loc.5110/0918 9445997
- website: bit.ly/LS-OHS
Office of the University Physician
- email: univphysician@ateneo.edu

''')

#CLASS_STATUS COMMAND
#bot will ask for your id number
@bot.message_handler(commands=['class_status'])
def class_status(message):
    bot.send_message(message.chat.id,'To check your classes, we need your ID Number\nReply with the format: "istherecov-id [ID Number]"\n\nExample reply:   istherecov-id 123456')

def class_question(message):
    message_words=message.text.split()
    if len(message_words)==2 and message_words[0].lower()=='istherecov-id' and message_words[1].isdigit():
        return True
    else:
        return False
@bot.message_handler(func=class_question)
def class_answer(message):
    message_words=message.text.split()
    id_number=message_words[1]
    if int(message_words[1]) in list(studentdata_df['id_number']):
        classes_list = df_covid.loc[int(id_number), "classes"].split(",")
        df_covid['classmates'] = df_covid.apply(lambda row: 'True' if any([item in row['classes'] for item in classes_list]) else 'False', axis = 1)
        if df_covid[df_covid['classmates'].str.contains('True') & df_covid['covid'].str.contains('yes')].empty:
            bot.send_message(message.chat.id,'There is no case of COVID in your classes.')
        else:
            bot.send_message(message.chat.id,'There is a case of COVID in your classes.')
    else:
        bot.send_message(message.chat.id,'You have entered an invalid ID. Please try again.')


#code that clears covid tracker every monday 8am (supposedly start of another school week)
def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(5)
def clear_covid():
    df_covid['covid'] = df_covid['covid'].replace(['yes'],'no')
if __name__ == "__main__":
    schedule.every().monday.at('08:00').do(clear_covid)
    # thread to run the schedule check while not blocking bot.
    threading.Thread(target=schedule_checker).start()



#STATUSUPDATE COMMAND
@bot.message_handler(commands=['statusupdate'])
def ph_status(message):
    r=requests.get("https://api.apify.com/v2/key-value-stores/lFItbkoNDXKeSWBBA/records/LATEST?disableRedirect=true")
    data_dict=eval(r.text)
    data_text=f'''COVID Data updated as of {data_dict['lastUpdatedAtApify'][0:10]}
Infected: {data_dict['infected']}
Tested: {data_dict['tested']}
Recovered: {data_dict['recovered']}
Deceased: {data_dict['deceased']}
Active Cases: {data_dict['activeCases']}

Data from https://ncovtracker.doh.gov.ph/'''
    bot.send_message(message.chat.id,data_text)


#KEEPSAFE COMMAND
@bot.message_handler(commands=['keepsafe'])
def keep_safe(message):
    bot.send_message(message.chat.id,'''Ways to keep safe:
-Get vaccinated
-Practice social distancing
-Wear masks as much as possible
-Avoid crowds and large gatherings
-Keep rooms well ventilated
For more comprehensive advice visit:
https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public''')


#to make sure the bot runs forever when executed in the command line
bot.polling()
