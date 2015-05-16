#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of resourcealchemy.
# https://github.com/TomNeyland/resource-alchemy

# Licensed under the TBD license:
# http://www.opensource.org/licenses/TBD-license
# Copyright (c) 2015, Tom Neyland <tcneyland+github@gmail.com>

from preggy import expect

from resourcealchemy import Resource, Field
from tests.base import TestCase, TestObj


class ResourceTestCase(TestCase):

    class Person(TestObj):
        pass

    class PersonResource(Resource):
        first_name = Field(read_only=False)
        last_name = Field(read_only=False)
        nick = Field('nickname', read_only=False)

    def setUp(self):

        self.person1_raw = dict(first_name='Ferdinand', last_name='Magellen', nick='Ferd')


    def test_decode_person1(self):

        person1 = ResourceTestCase.Person()
        person1 = ResourceTestCase.PersonResource.decode(person1, self.person1_raw)

        expect(person1.first_name).to_equal('Ferdinand')
        expect(person1.last_name).to_equal('Magellen')
        expect(person1.nickname).to_equal('Ferd')

        return person1

    def test_encode_person1(self):
        person1 = self.test_decode_person1()

        encoded_person1 = ResourceTestCase.PersonResource.encode(person1)
        expect(encoded_person1).to_be_like(self.person1_raw)

        return encoded_person1


class JsonResourceTestCase(ResourceTestCase):

    def test_json_decode_person1(self):
        pass

    def test_json_encode_person1(self):
        pass
