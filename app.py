from flask import Flask, jsonify
import random
from flask import request
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db" # <- тут путь к БД

app = Flask(__name__)
app.json.ensure_ascii = False


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

def convert_quotes(quotes_db):
    keys = ("id", "author", "text")
    if isinstance(quotes_db, tuple):
        return dict(zip(keys, quotes_db))
    else:
        quotes = []
        for quote_db in quotes_db:
            quote = dict(zip(keys, quote_db))
            quotes.append(quote)
        return quotes

def get_quote_by_id(id):
    select_quote = "SELECT * from quotes WHERE id=?"
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()
    cursor.execute(select_quote, (id,))
    quotes_db = cursor.fetchone()
    cursor.close()
    connection.close()
    return quotes_db


@app.route("/quotes", methods=['GET'])
def show_quotes():
    select_quotes = "SELECT * from quotes"
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()
    cursor.execute(select_quotes)
    quotes_db = cursor.fetchall()
    cursor.close()
    connection.close()
    quotes = convert_quotes(quotes_db)
    return jsonify(quotes), 200

@app.route("/quotes/<int:id>")
def get_quote(id):
    quotes_db = get_quote_by_id(id)
    if not quotes_db:
        return jsonify(f"Quote with id {id} not found"), 404

    quote = convert_quotes(quotes_db)
    return jsonify(quote), 200
    
# @app.route('/quotes/count')
# def get_quotes_count():
#     count_int = len(quotes)
#     count = {
#         "count": count_int
#     }
#     return count

@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json

    if not data or 'author' not in data or 'text' not in data:
        return "No valid data", 400
    
    # if 'rating' in data and validate_rating(data['rating']):
    #     rating = data['rating']
    # else:
    #     rating = 1
    
    # new_id = next_id(quotes)

    insert_quote = "INSERT INTO quotes (author, text) VALUES (?, ?);"
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()
    cursor.execute(insert_quote, (data['author'], data['text']))
    connection.commit()
    id_last = cursor.lastrowid
    cursor.close()
    connection.close()
    if not id_last:
        return "No row created", 400   
    quotes_db = get_quote_by_id(id_last) 
    quote = convert_quotes(quotes_db)
    return jsonify(quote), 201

@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):    
    new_data = request.json
    if not new_data:
        return "No data", 400
    
    set_clauses = []
    values = []
    
    if 'text' in new_data:
        set_clauses.append("text = ?")
        values.append(new_data['text'])
    
    if 'author' in new_data:
        set_clauses.append("author = ?")
        values.append(new_data['author'])
    
    set_query = ", ".join(set_clauses)
    update_quote = f"UPDATE quotes SET {set_query} WHERE id = ?"
    values.append(id)

    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()    
    cursor.execute(update_quote, tuple(values))
    connection.commit()
    count = cursor.rowcount
    cursor.close()
    connection.close()
    
    if count == 0:
        return "No rows updated", 400   
    quotes_db = get_quote_by_id(id) 
    quote = convert_quotes(quotes_db)
    return jsonify(quote), 201

@app.route("/quotes/<int:id>", methods=['DELETE'])
def delete_quote(id):
    delete_quote = "DELETE from quotes WHERE id=?"
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()    
    cursor.execute(delete_quote, (id,))
    connection.commit()
    count = cursor.rowcount
    cursor.close()
    connection.close()
    
    if count == 0:
        return "No rows deleted", 400
    return f"Quote with id {id} is deleted.", 200

if __name__ == "__main__":
    app.run(debug=True)