from flask import Flask, jsonify
import random
from flask import request
import sqlite3
from pathlib import Path

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from flask_migrate import Migrate
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class Base(DeclarativeBase):
    pass



BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.json.ensure_ascii = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'quotes.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)
migrate = Migrate(app, db)


class AuthorModel(db.Model):
    __tablename__ = 'authors'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[int] = mapped_column(String(32), index= True, unique=True)
    surname: Mapped[str] = mapped_column(String(50), default='Smit')
    quotes: Mapped[list['QuoteModel']] = relationship(back_populates='author', lazy='dynamic', cascade="all, delete-orphan")
    
    def __init__(self, name, surname):
        self.name = name
        self.surname = surname
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname
        }


class QuoteModel(db.Model):
    __tablename__ = 'quotes'
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('authors.id'))
    author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
    text: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(default=1, nullable=False)

    def __init__(self, author, text, rating):
        self.author = author
        self.text = text
        self.rating = rating

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "rating": self.rating
        }



def validate_rating(rating):
    return rating is not None and 1 <= rating <= 5

def convert_authors(authors_db):
    if isinstance(authors_db, AuthorModel):
        return authors_db.to_dict()
    else:
        authors = []
        for author_db in authors_db:
            authors.append(author_db.to_dict())
        return authors

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


@app.route("/authors", methods=["POST"])
def create_author():
    author_data = request.json
    author = AuthorModel(author_data["name"], author_data["surname"])
    db.session.add(author)
    db.session.commit()
    return author.to_dict(), 201

@app.route("/authors", methods=["GET"])
def get_author():
    author = db.session.query(AuthorModel)
    authors = convert_authors(author)
    return authors, 201

@app.route("/authors/<int:id>", methods=["GET"])
def get_author_by_id(id):
    author = db.session.get(AuthorModel, id)
    if not author:
        return jsonify(f"Author with id {id} not found"), 404
    return author.to_dict(), 201

@app.route("/quotes", methods=['GET'])
def show_quotes():
    #author_filter = request.args.get('author')
    #rating_filter = request.args.get('rating')

    query = db.session.query(QuoteModel)

    # if author_filter:
    #     query = query.filter(QuoteModel.author == author_filter)
    
    # if rating_filter:
    #     query = query.filter(QuoteModel.rating == rating_filter)
            
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

@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_quote(author_id: int):
    author = db.session.get(AuthorModel, author_id)
    new_quote = request.json
    if 'rating' in new_quote and validate_rating(new_quote['rating']):
        rating = new_quote['rating']
    else:
        rating = 1
    q = QuoteModel(author, new_quote["text"], rating)
    db.session.add(q)
    db.session.commit()
    return convert_quotes(q), 201

@app.route("/authors/<int:author_id>/quotes", methods=["GET"])
def get_author_quotes(author_id: int):
    author = db.session.get(AuthorModel, author_id)  
    if not author:
        return jsonify(f"Author with id {id} not found"), 404
    return jsonify(author.to_dict(), convert_quotes(author.quotes)), 201

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

@app.route("/authors/<int:id>", methods=['DELETE'])
def delete_author(id):
    a = db.session.get(AuthorModel, id)
    
    if not a:
        return "No rows to delete", 400 

    db.session.delete(a)
    db.session.commit()
    return f"Author with id {id} deleted.", 200

if __name__ == "__main__":
    app.run(debug=True)