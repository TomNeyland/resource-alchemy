from unittest import TestCase as PythonTestCase
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from resource_alchemy import Resource, Field, Relationship, ListRelationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

# an Engine, which the Session will use for connection resources
engine = create_engine('sqlite://')

# create a configured "Session" class
Session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = Session.query_property()


class User(Base):

    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    age = Column(Integer, nullable=False)
    savings = Column(Float, nullable=False)
    is_active = Column(Boolean)
    biography = Column(Text)

    orders = relationship('Order')


class UserResource(Resource):

    user_id = Field(description='The user id')
    first_name = Field(required=True, read_only=False)
    last_name = Field(read_only=False)
    age = Field()
    savings = Field()
    is_active = Field()
    biography = Field()

    orders = ListRelationship(lambda: OrderResource, title='Orders', read_only=True)

    class meta:
        model = User
        description = 'User resource'


class Order(Base):
    __tablename__ = 'orders'

    order_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    user = relationship('User', back_populates='orders')


class OrderResource(Resource):

    order_id = Field()
    user = Relationship(lambda: UserResource, description='the user')

    class meta:
        model = Order


class TestCase(PythonTestCase):

    def setUp(self):
        with session_scope():
            Base.metadata.create_all(engine)

    def tearDown(self):
        with session_scope():
            Base.metadata.drop_all(engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
