import os
import server
import re
from server import app, db
from server_files import data
import unittest
import tempfile
import json
from datetime import datetime

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
#    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4), m.group(5))

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
        server.test_init()

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

    def test_createQuestion_correctArgs(self):
        """
        Test that we can create a valid question/answers.
        Route tested: /questions/create_question
        """
        # Create question
        question_test = QuestionTest((2015, 5, 30, 15, 52), (2015, 5, 30, 16, 1))
        rv = self.app.post("/questions/create_question", data=dict(
            question=question_test.question,
            answers=question_test.answers,
            datetime_start=question_test.datetime_start,
            datetime_expiry=question_test.datetime_expiry),
                      follow_redirects=True)

        # Check return value
        rv_data = json.loads(rv.data.decode("utf-8"))
        self.assertTrue(rv_data['success'])

    def test_createQuestion_correctlyInserted(self):
        """
        Test that a valid question/answers created are really inserted into the database.
        Route tested: /questions/create_question
        """
        # Create question
        question_test = QuestionTest((2015, 5, 30, 15, 52), (2015, 5, 30, 16, 1))
        rv = self.app.post("/questions/create_question", data=dict(
            question=question_test.question,
            answers=question_test.answers,
            datetime_start=question_test.datetime_start,
            datetime_expiry=question_test.datetime_expiry),
                      follow_redirects=True)

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
        now = datetime.now()
        # Create a question valid for 5 minutes
        question_test = QuestionTest((now.year, now.month, now.day, now.hour, now.minute), (now.year, now.month, now.day, now.hour, now.minute + 5))
        rv = self.app.post("/questions/create_question", data=dict(
            question=question_test.question,
            answers=question_test.answers,
            datetime_start=question_test.datetime_start,
            datetime_expiry=question_test.datetime_expiry),
                      follow_redirects=True)

        # Check return value
        rv_data = json.loads(rv.data.decode("utf-8"))
        self.assertTrue(rv_data['success'])

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


if __name__ == '__main__':
    unittest.main()