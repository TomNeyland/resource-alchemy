#!/usr/bin/env python# -*- coding: utf-8 -*-

# This file is part of resource_alchemy.
# https://github.com/TomNeyland/resource-alchemy

# Licensed under the TBD license:
# http://www.opensource.org/licenses/TBD-license
# Copyright (c) 2015, Tom Neyland <tcneyland+github@gmail.com>

from preggy import expect

from resource_alchemy import Resource, Field
from tests.base import TestCase, TestObj, UserResource
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean

Base = declarative_base()


class User(Base):

    __tablename__ = 'users'

    email = Column(String(255), primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', deferrable=True, initially='DEFERRED'))
    google_token = Column(Text)
    active = Column(Boolean(), nullable=False, default=True)

    # employee = db.relationship('Employee')

    def get_id(self):
        return self.email


# class ResourceTestCase(TestCase):

#     class Person(TestObj):
#         pass

#     class PersonResource(Resource):
#         first_name = Field(read_only=False)
#         last_name = Field(read_only=False)
#         nick = Field('nickname', read_only=False)

#     def setUp(self):
#         self.person1_raw = dict(first_name='Ferdinand', last_name='Magellen', nick='Ferd')

#     def test_decode_person1(self):

#         person1 = ResourceTestCase.Person()
#         person1 = ResourceTestCase.PersonResource.decode(person1, self.person1_raw)

#         expect(person1.first_name).to_equal('Ferdinand')
#         expect(person1.last_name).to_equal('Magellen')
#         expect(person1.nickname).to_equal('Ferd')

#         return person1

    # def test_json_encode_person1(self):
#         person1 = self.test_decode_person1()

#         encoded_person1 = ResourceTestCase.PersonResource.encode(person1)
#         expect(encoded_person1).to_be_like(self.person1_raw)

#         return encoded_person1


class JSONSchemaTestCase(TestCase):

    def setUp(self):
        self.json_schema = UserResource.json_schema()

    def test_schema_type(self):
        expect(self.json_schema['type']).to_equal('object')

    def test_schema_url(self):
        expect(self.json_schema['$schema']).to_equal('http://json-schema.org/draft-04/schema#')

    def test_schema_id(self):
        expect(self.json_schema['id']).to_equal('user')

    def test_required_fields(self):
        expect(self.json_schema['required']).to_length(1)
        expect(self.json_schema['required'][0]).to_equal('first_name')

    def test_items(self):
        expect(self.json_schema['items']).not_to_be_null()
        expect(self.json_schema['items']['properties']).not_to_be_null()

    def test_description(self):
        expect(self.json_schema['description']).to_equal('User resource')


# class JSONResourceTestCase(ResourceTestCase):

#     def test_json_decode_person1(self):
#         pass

#     def test_json_encode_person1(self):
#         pass


# class RestResourceTestCase(TestCase):

#      class PersonResource(Resource):
#         first_name = Field(read_only=False)
#         last_name = Field(read_only=False)
#         nick = Field('nickname', read_only=False)
