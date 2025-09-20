# from flask import Flask
from flask_pymongo import PyMongo
from app import app
# app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb+srv://parthchawla5012_db_user:leaSWjoT0b2bj3VI@artisans.s8y9gfm.mongodb.net/marketplace"
mongo = PyMongo(app)
db = mongo.db
# Testing
# if db is not None:
#     print("success")
# comments = list(db.comments.find())
# print(comments)
