import logging

import datetime
from datetime import datetime, date
import dateutil.parser

from .exceptions import NotAuthorized

from sqlalchemy.ext.hybrid import hybrid_method


log = logging.getLogger(__name__)


def get_json_schema_type(column):
    field_type = None
    python_type = getattr(column.type, 'python_type')

    if python_type is list:
        field_type = 'array'
    elif python_type is bool:
        field_type = 'boolean'
    elif python_type is int:
        field_type = 'integer'
    elif python_type is float:
        field_type = 'number'
    elif python_type is dict:
        field_type = 'object'
    elif python_type is str:
        field_type = 'string'
    elif python_type is date:
        field_type = 'date-time'
    elif python_type is datetime:
        field_type = 'date-time'
    elif python_type is None:
        pass
    else:
        raise ValueError('Unknown type %s' % python_type)

    schema = {
        'type': field_type,
    }

    if column.nullable is True:
        schema = {
            'anyOf': [schema, {
                'type': 'null'
            }]
        }

    return schema


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

    def __init__(self, name=None, key=None, read_only=True, required=False, authorization=None, **kwargs):
        self.name = name
        self.read_only = read_only
        self.required = required
        self.options = kwargs

        if read_only:
            self.authorization = ReadOnlyFieldAuthorization
        elif authorization:
            self.authorization = authorization
        else:
            self.authorization = FullFieldAuthorization

    def encode(self, *args, **kwargs):
        return self.from_obj(*args, **kwargs)

    def decode(self, *args, **kwargs):
        return self.to_obj(*args, **kwargs)

    def json_schema(self):
        field_attribute = getattr(self.model, self.name)
        field_column = field_attribute.property.columns[0]

        schema = {}

        schema.update(get_json_schema_type(field_column))

        if 'description' in self.options:
            schema['description'] = self.options['description']

        if self.read_only:
            schema['readonly'] = self.read_only

        return schema

    def to_obj(self, obj, value, **obj_data):
        """Convert obj_data to a Python object."""

        current_value = getattr(obj, self.name, None)

        if value != current_value:
            if self.authorization.can_update(obj, value, **obj_data):
                log.debug('setting %s.%s = %s', obj, self.name, value)
                setattr(obj, self.name, value)
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
                if all(col.key in value for col in self.resource._primary_keys()):
                    # has all PKs, its an update
                    related_obj = self.resource.apply_transformers(value, 'update_obj')
                else:
                    # its a create
                    related_obj = self.resource.apply_transformers(value, 'create_obj')

            log.debug('setattr(%s, %s, %s)', obj, self.name, related_obj)
            setattr(obj, self.name, related_obj)

    def from_obj(self, obj, **kwargs):

        if not self.authorization.can_read(obj, **kwargs):
            return None

        related_obj = getattr(obj, self.name, None)

        if related_obj:
            return self.resource.serialize(related_obj)


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
            return [self.resource.serialize(related_obj)
                    for related_obj in related_objs]
        else:
            return []

    def to_obj(self, obj, values, **obj_data):

        if self.authorization.can_update(obj, values, **obj_data):
            # log.debug('setting %s.%s = %s', obj, self.name, values)
            related_objs = []
            for value in values:
                if all(col.key in value for col in self.resource._primary_keys()):
                    # has all PKs, its an update
                    related_obj = self.resource.apply_transformers(value, 'update_obj')
                else:
                    # its a create
                    related_obj = self.resource.apply_transformers(value, 'create_obj')

                related_objs.append(related_obj)

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

            return [self.resource.serialize(related_obj)
                    for related_obj in related_objs]
        else:
            return []
