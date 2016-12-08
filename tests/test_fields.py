from preggy import expect

from tests.base import TestCase, UserResource, OrderResource


class FieldTestCase(TestCase):

    def test_field_description(self):
        field = UserResource.user_id.json_schema()

        expect(field['description']).to_equal('The user id')

    def test_field_readonly(self):
        field = UserResource.user_id.json_schema()

        expect(field['readonly']).to_be_true()

    def test_field_required(self):
        # 'required' should not appear on the field
        err = expect.error_to_happen(KeyError)
        field = UserResource.first_name.json_schema()

        with err:
            field['required']

    def test_float_field(self):
        field = UserResource.savings.json_schema()

        expect(field).to_equal({
            'readonly': True,
            'type': 'number'
        })

    def test_integer_field(self):
        field = UserResource.age.json_schema()

        expect(field).to_equal({
            'readonly': True,
            'type': 'integer'
        })

    def test_nullable_boolean(self):
        field = UserResource.is_active.json_schema()

        expect(field).to_equal({
            'readonly': True,
            'anyOf': [{
                'type': 'boolean'
            }, {
                'type': 'null'
            }]})


class RelationshipTestCase(TestCase):

    def test_json_schema(self):
        relationship = OrderResource.user.json_schema()

        expect(relationship).to_equal({
            'type': 'object',
            'properties': {
                'first_name': {
                    'anyOf': [{
                        'type': 'string'
                    }, {
                        'type': 'null'
                    }]
                },
                'last_name': {
                    'anyOf': [{
                        'type': 'string'
                    }, {
                        'type': 'null'
                    }]
                },
                'user_id': {
                    'readonly': True,
                    'type': 'integer',
                    'description': 'The user id'
                },
                'age': {
                    'readonly': True,
                    'type': 'integer'
                },
                'is_active': {
                    'readonly': True,
                    'anyOf': [{
                        'type': 'boolean'
                    }, {
                        'type': 'null'
                    }]
                },
                'savings': {
                    'readonly': True,
                    'type': 'number'
                },
                'biography': {
                    'readonly': True,
                    'anyOf': [{
                        'type': 'string'
                    }, {
                        'type': 'null'
                    }]
                }
            },
            'readonly': True,
            'description': 'the user'
        })


class ListRelationshipTestCase(TestCase):

    def test_json_schema(self):
        relationship = UserResource.orders.json_schema()

        expect(relationship).to_equal({
            'items': {
                'properties': {
                    'order_id': {
                        'readonly': True,
                        'type': 'integer'
                    }
                },
                'title': 'Orders',
                'type': 'object'
            },
            'readonly': True,
            'type': 'array'
        })
