import logging
import pytz

import datetime
import dateutil.parser
import time

from .exceptions import NotAuthorized

from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import (undefer, joinedload, subqueryload, joinedload_all,
                            subqueryload_all, dynamic_loader)


log = logging.getLogger(__name__)


def isalambda(v):
    return isinstance(v, type(lambda: None)) and v.__name__ == '<lambda>'


class ReadOnlyFieldAuthorization(object):

    @hybrid_method
    def can_read(self, obj, **kwargs):
        return True

    @hybrid_method
    def can_update(self, obj, value, **obj_data):
        return False


class FullFieldAuthorization(object):

    @hybrid_method
    def can_read(self, obj, **kwargs):
        return True

    @hybrid_method
    def can_update(self, obj, value, **obj_data):
        return True


class Field(object):

    def __init__(self, name=None, key=None, read_only=True, required=False, authorization=None, json_type='string'):
        if name:
            assert isinstance(name, basestring), "Field name must be a string"

        self.name = name
        self.required = required
        self.json_type = json_type

        if authorization:
            self.authorization = authorization
        elif read_only:
            self.authorization = ReadOnlyFieldAuthorization
        elif not read_only:
            self.authorization = FullFieldAuthorization

    def encode(self, *args, **kwargs):
        return self.from_obj(*args, **kwargs)

    def decode(self, *args, **kwargs):
        return self.to_obj(*args, **kwargs)

    def json_schema(self):

        schema = {
            'type': self.json_type,
            'options': {
                'alchemyType': self.__class__.__name__
            }
        }

        return schema

    def to_obj(self, obj, value, **obj_data):
        """Convert obj_data to a Python object."""

        current_value = getattr(obj, self.name, None)

        if value != current_value:
            if self.authorization.can_update(obj, value, **obj_data):
                log.debug('setting %s.%s = %s', obj, self.name, value)
                return value
            else:
                raise NotAuthorized("Not authorized to update '%s'" % self.name)

    def from_obj(self, obj, **kwargs):
        """Convert a Python object to something we can serialize to JSON."""

        if not self.authorization.can_read(obj, **kwargs):
            return None

        return getattr(obj, self.name)


class DateTimeField(Field):

    def from_obj(self, obj, **kwargs):

        value = super(DateTimeField, self).from_obj(obj, **kwargs)

        if value is not None:
            value = value.isoformat()

        return value

    def to_obj(self, obj, value, **obj_data):

        if value is not None:
            value = dateutil.parser.parse(value)

        return super(DateTimeField, self).to_obj(obj, value, **obj_data)


class IntervalField(Field):

    def __init__(self, *args, **kwargs):
        super(IntervalField, self).__init__(*args, **kwargs)

    def to_obj(self, obj, value, **obj_data):
        if value is not None:
            value = datetime.timedelta(seconds=value)

        return super(IntervalField, self).to_obj(obj, value, **obj_data)

    def from_obj(self, obj, **kwargs):
        value = super(IntervalField, self).from_obj(obj, **kwargs)
        if value is not None:
            return value.total_seconds()
        else:
            return value


class Relationship(Field):

    def __init__(self, resource, **kwargs):
        self._resource = resource
        super(Relationship, self).__init__(**kwargs)

    @property
    def resource(self):
        if isalambda(self._resource):
            return self._resource()
        else:
            return self._resource

    def to_obj(self, obj, value, **obj_data):

        if self.authorization.can_update(obj, value, **obj_data):
            if value is None:
                related_obj = None
            else:
                related_obj = self.resource.to_obj(value)

            log.debug('disabled: setattr(%s, %s, %s)' % obj, self.name, related_obj)
            # setattr(obj, self.name, related_obj)

    def from_obj(self, obj, **kwargs):

        if not self.authorization.can_read(obj, **kwargs):
            return None

        related_obj = getattr(obj, self.name, None)

        if related_obj:
            return self.resource.to_dict(related_obj)


class ListRelationship(Field):

    def __init__(self, resource, **kwargs):
        self._resource = resource
        super(ListRelationship, self).__init__(**kwargs)

    @property
    def resource(self):
        if isalambda(self._resource):
            return self._resource()
        else:
            return self._resource

    def from_obj(self, obj, **kwargs):

        if not self.authorization.can_read(obj, **kwargs):
            return None

        related_objs = getattr(obj, self.name, None)

        if related_objs:
            return [self.resource.to_dict(related_obj)
                    for related_obj in related_objs]
        else:
            return []

    def to_obj(self, obj, values, **obj_data):

        if self.authorization.can_update(obj, values, **obj_data):
            # log.debug('setting %s.%s = %s', obj, self.name, values)
            related_objs = [self.resource.to_obj(value)
                            for value in values]

            setattr(obj, self.name, related_objs)


class FilteredListRelationship(ListRelationship):

    def __init__(self, resource, list_filter=None, **kwargs):
        self.list_filter = list_filter
        super(FilteredListRelationship, self).__init__(resource, **kwargs)

    def from_obj(self, obj, **kwargs):

        if not self.authorization.can_read(obj, **kwargs):
            return None

        related_objs = getattr(obj, self.name, None)

        if related_objs:
            if self.list_filter:
                related_objs = filter(self.list_filter, related_objs)

            return [self.resource.to_dict(related_obj)
                    for related_obj in related_objs]
        else:
            return []
