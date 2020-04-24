import tensorflow as tf 
import ktrain
import pandas as pd 
import numpy as np 
import praw
import unicodedata
import re

def unicodeToAscii(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
def normalizeString(s):
    if not isinstance(s, float):
      s = unicodeToAscii(s.lower().strip())
      s = re.sub(r"([.!?])", r" \1", s)
      s = re.sub(r"[^a-zA-Z.!?]+", r" ", s)
    return s

flairs = ["Scheduled", "Politics", "Photography", "Policy/Economy", "AskIndia", "Sports", "Non-Political", "Science/Technology", "Food", "Business/Finance", "Coronavirus", "CAA-NRC-NPR"]

predictor = ktrain.load_predictor('Predictor')

def predict_flair(url):
    #--------------------------------------------------------------------------------------------------------
    # Reddit Credentials Below for Web Scraping using praw
    reddit = praw.Reddit(client_id='EPeQ4_tZaSnieQ', client_secret="o8wiYMDri2RMiF1um14L1rGHXEs", user_agent='Reddit WebScraping')
    #--------------------------------------------------------------------------------------------------------
    s = reddit.submission(url=url)
    Data = pd.DataFrame
    Data['title'] = [s.title]
    Data['body'] = [s.selftext]
    Data['Text'] = Data['title'] + ' ' + Data['body']
    Data['Text'] = Data['Text'].apply(lambda x: normalizeString(x))
    return predictor.predict(Data['Text'])