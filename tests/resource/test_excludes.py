from preggy import expect

from resource_alchemy import RestResource, Field

from ..base import TestCase, User, session_scope


class UserResource(RestResource):

    age = Field(read_only=False)
    is_active = Field(required=True)

    class meta:
        model = User
        excludes = ('user_id', 'first_name', 'last_name',)


class ExcludesUserResourceTestCase(TestCase):

    def setUp(self):
        super(ExcludesUserResourceTestCase, self).setUp()

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

        expect(user['age']).to_equal(18)
        expect(user['savings']).to_equal(100.0)
        expect(user['is_active']).to_equal(True)
        expect(user['biography']).to_equal(None)

    def test_resource_get_list(self):
        users = UserResource.get_list()

        expect(len(users)).to_equal(2)

        expect(users[0]).to_equal(dict(age=18, savings=100.0, is_active=True, biography=None))
        expect(users[1]).to_equal(dict(age=19, savings=200.0, is_active=False, biography=None))

    def test_existing_fields(self):
        expect(UserResource.age.read_only).to_equal(False)
        expect(UserResource.is_active.required).to_equal(True)
