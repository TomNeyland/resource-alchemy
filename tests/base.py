#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of resource_alchemy.
# https://github.com/TomNeyland/resource-alchemy

# Licensed under the TBD license:
# http://www.opensource.org/licenses/TBD-license
# Copyright (c) 2015, Tom Neyland <tcneyland+github@gmail.com>

from unittest import TestCase as PythonTestCase
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean, Text, Integer, Float

from resource_alchemy import Resource, Field

Base = declarative_base()


class User(Base):

    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    age = Column(Integer, nullable=False)
    savings = Column(Float, nullable=False)
    is_active = Column(Boolean)
    biography = Column(Text)


class UserResource(Resource):

    user_id = Field(description='The user id')
    first_name = Field(required=True, read_only=False)
    last_name = Field(read_only=False)
    age = Field()
    savings = Field()
    is_active = Field()
    biography = Field()

    class meta:
        model = User
        description = 'User resource'


class TestCase(PythonTestCase):
    pass


class TestObj(object):

    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)
