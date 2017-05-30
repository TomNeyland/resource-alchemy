from preggy import expect

from resource_alchemy import RestResource, Field

from ..base import TestCase, User, session_scope


class UserResource(RestResource):

    age = Field(read_only=False)
    is_active = Field(required=True)

    class meta:
        model = User
        includes = ('user_id', 'first_name', 'last_name',)


class IncludesUserResourceTestCase(TestCase):

    def setUp(self):
        super(IncludesUserResourceTestCase, self).setUp()

        with session_scope() as session:
            user = User(user_id=1, first_name='Test', last_name='User', age=18, savings=100.0, is_active=True)
            user2 = User(
                user_id=2,
                first_name='Test',
                last_name='User2',
                age=19,
                savings=200.0,
                is_active=False)
            session.add(user)
            session.add(user2)
            session.commit()

    def test_resource_get_one(self):

        user = UserResource.get_one(1)

        expect(user['user_id']).to_equal(1)
        expect(user['first_name']).to_equal('Test')
        expect(user['last_name']).to_equal('User')
        expect(user['age']).to_equal(18)
        expect(user['is_active']).to_equal(True)

    def test_resource_get_list(self):
        users = UserResource.get_list()

        expect(len(users)).to_equal(2)

        expect(users[0]).to_equal(dict(user_id=1, first_name='Test', last_name='User', age=18, is_active=True))
        expect(users[1]).to_equal(dict(user_id=2, first_name='Test', last_name='User2', age=19, is_active=False))

    def test_existing_fields(self):
        expect(UserResource.age.read_only).to_equal(False)
        expect(UserResource.is_active.required).to_equal(True)
