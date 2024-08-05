import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

db = SQLAlchemy(app)

import routes

if __name__ == "__main__":
    app.run(debug=True)
