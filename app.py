from flask import Flask, jsonify, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from random import choice
from pathlib import Path
import sqlite3
from sqlalchemy import func


BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'quotes.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
columns = ['id', 'author', 'text']

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class AuthorModel(db.Model):

    __tablename__ = 'authors'

    id: int = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    surname = db.Column(db.String(32), unique=False, nullable=True)
    quotes = db.relationship('QuoteModel', backref='author', lazy='dynamic')
    changed = db.Column(db.Integer, default=1, nullable=True)

    def __init__(self, name):
        self.name = name

    def mark_as_deleted(self):
        self.changed = 3

        for quote in self.quotes:
            quote.mark_as_deleted()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name': self.surname
        }


class QuoteModel(db.Model):

    __tablename__ = 'quotes'

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey(AuthorModel.id))
    text = db.Column(db.String(255), unique=False)
    rating = db.Column(db.Integer, nullable=False, default=1)
    changed = db.Column(db.Integer, default=1, nullable=True)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __init__(self, author: AuthorModel, text, created, rating=1, changed=1):
        self.author_id = author.id
        self.text = text
        self.rating = rating
        self.changed = changed
        self.created = created

    def __str__(self):
        return f'Author: {self.author}, text: {self.text}'

    def __repr__(self):
        return f'Author: {self.author}, text: {self.text}, rating: {self.rating}'

    def to_dict(self):
        return {
            'id': self.id,
            'author': self.author.id,
            'text': self.text,
            'rating': self.rating,
            'created': self.created.strftime('%d.%m.%Y')
        }

    def mark_as_deleted(self):
        self.changed = 3

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
    return jsonify([quote.to_dict() for quote in quotes])


@app.route('/quotes/<int:quote_id>')
def show_quote_by_id(quote_id):
    quote = QuoteModel.query.get(quote_id)
    if quote:
        return to_dict(quote), 200
    return f"Quote with id={quote_id} not found", 404


@app.route('/quotes/<int:quote_id>/change_rating_by/<string:rating_diff>', methods=['PUT'])
def increase_or_decrease_quote_rating(quote_id, rating_diff):
    quote = QuoteModel.query.get(quote_id)
    rating_diff = int(rating_diff)
    if quote:
        quote.rating += rating_diff
        if quote.rating > 5:
            quote.rating = 5
        elif quote.rating < 1:
            quote.rating = 1

        db.session.add(quote)
        db.session.commit()
    return quote.to_dict(), 200


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

    filtered_quotes = QuoteModel.query.filter_by(**filter_dict).all()
    if filtered_quotes:
        return jsonify([filtered_quote._to_dict() for filtered_quote in filtered_quotes]), 201
    return 'Change filter params. The result is empty', 201


@app.route("/quotes", methods=['POST'])
def create_quote_old():
    data = request.json
    quote = QuoteModel(**data)
    db.session.add(quote)
    db.session.commit()
    return f'Quote added: {str(quote)}', 200


@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_quote(author_id):
    author = AuthorModel.query.get(author_id)
    new_quote = request.json
    q = QuoteModel(author, new_quote["text"])
    db.session.add(q)
    db.session.commit()
    return q.to_dict(), 201


@app.route("/authors/<int:author_id>/quotes")
def get_all_quotes_of_author(author_id):
    quotes = QuoteModel.query.filter_by(author_id=author_id).all()
    if quotes:
        return [quote.to_dict() for quote in quotes], 201
    else:
        return 'Empty', 404


@app.route("/authors", methods=["POST"])
def create_author():
    author_data = request.json
    author = AuthorModel(**author_data)
    db.session.add(author)
    db.session.commit()
    return author.to_dict(), 201


@app.route('/authors/<string:sort_by_column>')
def get_authors(sort_by_column):
    authors = AuthorModel.query.order_by(sort_by_column).all()
    return jsonify([to_dict(author) for author in authors])


@app.route('/authors/')
def get_authors_sorted():
    authors = AuthorModel.query.all()
    return jsonify([to_dict(author) for author in authors])


@app.route('/authors/<int:author_id>')
def get_author(author_id):
    # У автора тип Any | None, не работают подсказки
    author = AuthorModel.query.get(author_id)
    return jsonify(author.to_dict())


@app.route("/authors/<int:author_id>", methods=['PUT'])
def edit_author(author_id):
    data = request.json
    author = AuthorModel.query.get(author_id)
    if author:
        author.name = data['name']
        db.session.commit()
        return f'Rows was modified: {author.to_dict()}', 201
    else:
        return f'Rows was modified: 0', 404


@app.route("/authors/<int:author_id>", methods=['DELETE'])
def delete_authors(author_id):
    author = AuthorModel.query.get(author_id)
    if author:
        db.session.delete(author)
        db.session.commit()
        return f"Quote with id {author_id} is deleted.", 200
    return f'Quote with quote_id={author_id} not found', 404


if __name__ == "__main__":
   app.run(debug=True)
