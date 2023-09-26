from flask import Flask, jsonify, request
from random import choice

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

about_me = {
   "name": "Вадим",
   "surname": "Шиховцов",
   "email": "vshihovcov@specialist.ru"
}

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


@app.route("/about")
def about():
   return jsonify(about_me)


@app.route('/quotes')
def get_quotes():
    return quotes


@app.route('/quotes/<int:quote_id>')
def show_quote_by_id(quote_id):
    quote = [quote for quote in quotes if quote["id"] == quote_id]
    if quote:
        return quote, 200
    return f"Quote with id={quote_id} not found", 404


@app.route('/quotes/count')
def get_quotes_count():
    return str(len(quotes))


@app.route('/quotes/random_quote')
def get_random_quote():
    return choice(quotes)


@app.route("/")
def hello_world():
   return "Hello, World!"


@app.route("/quotes", methods=['POST'])
def create_quote():
   data = request.json
   data['id'] = max([quote['id'] for quote in quotes]) + 1
   data['rating'] = data['rating'] if data.get('rating', None) and 1 <= data['rating'] <= 5 else 1
   quotes.append(data)

   return data, 201


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    data = request.json
    for quote in quotes:
        if quote['id'] == quote_id:
            for key, value in data.items():
                if key == 'rating':
                    quote[key] = value if 1 <= value <= 5 else 1
                else:
                    quote[key] = value
            return quote, 201
    return f'Quote with quote_id={quote_id} not found', 404


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
    for quote in quotes:
        if quote['id'] == quote_id:
            quotes.remove(quote)
            return f"Quote with id {quote_id} is deleted.", 200
    return f'Quote with quote_id={quote_id} not found', 404


def convert_request_args_to_right_type(request_args):
    typed_request_args = {}
    for key in request_args.keys():
        if key in ['id', 'rating']:
            typed_request_args[key] = int(request_args[key])
        else:
            typed_request_args[key] = request_args[key]
    return typed_request_args


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
