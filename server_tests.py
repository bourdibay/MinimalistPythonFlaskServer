import os
import server
import re
from server import app, db
from server_files import data
import unittest
import tempfile
import json
from datetime import datetime
from datetime import timedelta

def dateToStr(year, month, day, hour, minute):
    return "{year}-{month}-{day} {hour}:{minute}".format(year=year, 
                                                         month=month,
                                                         day=day,
                                                         hour=hour,
                                                         minute=minute)

def strToDateTuple(str):
    m = re.match(r"(\d+)-(\d+)-(\d+) (\d+):(\d+)", str)
    ret = []
    for i in range(1, 6):
        ret.append(int(m.group(i)))
    return tuple(ret)

class QuestionTest(object):
    def __init__(self, start_date, end_date):
        self.question = "This is a new question"
        # 3 answers separated by ';'
        self.answers_list = ["_answer1_", "answer2_", "_answer3_"]
        self.answers = ';'.join(self.answers_list)

        self.start_date = start_date
        self.end_date = end_date

        self.datetime_start = dateToStr(*(self.start_date))
        self.datetime_expiry = dateToStr(*(self.end_date))


class ServerTestCase(unittest.TestCase):
   
    def setUp(self):
        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'test.db')
        self.app = app.test_client()
        server.clean_db()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def compare_dates(self, actual_datetime, year, month, day, hour, minute):
        self.assertEqual(actual_datetime.year, year)
        self.assertEqual(actual_datetime.month, month)
        self.assertEqual(actual_datetime.day, day)
        self.assertEqual(actual_datetime.hour, hour)
        self.assertEqual(actual_datetime.minute, minute)

    def compare_dates_tuples(self,
                      actual_year, actual_month, actual_day, actual_hour, actual_minute,
                      year, month, day, hour, minute):
        self.assertEqual(actual_year, year)
        self.assertEqual(actual_month, month)
        self.assertEqual(actual_day, day)
        self.assertEqual(actual_hour, hour)
        self.assertEqual(actual_minute, minute)

    def postValidQuestion(self):
        now = datetime.now()
        expired = now + timedelta(minutes=5)
        # Create a question valid for 5 minutes

        question_test = QuestionTest((now.year, now.month, now.day, now.hour, now.minute),
                                     (expired.year, expired.month, expired.day, expired.hour, expired.minute))
        rv = self.app.post("/questions/create_question", data=dict(
            question=question_test.question,
            answers=question_test.answers,
            datetime_start=question_test.datetime_start,
            datetime_expiry=question_test.datetime_expiry),
                      follow_redirects=True)
        return (question_test, rv)

    def postExpiredQuestion(self):
        now = datetime.now()
        start = now - timedelta(minutes=10)
        expired = now - timedelta(minutes=5)
        # Create a question valid for 5 minutes
        question_test = QuestionTest((start.year, start.month, start.day, start.hour, start.minute),
                                     (expired.year, expired.month, expired.day, expired.hour, expired.minute))
        rv = self.app.post("/questions/create_question", data=dict(
            question=question_test.question,
            answers=question_test.answers,
            datetime_start=question_test.datetime_start,
            datetime_expiry=question_test.datetime_expiry),
                      follow_redirects=True)
        return (question_test, rv)

    def checkValidMessage(self, rv):
        # Check return value
        rv_data = json.loads(rv.data.decode("utf-8"))
        self.assertTrue(rv_data['success'])

    def test_createQuestion_correctArgs(self):
        """
        Test that we can create a valid question/answers.
        Route tested: /questions/create_question
        """
        # Create question
        question_test, rv = self.postValidQuestion()
        self.checkValidMessage(rv)

    def test_createQuestion_correctlyInserted(self):
        """
        Test that a valid question/answers created are really inserted into the database.
        Route tested: /questions/create_question
        """
        # Create question
        question_test, _ = self.postValidQuestion()

        # Perform the queries
        actual_question = data.Questions.query.filter_by(content=question_test.question).first()
        all_answers = data.Answers.query.all()
        answers_to_check = [answer for answer in all_answers if answer.content in question_test.answers_list]

        self.assertEqual(len(answers_to_check), len(question_test.answers_list), "The number of answers inserted is not correct")
        self.assertIsNotNone(actual_question, "The question has not been inserted")

        self.compare_dates(actual_question.datetime_start, *question_test.start_date)
        self.compare_dates(actual_question.datetime_expiry, *question_test.end_date)

        question_id = actual_question.id
        for answer in answers_to_check:
            answer_id = answer.id
            answer_binding = data.AnswersBinding.query.filter_by(question_id=question_id, answer_id=answer_id).first()
            self.assertIsNotNone(answer_binding, "The binding between answer {} and question {} has not been performed".format(answer.content, actual_question.content))        

        
    def test_getAllQuestions(self):
        """
        Route tested: /questions/get_all_questions_answers
        """
        # Create a question valid for 5 minutes
        question_test, rv = self.postValidQuestion()

        self.checkValidMessage(rv)

        rv = self.app.get("/questions/get_all_questions_answers")
        rv_data = json.loads(rv.data.decode("utf-8"))
        self.assertTrue(rv_data['success'])

        json_obj = json.loads(rv_data['message'])

        self.assertEqual(len(json_obj), 1) # only 1 question valid right now, the one we've just inserted.
        json_answers = json_obj[0]['answers']
        json_question_id = json_obj[0]['question_id']
        json_question_datetime_expiry = json_obj[0]['datetime_expiry']
        json_question_datetime_start = json_obj[0]['datetime_start']
        json_question_content = json_obj[0]['content']

        self.assertIsNotNone(json_answers)
        self.assertEqual(len(json_answers), 3) # 3 answers

        datetime_start_tuple = strToDateTuple(json_question_datetime_start)
        datetime_end_tuple = strToDateTuple(json_question_datetime_expiry)

        self.compare_dates_tuples(*(datetime_start_tuple + question_test.start_date))
        self.compare_dates_tuples(*(datetime_end_tuple + question_test.end_date))
        self.assertEqual(json_question_content, question_test.question)

    def test_incNbVotes_voteReallyIncreased(self):
        """
        Route tested: /answer/vote
        """
        question_test, rv = self.postValidQuestion()
        self.checkValidMessage(rv)

        question = data.Questions.query.filter_by(content=question_test.question).first()
        answer = data.Answers.query.filter_by(content=question_test.answers_list[-1]).first()
        answer_binding = data.AnswersBinding.query.filter_by(question_id=question.id,
                                                             answer_id=answer.id).first()

        previous_nb_votes = answer_binding.nb_votes

        rv = self.app.post("/answer/vote", data=dict(
            question_id=question.id,
            answer_id=answer.id), follow_redirects=True)
        
        self.checkValidMessage(rv)

        answer_binding = data.AnswersBinding.query.filter_by(question_id=question.id,
                                                             answer_id=answer.id).first()
        current_nb_votes = answer_binding.nb_votes
        self.assertEqual(current_nb_votes, previous_nb_votes + 1, "The vote has not been taken account")

    def test_incNbVotes_expiredQuestion_noIncrease(self):
        """
        Test that if we vote for a question with an expired date < current date,
        we get an error and the number of votes did not change.
        Route tested: /answer/vote
        """
        question_test, rv = self.postExpiredQuestion()
        self.checkValidMessage(rv)

        question = data.Questions.query.filter_by(content=question_test.question).first()
        answer = data.Answers.query.filter_by(content=question_test.answers_list[-1]).first()
        answer_binding = data.AnswersBinding.query.filter_by(question_id=question.id,
                                                             answer_id=answer.id).first()

        previous_nb_votes = answer_binding.nb_votes

        rv = self.app.post("/answer/vote", data=dict(
            question_id=question.id,
            answer_id=answer.id), follow_redirects=True)

        rv_data = json.loads(rv.data.decode("utf-8"))
        self.assertFalse(rv_data['success'])

        answer_binding = data.AnswersBinding.query.filter_by(question_id=question.id,
                                                             answer_id=answer.id).first()
        current_nb_votes = answer_binding.nb_votes
        self.assertEqual(current_nb_votes, previous_nb_votes, "The vote has been taken account, whereas it should have not")

if __name__ == '__main__':
    unittest.main()