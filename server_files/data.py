
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
import sys

app = Flask(__name__)
if sys.platform.startswith('win32') :
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

db = SQLAlchemy(app)

############ DATABASE MODELS ###############

class Questions(db.Model) :
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    content = db.Column(db.String(50), unique=True)
    datetime_start = db.Column(db.DateTime)
    datetime_expiry = db.Column(db.DateTime)
    
    def __init__(self, question, datetime_start, datetime_expiry):
        self.content = question
        self.datetime_start = datetime.strptime(datetime_start, '%Y-%m-%d %H:%M')
        self.datetime_expiry = datetime.strptime(datetime_expiry, '%Y-%m-%d %H:%M')
    
class Answers(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    content = db.Column(db.String(50))
    
    def __init__(self, answer):
        self.content = answer

class AnswersBinding(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    question_id = db.Column(db.Integer)
    answer_id = db.Column(db.Integer)
    nb_votes = db.Column(db.Integer)

    def __init__(self, question_id, answer_id):
        self.question_id = question_id
        self.answer_id = answer_id
        self.nb_votes = 0
