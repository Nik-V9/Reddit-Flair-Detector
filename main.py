from flask import Flask, request, jsonify, make_response
from flask import render_template, url_for, flash, redirect
from forms import FlairForm
from flask_restful import reqparse, abort, Api, Resource
from werkzeug.datastructures import FileStorage
import tensorflow as tf
import ktrain
import pandas as pd 
import numpy as np 
import praw
import unicodedata
import re
import json
import argparse

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba049'
api = Api(app)

Train_data = pd.read_csv('static/data/Train_Data.csv')

flairs = list(set(Train_data['flair']))

x_train = Train_data['Text']
y_train = Train_data['flair']

from ktrain import text
MODEL_NAME = 'xlnet-base-cased'
t = text.Transformer(MODEL_NAME, maxlen=500, class_names=flairs)
train = t.preprocess_train(x_train, y_train)
model = t.get_classifier()
learner = ktrain.get_learner(model, train_data=train, batch_size=6)

learner.load_model('static/Models/model_XLNet', preproc=t)

predictor = ktrain.get_predictor(learner.model, preproc=t)
# Reddit Credentials Below for Web Scraping using praw
reddit = praw.Reddit(client_id='EPeQ4_tZaSnieQ', client_secret="o8wiYMDri2RMiF1um14L1rGHXEs", user_agent='Reddit WebScraping')

post = []

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

def predict_flair(url):
    s = reddit.submission(url=url)
    Data = {"title":[], "body":[]}
    Data['title'].append(s.title)
    Data['body'].append(s.selftext)
    Data = pd.DataFrame(Data)
    Data['Text'] = Data['title'] + ' ' + Data['body']
    Data['Text'] = Data['Text'].apply(lambda x: normalizeString(x))
    data= Data['Text'].values.tolist()
    return predictor.predict(data)

@app.route("/",methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    global post
    form = FlairForm()
    if form.validate_on_submit():
        if request.method == 'POST':
            flair = predict_flair(form.URL.data)
            pred = {"flair":[], "URL":[]}
            pred['flair'].append(flair[0])
            pred['URL'].append(form.URL.data)
            post = pd.DataFrame(pred)
        return redirect(url_for('Flair_Detected'))
    return render_template('Home.html', form=form)


@app.route("/Flair_Detected", methods=['GET', 'POST'])
def Flair_Detected():
    return render_template('Flair_detected.html',output = post)

# argument parsing
parser = reqparse.RequestParser()
parser.add_argument('files')


class PredictionTest(Resource):
    def post(self):
       
        urls = request.files['upload_file'].readlines()

        urls = [x.decode('utf8').strip('\n') for x in urls]

        Results = pd.DataFrame(columns = ['URL','Flair'])

        for url in urls:
            flair = predict_flair(url)
            Results = Results.append([{'URL': url, 'Flair': flair[0]}], ignore_index=True)

        output = json.dumps(Results.to_dict('records'))

        res = make_response(jsonify(output), 200)

        return res

# Setup the Api resource routing here
# Route the URL to the resource
api.add_resource(PredictionTest, '/automated_testing', methods=['GET', 'POST'])


if __name__ == '__main__':
    app.run(debug=True)