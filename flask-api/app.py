from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


@app.route("/stories", methods=["GET"])
def get_stories():
    query = request.args.get("status")
    return jsonify()


@app.route("/stories/<int:stories_id>", methods=["GET"])
def get_story():
    return jsonify()
