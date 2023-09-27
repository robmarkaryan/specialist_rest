from flask import Flask, jsonify, request, g
from flask_sqlalchemy import SQLAlchemy
from random import choice
from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'main.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class QuoteModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(32), unique=False)
    text = db.Column(db.String(255), unique=False)
    rating = db.Column(db.Integer, nullable=False)

    def __init__(self, author, text, rating=1):
        self.author = author
        self.text = text
        self.rating = rating

    def __str__(self):
        return f'Author: {self.author}, text: {self.text}'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    print(f'Db connection in opened: {db}')
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        print(f'Db connection in closed: {db}')
        db.close()


def to_dict(object):
    model_dict = object.__dict__
    del model_dict['_sa_instance_state']
    return model_dict


@app.route('/quotes')
def get_quotes():
    quotes = QuoteModel.query.all()
    return jsonify([to_dict(quote) for quote in quotes])


@app.route('/quotes/<int:quote_id>')
def show_quote_by_id(quote_id):
    quote = QuoteModel.query.get(quote_id)
    if quote:
        return to_dict(quote), 200
    return f"Quote with id={quote_id} not found", 404


@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    quote = QuoteModel(data['author'], data['text'])
    db.session.add(quote)
    db.session.commit()
    return f'Quote added: {str(quote)}', 200


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    data = request.json
    quote = QuoteModel.query.get(quote_id)
    quote.author, quote.text = data['author'], data['text']
    db.session.commit()
    if quote:
        return f'Rows was modified: {quote}', 201
    else:
        return f'Rows was modified: 0', 404


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
    quote = QuoteModel.query.get(quote_id)
    db.session.delete(quote)
    db.session.commit()
    if quote:
        return f"Quote with id {quote_id} is deleted.", 200
    return f'Quote with quote_id={quote_id} not found', 404


@app.route("/quotes/filter")
def get_quotes_by_filter():

    filter_dict = request.json

    if filter_dict['author'] and filter_dict['rating']:
        filtered_quotes = QuoteModel.query.filter(QuoteModel.author == filter_dict['author'],
                                                  QuoteModel.rating == filter_dict['rating']).all()
    elif filter_dict['author']:
        filtered_quotes = QuoteModel.query.filter(QuoteModel.author == filter_dict['author']).all()
    elif filter_dict['rating']:
        filtered_quotes = QuoteModel.query.filter(QuoteModel.rating == filter_dict['rating']).all()
    else:
        filtered_quotes = QuoteModel.query.all()
    if filtered_quotes:
        return jsonify([to_dict(filtered_quote) for filtered_quote in filtered_quotes]), 201
    return 'Change filter params. The result is empty', 201


if __name__ == "__main__":
   app.run(debug=True)
