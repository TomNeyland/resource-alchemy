#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of resourcealchemy.
# https://github.com/TomNeyland/resource-alchemy

# Licensed under the TBD license:
# http://www.opensource.org/licenses/TBD-license
# Copyright (c) 2015, Tom Neyland <tcneyland+github@gmail.com>

from preggy import expect
import resourcealchemy
from tests.base import TestCase


class ExportsTestCase(TestCase):

    def test_resourcealchemy_exports(self):

        # Base Resource Classes
        expect(resourcealchemy.ModelResource).not_to_be_null()
        expect(resourcealchemy.ApiResource).not_to_be_null()

        # Basic fields
        expect(resourcealchemy.Field).not_to_be_null()
        expect(resourcealchemy.Relationship).not_to_be_null()
        expect(resourcealchemy.ListRelationship).not_to_be_null()
        expect(resourcealchemy.FilteredListRelationship).not_to_be_null()
        expect(resourcealchemy.DateTimeField).not_to_be_null()
        expect(resourcealchemy.ApiResource).not_to_be_null()
        expect(resourcealchemy.IntervalField).not_to_be_null()

        # Basic Authorization Types
        expect(resourcealchemy.FullAuthorization).not_to_be_null()
        expect(resourcealchemy.ReadOnlyAuthorization).not_to_be_null()
        expect(resourcealchemy.PropertyAuthorization).not_to_be_null()
        expect(resourcealchemy.NoAuthorization).not_to_be_null()