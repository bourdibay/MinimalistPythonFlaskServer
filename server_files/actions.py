
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from datetime import datetime
from flask import Flask, request, render_template, Blueprint
import json
from flask_cors import cross_origin

from data import db
import data
import utils

actions = Blueprint('actions', __name__)

@actions.route('/questions/create_question', methods=['POST'])
@cross_origin() # allow all origins all methods.
def create_question():
    try:
        args = utils.fieldsToValuesPOST(['question', 'answers',
                                         'datetime_start', 'datetime_expiry'], request)
        arg_question = args['question']
        arg_answers = args['answers']
        arg_datetime_start = args['datetime_start']
        arg_datetime_expiry = args['datetime_expiry']

        arg_answers = [a for a in arg_answers.split(';')]

        does_question_exist = data.Questions.query.filter_by(content=arg_question).first()
        if not does_question_exist:
            question = data.Questions(arg_question, arg_datetime_start, arg_datetime_expiry)
            db.session.add(question)
            db.session.commit()
            question_id = question.id
        else:
            question_id = does_question_exist.id

        for answer in arg_answers:
            does_answer_exist = data.Answers.query.filter_by(content=answer).first()
            if not does_answer_exist:
                ans = data.Answers(answer)
                db.session.add(ans)
                db.session.commit()
                answer_id = ans.id
            else:
                answer_id = does_answer_exist.id

            does_answer_binding_exist = data.AnswersBinding.query.filter_by(question_id=question_id,
                                                                            answer_id=answer_id).first()
            if not does_answer_binding_exist:
                db.session.add(data.AnswersBinding(question_id, answer_id))
                db.session.commit()
        db.session.commit()
        return json.dumps({"success": True, "message": "Question and answers correctly created."})
    except Exception as e:
        utils.print_exception(e)
        return json.dumps({"success": False, "message": str(e)})


@actions.route('/questions/get_all_questions_answers', methods=['GET'])
@cross_origin()
def get_all_questions_answers():
    """ Get all running questions and answers.
    A valid question is a question whose date is superior to the current date,
    and did not expire yet.
    """
    try:
        current_date = datetime.now()

        questions = data.Questions.query.all()
        # I do not use where() clause because I did not find how to call it with flask-sqlalchemy...
        questions = [question for question in questions
                     if question.datetime_start < current_date
                     and question.datetime_expiry > current_date]

        ret = []
        for question in questions:
            bindings = data.AnswersBinding.query.filter_by(question_id=question.id)
            json_answers = []
            for binding in bindings:
                answer = data.Answers.query.filter_by(id=binding.answer_id).first()
                answer_obj = {}
                answer_obj["content"] = answer.content
                answer_obj["answer_id"] = answer.id
                json_answers.append(answer_obj)
            question_obj = {}
            question_obj["datetime_start"] = str(question.datetime_start)
            question_obj["datetime_expiry"] = str(question.datetime_expiry)
            question_obj["answers"] = json_answers
            question_obj["content"] = question.content
            question_obj["question_id"] = question.id
            ret.append(question_obj)
        json_ret = json.dumps(ret)
        return json.dumps({"success": True, "message": json_ret})
    except Exception as e:
        utils.print_exception(e)
        return json.dumps({"success": False, "message": str(e)})

@actions.route('/answer/vote', methods=['POST'])
@cross_origin()
def inc_nb_votes():
    """ Increment the number of votes of a couple question/answer.
    """
    try:
        args = utils.fieldsToValuesPOST(['question_id', 'answer_id'], request)
        arg_question_id = args['question_id']
        arg_answer_id = args['answer_id']
        answer_binding = data.AnswersBinding.query.filter_by(question_id=arg_question_id,
                                                             answer_id=arg_answer_id).first()
        answer_binding.nb_votes += 1
        return json.dumps({"success": True, "message": answer_binding.nb_votes})
    except Exception as e:
        utils.print_exception(e)
        return json.dumps({"success": False, "message": str(e)})
