#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of resource_alchemy.
# https://github.com/TomNeyland/resource-alchemy

# Licensed under the TBD license:
# http://www.opensource.org/licenses/TBD-license
# Copyright (c) 2015, Tom Neyland <tcneyland+github@gmail.com>

from preggy import expect
import resource_alchemy
from tests.base import TestCase


class ExportsTestCase(TestCase):

    def test_resource_alchemy_exports(self):

        # Base Resource Classes
        expect(resource_alchemy.ModelResource).not_to_be_null()
        expect(resource_alchemy.ApiResource).not_to_be_null()

        # Basic fields
        expect(resource_alchemy.Field).not_to_be_null()
        expect(resource_alchemy.Relationship).not_to_be_null()
        expect(resource_alchemy.ListRelationship).not_to_be_null()
        expect(resource_alchemy.FilteredListRelationship).not_to_be_null()
        expect(resource_alchemy.DateTimeField).not_to_be_null()
        expect(resource_alchemy.ApiResource).not_to_be_null()
        expect(resource_alchemy.IntervalField).not_to_be_null()

        # Basic Authorization Types
        expect(resource_alchemy.FullAuthorization).not_to_be_null()
        expect(resource_alchemy.ReadOnlyAuthorization).not_to_be_null()
        expect(resource_alchemy.PropertyAuthorization).not_to_be_null()
        expect(resource_alchemy.NoAuthorization).not_to_be_null()
