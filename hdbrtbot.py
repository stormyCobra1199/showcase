import pandas as pd
import datetime
import logging
import requests
import json
import re
import os
import telegram
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from tabulate import tabulate
from pandas.plotting import table 

PORT = int(os.environ.get('PORT', 5000))
TOKEN = os.environ["TOKEN"]
GTOKEN = os.environ["GTOKEN"]
GID = os.environ["GID"]

def get_url():
    contents = requests.get('https://dog.ceo/api/breeds/image/random').json()
    url = contents['message']
    return url

def get_image_url():
    allowed_extension = ['jpg', 'jpeg', 'png']
    file_extension = ''
    while file_extension not in allowed_extension:
        url = get_url()
        file_extension = re.search("([^.]*)$", url).group(1).lower()
    return url

def bop(update, context):
    url = get_image_url()
    chat_id = update.message.chat.id
    context.bot.send_photo(chat_id=chat_id, photo=url)


###
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="HDBRT Bot - Get latest HDB Resale Transactions.\nExamples: /hs 5 Bedok for 5Rm in Bedok or /hs French for all French Road.")
   
def hs(update, context):
    q=' '.join(context.args)
    if q[0] in ["2","3","4","5"]:
        url = "https://data.gov.sg/api/action/datastore_search?resource_id=f1765b54-a209-4718-8d38-a39237f502b3&fields=month,block,street_name,flat_type,flat_model,resale_price,floor_area_sqm,lease_commence_date,storey_range&sort=month%20desc&limit=20&filters={\"flat_type\":\""+q[0]+" ROOM"+"\",\"town\":\""+q[2:].upper()+"\"}"
        #context.bot.send_message(chat_id=update.effective_chat.id, text=url)
    else:
        url = "https://data.gov.sg/api/action/datastore_search?resource_id=f1765b54-a209-4718-8d38-a39237f502b3&fields=month,block,street_name,flat_type,flat_model,resale_price,floor_area_sqm,lease_commence_date,storey_range&sort=month%20desc&limit=20&q="+q
    response=requests.get(url)
    dataset=response.json()
    df = pd.json_normalize(dataset['result'], "records")  
    df = df.sort_values(by='block').set_index('block').reindex(columns=['street_name','flat_type','flat_model','resale_price','floor_area_sqm','lease_commence_date','storey_range','month'])
    df.rename(columns={'street_name': 'street', 'flat_type': 'type', 'resale_price': 'price', 'lease_commence_date': 'built', 'storey_range': 'floor', 'floor_area_sqm': 'sqm', 'flat_model': 'model', 'month': 'sold'}, inplace=True)
    df.replace(['2 ROOM', '3 ROOM', '4 ROOM', '5 ROOM', 'New Generation', 'Standard', 'EXECUTIVE', 'Maisonette', 'Simplified', 'Improved'],['2','3','4','5','NG','Std','E','M','S','I'], inplace=True) 
    df['type']=df['type']+df['model']
    df.drop('model', axis=1, inplace=True)
    dft=tabulate(df, headers='keys', tablefmt='plain', numalign='left')
    context.bot.send_message(chat_id=update.effective_chat.id, text=dft)
    ## copy query to gist
    query_url = "https://api.github.com/gists/"+GID+"/comments"
    data = {"body": q}
    headers = {'Authorization': f'token {GTOKEN}'}
    r = requests.post(query_url, headers=headers, data=json.dumps(data))

def errorhand(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter a valid town or search term. Eg: /hs 5 Bedok for 5Rm in Bedok or /hs French for all French Road.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('bop', bop))
    dp.add_handler(CommandHandler('hs', hs))
    dp.add_error_handler(errorhand)
    ##
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://doggodemo.herokuapp.com/' + TOKEN)
    
    updater.idle()


if __name__ == '__main__':
    main()
