from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config


db = SQLAlchemy()

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

from models.user import User
from models.contest import Contest
from models.problem import Problem
from models.submission import Submission
from models.participant import ContestParticipant

@app.route("/")
def home():
    return {"message": "Server running"}

if __name__ == "__main__":
    app.run(debug=True)