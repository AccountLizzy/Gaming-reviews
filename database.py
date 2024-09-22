from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import Session, mapped_column, Mapped, relationship
from sqlalchemy.ext.declarative import declarative_base
import requests
import os
from flask_login import UserMixin
from typing import List

# Ensure there is directory
if not os.path.exists('instance'):
    os.makedirs('instance')

engine = create_engine('sqlite:///instance/blogs.db')
session = Session(bind=engine)

Base = declarative_base()


class User(UserMixin, Base):
    __tablename__ = 'User'
    id:Mapped[int] = mapped_column(primary_key=True)
    email:Mapped[str] = mapped_column(nullable=False, unique=True)
    password:Mapped[str] = mapped_column(nullable=False)
    name:Mapped[str] = mapped_column(nullable=False)

    # One-to-Many relationship: A user can have many blogs and comments
    blogs:Mapped[List['Blogs']] = relationship('Blogs', back_populates='author')
    comments:Mapped[List['Comments']] = relationship('Comments', back_populates='author')


class Comments(Base):
    __tablename__ = 'Comments'
    id:Mapped[int] = mapped_column(primary_key=True)
    text:Mapped[str] = mapped_column(nullable=False)

    # Many-to-One
    author_id:Mapped[int] = mapped_column(ForeignKey('User.id'), nullable=False)

    # Many-to-One relationship: Each comment is written by one user
    blog_id:Mapped[int] = mapped_column(ForeignKey('Blogs.id'), nullable=False)

    # Relationship to link to a user
    author:Mapped[User] = relationship('User', back_populates='comments')


class Blogs(Base):
    __tablename__ = 'Blogs'
    id:Mapped[int] = mapped_column(primary_key=True)
    body:Mapped[str] = mapped_column(nullable=False)
    image:Mapped[str]
    title:Mapped[str] = mapped_column(nullable=False)
    subtitle:Mapped[str] = mapped_column(nullable=False)
    date:Mapped[str] = mapped_column(nullable=False)

    # Many-to-One relationship: Each blog is written by one user
    author_id:Mapped[int] = mapped_column(ForeignKey('User.id'), nullable=False)

    # Relationship to link the blog to a user. The "blogs" refers to the blogs property in the User class.
    author:Mapped[User] = relationship('User', back_populates='blogs')


Base.metadata.create_all(bind=engine)



# ------------- API --------------- #

# response = requests.get(url='https://api.npoint.io/80b78fa396df0123eade').json()
# if response:
#     for blog in response:
#         new_blog = Blogs(
#             body = blog['body'],
#             image = blog['image'],
#             title = blog['title'],
#             subtitle = blog['subtitle'],
#             date = 'August 5, 2024',
#             author = 'Lizzy and ChatGPT'
#         )
#         session.add(new_blog)
#     session.commit()
#     session.close()
# else:
#     print('Oh no, error at handling database!')
