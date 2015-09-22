import math
import re
import ujson as json
# from flask.ext.login import current_user

from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

# from panel.core.database import session
# from panel.common.models import Base
# from panel.jsonrpc.exc import NotAuthorizedError

from .search import search
from .fields import Field, Relationship, ListRelationship
from .authorization import NoAuthorization, FullAuthorization, ReadOnlyAuthorization, PropertyAuthorization


def convert_name(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class ModelResourceMetaclass(type):

    authorization = NoAuthorization
    query_options = ()
    method_options = {}
    results_per_page = 100

    def __new__(cls, name, bases, attrs):

        cls.setup_resource(name, bases, attrs)

        new_cls = type.__new__(cls, name, bases, attrs)

        return new_cls

    @classmethod
    def setup_resource(cls, name, bases, attrs):

        meta_cls = attrs.pop('meta', None)

        if meta_cls:
            meta_bases = (meta_cls, ModelResourceMetaclass)
        else:
            meta_bases = (ModelResourceMetaclass,)

        meta_cls = type(name + 'Metadata', meta_bases, {})

        resource_name = getattr(meta_cls, 'name', None)

        if resource_name is None:
            model = getattr(meta_cls, 'model', None)
            if model:
                resource_name = convert_name(model.__name__)
            else:
                resource_name = ''

        meta_cls.name = resource_name

        attrs['meta'] = meta_cls

        for attr, value in attrs.iteritems():

            if isinstance(value, Field):
                value.key = attr
                value.name = value.name or attr
            elif isinstance(value, type) and issubclass(value, Field):
                field = value()
                field.key = attr
                field.name = attr
                attrs[attr] = field


class Resource(object):

    __metaclass__ = ModelResourceMetaclass

    @classmethod
    def fields(cls):
        for attr, value in cls.__dict__.iteritems():
            if isinstance(value, (Field)) and not isinstance(value, (Relationship, ListRelationship)):
                yield (attr, value)

    @classmethod
    def relationships(cls):
        for attr, value in cls.__dict__.iteritems():
            if isinstance(value, (Relationship, ListRelationship)):
                yield (attr, value)

    @classmethod
    def encode(cls, obj, **options):

        result = {}

        for attr, field in cls.fields():
            result[attr] = field.encode(obj)

        for attr, relationship in cls.relationships():
            result[attr] = relationship.encode(obj)

        return result

    @classmethod
    def decode(cls, obj, obj_data, **options):

        for attr, field in cls.fields():
            raw_value = obj_data.get(attr)
            value = field.decode(obj, raw_value, **options)
            setattr(obj, field.name, value)

        for attr, relationship in cls.relationships():
            raw_value = obj_data.get(attr)
            value = relationship.decode(obj, raw_value, **options)
            setattr(obj, relationship.name, value)

        return obj

    @classmethod
    def json_schema(cls):

        schema = {
            'type': 'object',
            'properties': {},
            'options': {
                'alchemyResource': cls.__name__
            }
        }

        for attr, field in cls.fields():
            field_schema = field.json_schema()
            schema['properties'][attr] = field_schema

        return schema


class JsonResource(object):

    @classmethod
    def json_encode(cls, obj, **options):
        obj_data = cls.encode(obj, **options)
        obj_json = json.dumps(obj_data)
        return obj_json

    @classmethod
    def json_decode(cls, obj, obj_data, **options):
        obj = cls.decode(obj, obj_data, **options)
        return obj


class CRUDResource(object):

    __metaclass__ = ModelResourceMetaclass

    class meta:
        pass

    # create
    @classmethod
    def create(cls, resource_data, **options):
        pass

    # read
    @classmethod
    def read(cls, resource_id, **options):
        pass

    # update
    @classmethod
    def update(cls, resource_data, **options):
        pass

    # delete
    @classmethod
    def delete(cls, resource_id, **options):
        pass


class RESTResource(object):

    __metaclass__ = ModelResourceMetaclass

    class meta:
        pass

    # create
    @classmethod
    def post(cls, resource_data, **options):
        pass

    # read
    @classmethod
    def get(cls, resource_id, **options):
        pass

    # update
    @classmethod
    def patch(cls, resource_data, **options):
        pass

    # delete
    @classmethod
    def delete(cls, resource_id, **options):
        pass


class ModelResource(object):

    __metaclass__ = ModelResourceMetaclass

    class meta:
        pass

    @classmethod
    def to_dict(cls, obj_or_pk, **kwargs):

        if not isinstance(obj_or_pk, Base):
            obj = cls.get_obj(obj_or_pk)
        else:
            obj = obj_or_pk

        if cls.meta.authorization:
            if not cls.meta.authorization.can_read(obj, **kwargs):
                raise NotAuthorizedError('%s: %s Not authorized to read %s' %
                                         (cls.meta.authorization, current_user, obj))

        result = {}

        for key, field in cls._fields():
            result[key] = field.from_obj(obj)

        return result

    @classmethod
    def to_obj(cls, obj_data):

        Model = cls.meta.model

        model_pks = Model._pk_attrs

        created = False

        obj = None

        if all(pk in obj_data for pk in model_pks):
            # if we have all the pks, we do an update
            obj_pks = tuple(obj_data[pk] for pk in model_pks)

            obj = cls.query('get').get(obj_pks)

            if obj and not cls.meta.authorization.can_read(obj):
                raise NotAuthorizedError('Not authorized to read object')

        if obj == None:
            if cls.meta.authorization.can_create(obj_data):
                obj = Model()
                created = True
            else:
                raise NotAuthorizedError('Not authorized to create object')

        if created is True or cls.meta.authorization.can_update(obj):
            for key, field in cls._fields():
                # TODO: Better checking of field setting on creating
                if key in obj_data:
                    value = obj_data[key]
                    # Ignore fields that aren't writable
                    if field.authorization.can_update(obj, value, **obj_data):
                        field.to_obj(obj, value, **obj_data)
        elif not created:
            raise NotAuthorizedError('Not authorized to edit object')

        return obj

    @classmethod
    def update_obj(cls, obj_data):
        return

    @classmethod
    def get_obj(cls, obj_pk):

        if not isinstance(obj_pk, tuple):
            obj_pk = (obj_pk,)

        Model = cls.meta.model

        query = cls.query('get')

        obj = query.get(obj_pk)

        return obj

    @classmethod
    def search(cls, search_params={}, query=None):

        result = search(session, cls.meta.model, search_params, query=query)
#
        return result

    @classmethod
    def query(cls, mode='search'):

        Model = cls.meta.model

        if mode is 'get':
            query = cls.get_query
        elif mode is 'search':
            query = cls.search_query
        elif mode is 'update':
            query = cls.update_query
        elif mode is 'delete':
            query = cls.update_query

        options = cls.meta.query_options

        if options:
            query = query.options(*options)

        return query

    @hybrid_property
    def base_query(cls):
        return cls.meta.model.query

    @hybrid_property
    def get_query(cls):
        return cls.base_query

    @hybrid_property
    def search_query(cls):
        return cls.base_query

    @hybrid_property
    def update_query(cls):
        return cls.base_query

    @hybrid_property
    def delete_query(cls):
        return cls.base_query

    @classmethod
    def _fields(cls):
        for attr, value in cls.__dict__.iteritems():
            if isinstance(value, Field):
                yield (attr, value)


class ApiResource(ModelResource):

    @classmethod
    def pre_get(cls, pk):
        return pk

    @classmethod
    def get(cls, pk):

        pk = cls.pre_get(pk)

        obj = cls.get_obj(pk)
        obj_data = cls.to_dict(obj)

        obj_data = cls.post_get(obj_data, obj, pk)

        return obj_data

    @classmethod
    def post_get(cls, obj_data, obj, pk):
        return obj_data

    @classmethod
    def pre_create(cls, obj_data):
        return obj_data

    @classmethod
    def create(cls, obj_data):

        obj_data = cls.pre_create(obj_data)

        obj = super(ApiResource, cls).to_obj(obj_data)

        obj = cls.post_create(obj, obj_data)

        session.add(obj)
        # session.commit()
#
        cls.post_create_commit(obj)

        return cls.to_dict(obj)

    @classmethod
    def post_create(cls, obj, obj_data):
        return obj

    @classmethod
    def post_create_commit(cls, obj):
        """Called after `obj` has been created and committed to the SQLAlchemy session."""
        pass

    @classmethod
    def pre_update(cls, obj_data):
        return obj_data

    @classmethod
    def update(cls, obj_data):

        obj_data = cls.pre_update(obj_data)

        obj = super(ApiResource, cls).to_obj(obj_data)

        obj = cls.post_update(obj, obj_data)

        session.add(obj)
        session.commit()

        obj_pk = tuple(getattr(obj, pk) for pk in obj.__class__._pk_attrs)
        session.expunge(obj)
        obj = cls.get_obj(obj_pk)

        return cls.to_dict(obj)

    @classmethod
    def post_update(cls, obj, obj_data):
        return obj

    @classmethod
    def delete(cls, pk):
        raise NotImplemented("Delete does not have a default implementation")

    @classmethod
    def search(cls, search_params={}):

        search_result = super(ApiResource, cls).search(search_params=search_params,
                                                       query=cls.query('search'))
        result_count = search_result.count()

        page = search_params.get('page', 1)
        results_per_page = search_params.get('results_per_page') or cls.meta.results_per_page
        pages = int(math.ceil(float(result_count) / results_per_page))

        if search_params.get('single'):
            result = search_result.one()
            response = cls.to_dict(result)
        else:
            slice_start = (page - 1) * results_per_page
            slice_end = slice_start + results_per_page

            result = [cls.to_dict(obj) for obj in search_result[slice_start:slice_end]]

            response = {
                'num_results': result_count,
                'total_pages': pages,
                'page': page,
                'objects': result
            }

        return response