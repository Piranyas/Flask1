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
import datetime
from sqlalchemy import func, DateTime

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
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    quotes: Mapped[list['QuoteModel']] = relationship(back_populates='author', lazy='dynamic', cascade="all, delete-orphan")
    
    def __init__(self, name, surname):
        self.name = name
        self.surname = surname
    
    def to_dict(self, include_deleted=False):
        data = {
            "id": self.id,
            "name": self.name,
            "surname": self.surname
        }
        if include_deleted:
            data["is_deleted"] = self.is_deleted
        return data


class QuoteModel(db.Model):
    __tablename__ = 'quotes'
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('authors.id'))
    author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
    text: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(default=1, nullable=False)
    created: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    def __init__(self, author, text, rating):
        self.author = author
        self.text = text
        self.rating = rating

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "rating": self.rating,
            "created": self.created.strftime("%d.%m.%Y") if self.created else None
        }



def validate_rating(rating):
    return rating is not None and 1 <= rating <= 5

def convert_authors(authors_db, include_deleted=False):
    if isinstance(authors_db, AuthorModel):
        return authors_db.to_dict(include_deleted)
    else:
        authors = []
        for author_db in authors_db:
            authors.append(author_db.to_dict(include_deleted))
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
    name_filter = request.args.get('name')
    surname_filter = request.args.get('surname')

    query = AuthorModel.query.filter_by(is_deleted=False)
    if name_filter:
        query = query.filter(AuthorModel.name.ilike(f'%{name_filter}%'))
    if surname_filter:
        query = query.filter(AuthorModel.surname.ilike(f'%{surname_filter}%'))
    authors = query.all()
    authors_list = convert_authors(authors)
    return authors_list, 200

@app.route("/authors/<int:id>", methods=["GET"])
def get_author_by_id(id):
    author = AuthorModel.query.filter_by(id=id, is_deleted=False).first()
    if not author:
        return jsonify(f"Author with id {id} not found"), 404
    return author.to_dict(), 200

@app.route("/quotes", methods=['GET'])
def show_quotes():

    query = QuoteModel.query.join(AuthorModel).filter(AuthorModel.is_deleted == False)
            
    quotes_db = query.all()
    quotes = convert_quotes(quotes_db)
    return jsonify(quotes), 200

@app.route("/quotes/<int:id>")
def get_quote(id):
    quote = QuoteModel.query.join(AuthorModel).filter(
        QuoteModel.id == id,
        AuthorModel.is_deleted == False
    ).first()
    
    if not quote:
        return jsonify(f"Quote with id {id} not found"), 404

    return jsonify(quote.to_dict()), 200

@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_quote(author_id: int):
    author = AuthorModel.query.filter_by(id=author_id, is_deleted=False).first()
    if not author:
        return jsonify(f"Author with id {author_id} not found"), 404
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
    author = AuthorModel.query.filter_by(id=author_id, is_deleted=False).first()
    if not author:
        return jsonify(f"Author with id {author_id} not found"), 404
    quotes = convert_quotes(author.quotes.all())
    return jsonify({
        "author": author.to_dict(),
        "quotes": quotes
    }), 200

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

# Эндпоинты для работы с удаленными авторами
@app.route("/authors/deleted", methods=["GET"])
def get_deleted_authors():
    deleted_authors = AuthorModel.query.filter_by(is_deleted=True).all()
    authors_list = convert_authors(deleted_authors, include_deleted=True)
    return jsonify(authors_list), 200

@app.route("/authors/<int:id>/restore", methods=["PATCH"])
def restore_author(id):
    author = AuthorModel.query.filter_by(id=id, is_deleted=True).first()
    if not author:
        return jsonify(f"Deleted author with id {id} not found"), 404
    
    author.is_deleted = False
    db.session.commit()
    return author.to_dict(include_deleted=True), 200

@app.route("/authors/<int:id>", methods=['DELETE'])
def delete_author(id):
    a = AuthorModel.query.filter_by(id=id, is_deleted=False).first()
    if not a:
        return jsonify(f"Author with id {id} not found or already deleted"), 404

    a.is_deleted = True
    db.session.commit()
    return jsonify({
        "message": f"Author with id {id} marked as deleted",
        "author": a.to_dict(include_deleted=True)
    }), 200
##################################################

@app.route("/quotes/<int:id>/upvote", methods=['PATCH'])
def upvote_quote(id):
    quote = db.session.get(QuoteModel, id)
    if not quote:
        return jsonify(f"Quote with id {id} not found"), 404

    if quote.rating < 5:
        quote.rating += 1
        db.session.commit()
    
    return convert_quotes(quote), 200

@app.route("/quotes/<int:id>/downvote", methods=['PATCH'])
def downvote_quote(id):
    quote = db.session.get(QuoteModel, id)
    if not quote:
        return jsonify(f"Quote with id {id} not found"), 404

    if quote.rating > 1:
        quote.rating -= 1
        db.session.commit()
    
    return convert_quotes(quote), 200

if __name__ == "__main__":
    app.run(debug=True)