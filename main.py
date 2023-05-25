import datetime as dt
import os

import requests as r
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Text, Integer, Date, desc

EXT_API_URL: str = 'https://jservice.io/api/random?count=1'


app: Flask = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("POSTGTRES_SQL_URI", "sqlite:///test.db")
db: SQLAlchemy = SQLAlchemy(app)


class QuizQuestions(db.Model):
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, unique=True, index=True, nullable=False)
    quiz_txt = Column(Text, nullable=False, default="")
    answer_txt = Column(Text, nullable=False, default="")
    quiz_date = Column(Date, nullable=False)

    def to_json(self):
        return jsonify({"quiz_id": self.quiz_id,
                        "quiz_txt": self.quiz_txt,
                        "answer_txt": self.answer_txt,
                        "quiz_date": self.quiz_date.isoformat()})


with app.app_context():
    db.create_all()


@app.route("/", methods=['POST'])
def main_route():
    user_req = request.json
    if user_req:
        n = user_req.get("questions_num", 0)
        try:
            n = int(n)
        except ValueError:
            return jsonify({}), 400
        if n:
            created_date: dt.date = dt.datetime.now().date()
            i = 0
            while i < n:
                api_resp = r.get(EXT_API_URL)
                if api_resp.ok:
                    json_data = api_resp.json()[0]
                    quiz_id = json_data.get("id")
                    quiz_txt = json_data.get("question", "")
                    answer_txt = json_data.get("answer", "")
                    created_at_txt = json_data.get("created_at", "")
                    try:
                        created_date: dt.date = dt.datetime.strptime(created_at_txt, "%Y-%m-%dT%H:%M:%S.%f%z").date()
                    except ValueError:
                        pass
                    if db.session.query(QuizQuestions).filter(QuizQuestions.quiz_id == quiz_id).first():
                        continue
                    new_quiz: QuizQuestions = QuizQuestions(quiz_id=quiz_id, quiz_txt=quiz_txt,
                                                            answer_txt=answer_txt, quiz_date=created_date)
                    db.session.add(new_quiz)
                    db.session.commit()
                    i += 1
                else:
                    return jsonify({}), api_resp.status_code
            last_quiz = db.session.query(QuizQuestions).order_by(desc(QuizQuestions.id)).first()
            if last_quiz:
                return last_quiz.to_json()
            return jsonify({})
        else:
            return jsonify({}), 400
    else:
        return jsonify({}), 400


if __name__ == '__main__':
    app.run(debug=True, port=8080)
