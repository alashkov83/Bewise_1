import datetime as dt
import os
from http import HTTPStatus

import requests as r
from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Text, Integer, Date, desc

EXT_API_URL: str = 'https://jservice.io/api/random'

app: Flask = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("POSTGTRES_SQL_URI", "sqlite:///test.db")
db: SQLAlchemy = SQLAlchemy(app)


class QuizQuestions(db.Model):
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, unique=True, index=True, nullable=False)
    quiz_txt = Column(Text, nullable=False, default="")
    answer_txt = Column(Text, nullable=False, default="")
    quiz_date = Column(Date, nullable=False)

    def to_json(self) -> Response:
        return jsonify({"quiz_id": self.quiz_id,
                        "quiz_txt": self.quiz_txt,
                        "answer_txt": self.answer_txt,
                        "quiz_date": self.quiz_date.isoformat()})


with app.app_context():
    db.create_all()


def save_to_db(json_data: dict) -> bool:
    quiz_id: str = json_data.get("id")
    quiz_txt: str = json_data.get("question", "")
    answer_txt: str = json_data.get("answer", "")
    airdate_txt: str = json_data.get("airdate", "")
    try:
        airdate: dt.date = dt.datetime.strptime(airdate_txt, "%Y-%m-%dT%H:%M:%S.%f%z").date()
    except ValueError:
        airdate: dt.date = dt.datetime.now().date()
    if db.session.query(QuizQuestions).filter(QuizQuestions.quiz_id == quiz_id).first():
        return False
    new_quiz: QuizQuestions = QuizQuestions(quiz_id=quiz_id, quiz_txt=quiz_txt,
                                            answer_txt=answer_txt, quiz_date=airdate)
    db.session.add(new_quiz)
    db.session.commit()
    return True


@app.route("/", methods=['POST'])
def main_route() -> tuple[Response, int]:
    user_req = request.json
    if user_req:
        n = user_req.get("questions_num", 0)
        try:
            n = int(n)
        except ValueError:
            return jsonify({}), HTTPStatus.BAD_REQUEST
        if n:
            i = 0
            api_resp: r.Response = r.get(EXT_API_URL, params={'count': n})
            if api_resp.ok:
                for json_data in api_resp.json():
                    if save_to_db(json_data):
                        i += 1
            else:
                return jsonify({}), api_resp.status_code
            while i < n:
                api_resp: r.Response = r.get(EXT_API_URL, params={'count': 1})
                if api_resp.ok:
                    json_data: dict = api_resp.json()[0]
                    if save_to_db(json_data):
                        i += 1
                else:
                    return jsonify({}), api_resp.status_code
            last_quiz = db.session.query(QuizQuestions).order_by(desc(QuizQuestions.id)).first()
            if last_quiz:
                return last_quiz.to_json(), HTTPStatus.OK
            return jsonify({}), HTTPStatus.BAD_REQUEST
        else:
            return jsonify({}), HTTPStatus.BAD_REQUEST
    else:
        return jsonify({}), HTTPStatus.BAD_REQUEST


if __name__ == '__main__':
    app.run(debug=True, port=8080)
