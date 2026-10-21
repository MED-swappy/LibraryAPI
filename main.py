import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Integer, String, ForeignKey
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

DATABASE_URL = "os.environ["DATABASE_URL"]"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False , autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AuthorCreate(BaseModel):
    name : str

class BookCreate(BaseModel):
    name: str
    author_id: int





class Base(DeclarativeBase):
    pass

class Author(Base):
    __tablename__= "authors"

    id : Mapped[int] = mapped_column(Integer, primary_key=True , autoincrement=True)
    name : Mapped[str] = mapped_column(String, nullable=False)

    books : Mapped[list["Book"]] = relationship(back_populates="author")

class Book(Base):

    __tablename__= "books"
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True , autoincrement=True)
    name : Mapped[str] = mapped_column(String, nullable=False)

    author_id : Mapped[int] = mapped_column(Integer, ForeignKey("authors.id"))
    author : Mapped["Author"] = relationship(back_populates="books")

Base.metadata.create_all(engine)



app = FastAPI()

@app.get("/")
def root():
    return {"message" : "Welcome to my Library API"}


@app.get("/authors")
def get_authors(db : Session = Depends(get_db)):
    authors = db.query(Author).all()
    return authors


@app.get("/books")
def get_books(db : Session = Depends(get_db)):
    book = db.query(Book).all()
    return book


@app.get("/books/{id}")
def get_books_by_id(id: int, db : Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == id).first()
    if book is None:
     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                         detail="Book does not exist")
    return book

@app.get("/authors/{id}/books")
def get_authors_by_id(id: int, db : Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == id).first()
    if author is None :
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                     detail="Author does not exist")
    return author.books

@app.post("/authors")
def post_author(author : AuthorCreate, db : Session = Depends(get_db)):
      new_author = Author(
          name = author.name
      )

      db.add(new_author)
      db.commit()
      db.refresh(new_author)

      return new_author

     

@app.post("/books")
def post_book(book : BookCreate, db : Session = Depends(get_db)):

    new_book = Book(
        name = book.name,
        author_id = book.author_id
    )

    db.add(new_book)
    
    try:
        db.commit()
        db.refresh(new_book)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="Author does not exist")        
    return new_book


@app.put("/authors/{author_id}")
def update_author(
    author_id: int,
    author: AuthorCreate,
    db: Session = Depends(get_db)
):
    existing_author = db.query(Author).filter(
        Author.id == author_id
    ).first()

    if existing_author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    existing_author.name = author.name

    db.commit()
    db.refresh(existing_author)

    return existing_author


@app.put("/books/{book_id}")
def update_book(
    book_id: int,
    book: BookCreate,
    db: Session = Depends(get_db)
):
    existing_book = db.query(Book).filter(
        Book.id == book_id
    ).first()

    if existing_book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    existing_book.name = book.name
    existing_book.author_id = book.author_id

    try:
        db.commit()
        db.refresh(existing_book)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Author does not exist"
        )

    return existing_book


@app.delete("/books/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    existing_book = db.query(Book).filter(
        Book.id == book_id
    ).all()

    if existing_book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    db.delete(existing_book)
    db.commit()

    return {"message": "Book deleted"}


@app.delete("/authors/{author_id}")
def delete_author(
    author_id: int,
    db: Session = Depends(get_db)
):
    existing_author = db.query(Author).filter(
        Author.id == author_id
    ).first()

    existing_books = db.query(Book).filter(
            Book.author_id == author_id
        ).all()

    if existing_author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    if existing_books is not None:
        db.delete(existing_books)
        db.commit()
        db.refresh(existing_author)
    db.delete(existing_author)
    db.commit()

    return {"message": "Author deleted (His/Her books got deleted automatically)"}