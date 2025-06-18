from flask import Flask, jsonify
import random
from flask import request
import sqlite3
from pathlib import Path

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class Base(DeclarativeBase):
    pass



BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db" # <- тут путь к БД

app = Flask(__name__)
app.json.ensure_ascii = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'main.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)

class QuoteModel(db.Model):
    tablename__ = 'quotes'
    id: Mapped[int] = mapped_column(primary_key=True)
    author: Mapped[str] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(default=1)

    def __init__(self, author, text, rating):
        self.author = author
        self.text = text
        self.rating = rating

    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author,
            "text": self.text,
            "rating": self.rating
        }



def validate_rating(rating):
    return rating is not None and 1 <= rating <= 5

def convert_quotes(quotes_db):
    if isinstance(quotes_db, QuoteModel):
        return quotes_db.to_dict()
    else:
        quotes = []
        for quote_db in quotes_db:
            quotes.append(quote_db.to_dict())
        return quotes

def get_quote_by_id(id):
    quotes_db = db.session.get(QuoteModel, id)
    return quotes_db


@app.route("/quotes", methods=['GET'])
def show_quotes():
    author_filter = request.args.get('author')
    rating_filter = request.args.get('rating')

    query = db.session.query(QuoteModel)

    if author_filter:
        query = query.filter(QuoteModel.author == author_filter)
    
    if rating_filter:
        query = query.filter(QuoteModel.rating == rating_filter)
            
    quotes_db = query.all()
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
    
    if 'rating' in data and validate_rating(data['rating']):
        rating = data['rating']
    else:
        rating = 1

    q = QuoteModel(data['author'], data['text'], rating)

    db.session.add(q)
    db.session.commit()

    if not q.id:
        return "No row created", 400   
    quotes_db = get_quote_by_id(q.id) 
    quote = convert_quotes(quotes_db)
    return jsonify(quote), 201

@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):    
    new_data = request.json
    if not new_data:
        return "No data", 400
    
    q = db.session.get(QuoteModel, id)
    
    if not q:
        return "No rows updated", 400 

    if 'text' in new_data:
        q.text = new_data['text']
    
    if 'author' in new_data:
        q.author = new_data['author']
    
    db.session.commit()
      
    quotes_db = get_quote_by_id(id) 
    quote = convert_quotes(quotes_db)
    return jsonify(quote), 201

@app.route("/quotes/<int:id>", methods=['DELETE'])
def delete_quote(id):
    q = db.session.get(QuoteModel, id)
    
    if not q:
        return "No rows to delete", 400 

    db.session.delete(q)
    db.session.commit()
    return f"Quote with id {id} deleted.", 200

if __name__ == "__main__":
    app.run(debug=True)