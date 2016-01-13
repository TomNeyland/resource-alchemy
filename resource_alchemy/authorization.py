import math
import re
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from .search import search


def convert_name(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class NoAuthorization(object):

    @classmethod
    def can_create(cls, obj_data, **kwargs):
        return False

    @classmethod
    def can_read(cls, obj, **kwargs):
        return False

    @classmethod
    def can_update(cls, obj, **kwargs):
        return False

    @classmethod
    def can_delete(cls, obj, **kwargs):
        return False


class FullAuthorization(object):

    @classmethod
    def can_create(cls, obj_data, **kwargs):
        return True

    @classmethod
    def can_read(cls, obj, **kwargs):
        return True

    @classmethod
    def can_update(cls, obj, **kwargs):
        return True

    @classmethod
    def can_delete(cls, obj, **kwargs):
        return True


class UserManagedAuthorization(object):

    @classmethod
    def can_create(cls, obj_data, **kwargs):
        return True

    @classmethod
    def can_read(cls, obj, **kwargs):
        return obj.can_read()

    @classmethod
    def can_update(cls, obj, **kwargs):
        return obj.can_update()

    @classmethod
    def can_delete(cls, obj, **kwargs):
        return obj.can_delete()


class ReadOnlyAuthorization(object):

    @classmethod
    def can_create(cls, obj_data, **kwargs):
        return False

    @classmethod
    def can_read(cls, obj, **kwargs):
        return True

    @classmethod
    def can_update(cls, obj, **kwargs):
        return False

    @classmethod
    def can_delete(cls, obj, **kwargs):
        return False


class PropertyAuthorization(object):

    """Defer authorization responsibility to a property."""

    def __init__(self, property_name):
        self.property_name = property_name

    def can_create(self, obj, **kwargs):
        return True

    def can_read(self, obj, **kwargs):
        return getattr(obj, self.property_name).can_read(**kwargs)

    def can_update(self, obj, **kwargs):
        return getattr(obj, self.property_name).can_update(**kwargs)

    def can_delete(self, obj, **kwargs):
        return getattr(obj, self.property_name).can_delete(**kwargs)
