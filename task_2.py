from flask import Flask, jsonify, request, g
from random import choice
from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "test.db"
app = Flask(__name__)
columns = ['id', 'author', 'text']


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


quotes = [
   {
       "id": 3,
       "rating": 1,
       "author": "Rick Cook",
       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
   },
   {
       "id": 5,
       "rating": 1,
       "author": "Waldi Ravens",
       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
   },
   {
       "id": 6,
       "rating": 1,
       "author": "Mosher’s Law of Software Engineering",
       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
   },
   {
       "id": 8,
       "rating": 1,
       "author": "Yoggi Berra",
       "text": "В теории, теория и практика неразделимы. На практике это не так."
   },

]


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


def get_connection_and_cursor(db_name="test.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    return connection, cursor


def close_connection_and_cursor(connection=None, cursor=None):
    if cursor:
        cursor.close()
    if connection:
        connection.close()


@app.route('/quotes')
def get_quotes():
    #connection, cursor = get_connection_and_cursor()
    connection = get_db()
    cursor = connection.cursor()
    query = "select * FROM quotes"
    execute_result = cursor.execute(query).fetchall()
    results = [dict(zip(columns, result)) for result in execute_result]
    #close_connection_and_cursor(connection, cursor)
    return jsonify(results)


@app.route('/quotes/<int:quote_id>')
def show_quote_by_id(quote_id):
    #connection, cursor = get_connection_and_cursor()
    connection = get_db()
    cursor = connection.cursor()
    query = f"select * FROM quotes where id=?"
    execute_result = cursor.execute(query, (quote_id,)).fetchone()
    #close_connection_and_cursor(connection, cursor)
    if execute_result:
        quote = dict(zip(columns, execute_result))
        return quote, 200
    return f"Quote with id={quote_id} not found", 404


@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    quotes.append(data)
    #connection, cursor = get_connection_and_cursor()
    connection = get_db()
    cursor = connection.cursor()
    query = f"INSERT INTO quotes (author, text) VALUES (?, ?);"
    data_for_insert = (data['author'], data['text'])
    execute_result = cursor.execute(query, (*data_for_insert, )).lastrowid
    connection.commit()
    #close_connection_and_cursor(connection, cursor)
    return f'id={str(execute_result)}, author={data["author"]}, text={data["text"]}', 201


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    data = request.json
    #connection, cursor = get_connection_and_cursor()
    connection = get_db()
    cursor = connection.cursor()
    update_quote = f"UPDATE quotes SET author=?, text=? WHERE id=?"
    data_for_update = (data['author'], data['text'], quote_id)
    result = cursor.execute(update_quote, (*data_for_update, )).rowcount
    connection.commit()
   # close_connection_and_cursor(connection, cursor)
    if result:
        return f'Rows was modified: {result}', 201
    else:
        return f'Rows was modified: 0', 404


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
    #connection, cursor = get_connection_and_cursor()
    connection = get_db()
    cursor = connection.cursor()
    delete_quote_str = 'DELETE FROM quotes WHERE id=?;'
    result = cursor.execute(delete_quote_str, (quote_id, )).rowcount
    if result:
        return f"Quote with id {quote_id} is deleted.", 200
    return f'Quote with quote_id={quote_id} not found', 404


@app.route("/quotes/filter")
def get_quotes_by_filter():
    #При работе через args, нужн оприводить типы
    #filter_dict = request.args
    # filtered_quotes = list(filter(lambda q: all(q.get(key) == type(q.get(key))(value)
    #                                             for key, value in filter_dict.items()), quotes))
    filter_dict = request.json

    filtered_quotes = list(filter(lambda q: all(q.get(key) == value
                                                for key, value in filter_dict.items()), quotes))

    if filtered_quotes:
        return filtered_quotes, 201
    return 'Change filter params. The result is empty', 201


if __name__ == "__main__":
   app.run(debug=True)
