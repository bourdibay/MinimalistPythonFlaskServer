
import datetime
from flask import Flask, request, render_template
from werkzeug import security
import json
from flask_cors import cross_origin

from random import randint

from server_files import data
from server_files.data import db
from server_files import utils

import server_files.actions

import random

def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = True
    app.register_blueprint(server_files.actions.actions)
    return app
    
app = create_app()

@app.route('/')
@cross_origin() # allow all origins all methods.
def hello_world():
    return "Hello world!"

def test_init():
    """
    This function performs some insertions into the database.
    """
    db.create_all()
    question = data.Questions("What is your name ?", "2015-05-25 17:30", "2015-05-25 18:05")
    answers = [data.Answers("Name1"), data.Answers("Name2"),
               data.Answers("Name3"), data.Answers("Name4")]
    db.session.add(question)
    for ans in answers:
        db.session.add(ans)
    db.session.commit()

    for ans in answers:
        answer_binding = data.AnswersBinding(question.id, ans.id)
        db.session.add(answer_binding)
    db.session.commit()

    question = data.Questions("What is your name 2 ?", "2015-05-25 18:00", "2015-05-25 18:30")
    answers[1] = data.Answers("2_Name2")
    answers[3] = data.Answers("2_Name4")
    db.session.add(question)
    db.session.add(answers[1])
    db.session.add(answers[3])
    db.session.commit()

    for ans in answers:
        answer_binding = data.AnswersBinding(question.id, ans.id)
        db.session.add(answer_binding)
    db.session.commit()

def clean_db():
    db.reflect()
    db.drop_all()

@app.route('/cleanall')
@cross_origin()
def clean_all():
    clean_db()
    test_init()
    return "Clean!"

# catch-all
@app.route('/<path>')
@cross_origin() # allow all origins all methods.
def serve_index(path):
    return "serve index"

# Fill the database at the launch.
@app.before_first_request
def initialize():
    try:
        clean_db()
        test_init()
    except Exception as e:
        utils.print_exception(e)

@app.teardown_appcontext
def teardown_db(exception):
    db.session.close()

if __name__ == '__main__':
    app.run()
