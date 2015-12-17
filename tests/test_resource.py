#!/usr/bin/env python# -*- coding: utf-8 -*-

# This file is part of resource_alchemy.
# https://github.com/TomNeyland/resource-alchemy

# Licensed under the TBD license:
# http://www.opensource.org/licenses/TBD-license
# Copyright (c) 2015, Tom Neyland <tcneyland+github@gmail.com>

from preggy import expect

from resource_alchemy import Resource, Field
from resource_alchemy.resource import RestResource
from tests.base import TestCase, UserResource, User, session_scope
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean


class JSONSchemaTestCase(TestCase):

    def setUp(self):
        super(JSONSchemaTestCase, self).setUp()
        self.json_schema = UserResource._schema()

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


class RestUserResource(RestResource):

        user_id = Field()
        first_name = Field()
        last_name = Field()

        class meta:
            model = User


class RestUserResourceTestCase(TestCase):

    def setUp(self):
        super(RestUserResourceTestCase, self).setUp()

        with session_scope() as session:
            user = User(user_id=1, first_name='Test', last_name='User', age=18, savings=100.0)
            user2 = User(user_id=2, first_name='Test', last_name='User2', age=19, savings=200.0)
            session.add(user)
            session.add(user2)
            session.commit()

    def test_resource_get_one(self):

        user = RestUserResource.get_one(1)

        expect(user['user_id']).to_equal(1)
        expect(user['first_name']).to_equal('Test')
        expect(user['last_name']).to_equal('User')

    def test_resource_get_list(self):
        users = RestUserResource.get_list()

        expect(len(users)).to_equal(2)

        expect(users[0]).to_equal(dict(user_id=1, first_name='Test', last_name='User'))
        expect(users[1]).to_equal(dict(user_id=2, first_name='Test', last_name='User2'))
