from preggy import expect

from resource_alchemy.resource import RestResource

from ..base import TestCase, User, session_scope


class UserResource(RestResource):

    class meta:
        model = User
        includes = ('user_id', 'first_name', 'last_name',)


class IncludesUserResourceTestCase(TestCase):

    def setUp(self):
        super(IncludesUserResourceTestCase, self).setUp()

        with session_scope() as session:
            user = User(user_id=1, first_name='Test', last_name='User', age=18, savings=100.0)
            user2 = User(user_id=2, first_name='Test', last_name='User2', age=19, savings=200.0)
            session.add(user)
            session.add(user2)
            session.commit()

    def test_resource_get_one(self):

        user = UserResource.get_one(1)

        expect(user['user_id']).to_equal(1)
        expect(user['first_name']).to_equal('Test')
        expect(user['last_name']).to_equal('User')

    def test_resource_get_list(self):
        users = UserResource.get_list()

        expect(len(users)).to_equal(2)

        expect(users[0]).to_equal(dict(user_id=1, first_name='Test', last_name='User'))
        expect(users[1]).to_equal(dict(user_id=2, first_name='Test', last_name='User2'))
