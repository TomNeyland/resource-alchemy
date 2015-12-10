from preggy import expect

from tests.base import TestCase, UserResource


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
