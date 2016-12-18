from preggy import expect

from ..base import TestCase, UserResource


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

    def test_relationship(self):
        orders_schema = self.json_schema['items']['properties']['orders']

        expect(orders_schema).not_to_be_null()
        expect(orders_schema['type']).to_equal('array')
