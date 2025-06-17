from flask import Flask
import random
from flask import request

app = Flask(__name__)
app.json.ensure_ascii = False

@app.route("/")
def hello_world():
    return "Hello, World!"

about_me = {
    "name": "Вадим",
    "surname": "Шиховцов",
    "email": "vshihovcov@specialist.ru"
}

@app.route("/about")
def about():
    return about_me

quotes = [
    {
        "id": 3,
        "author": "Rick Cook",
        "text": "Программирование сегодня — это гонка "
                "разработчиков программ, стремящихся писать программы с "
                "большей и лучшей идиотоустойчивостью, и вселенной, которая "
                "пытается создать больше отборных идиотов. Пока вселенная "
                "побеждает.",
        "rating": 2
    },
    {
        "id": 5,
        "author": "Waldi Ravens",
        "text": "Программирование на С похоже на быстрые танцы "
                "на только что отполированном полу людей с острыми бритвами в "
                "руках.",
        "rating": 4
    },
    {
        "id": 6,
        "author": "Mosher’s Law of Software Engineering",
        "text": "Не волнуйтесь, если что-то не работает. Если "
                "бы всё работало, вас бы уволили.",
        "rating": 4
    },
    {
        "id": 8,
        "author": "Yoggi Berra",
        "text": "В теории, теория и практика неразделимы. На "
                "практике это не так.",
        "rating": 3
    }
]

def next_id(quotes_list):
    if not quotes_list: 
        return 1
    return quotes_list[-1]["id"] + 1

def validate_rating(rating):
    return rating is not None and 1 <= rating <= 5

def find_quote_by_id(quotes_list, target_id):
    for quote in quotes_list:
        if quote["id"] == target_id:
            return quote
    return None


@app.route("/quotes", methods=['GET'])
def show_quotes():
    author_filter = request.args.get('author')
    rating_filter = request.args.get('rating')
    
    filtered_quotes = quotes.copy()

    if author_filter:
        filtered_quotes = [q for q in filtered_quotes 
                          if author_filter.lower() == q['author'].lower()]
    
    if rating_filter:
        rating_value = int(rating_filter)
        filtered_quotes = [q for q in filtered_quotes 
                          if q['rating'] == rating_value]
            
    return filtered_quotes

@app.route("/quotes/<int:id>")
def get_quote(id):
    for quote in quotes:
        if quote["id"] == id:
            return quote
        return f"Quote with id={id} not found", 404
    
@app.route('/quotes/count')
def get_quotes_count():
    count_int = len(quotes)
    count = {
        "count": count_int
    }
    return count

@app.route('/quotes/random')
def get_random_quote():
    random_quote = random.choice(quotes)
    return random_quote

@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json

    if not data or 'author' not in data or 'text' not in data:
        return "No data", 400
    
    if 'rating' in data and validate_rating(data['rating']):
        rating = data['rating']
    else:
        rating = 1
    
    new_id = next_id(quotes)

    new_quote = {
        "id": new_id,
        "author": data['author'],
        "text": data['text'],
        "rating": rating
    }
    
    quotes.append(new_quote)
    
    return new_quote, 201

@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    quote = find_quote_by_id(quotes, id)
    if not quote:
        return f"Quote with id {id} not found", 404
    
    new_data = request.json
    if not new_data:
        return "No data", 400
    
    if 'author' in new_data:
        quote['author'] = new_data['author']
    if 'text' in new_data:
        quote['text'] = new_data['text']
    
    return quote, 200

@app.route("/quotes/<int:id>", methods=['DELETE'])
def delete_quote(id):
    # Ищем цитату по ID
    quote = find_quote_by_id(quotes, id)
    if not quote:
        return f"Quote with id {id} not found", 404
    
    # Удаляем цитату из списка
    quotes.remove(quote)
    return f"Quote with id {id} is deleted.", 200

if __name__ == "__main__":
    app.run(debug=True)