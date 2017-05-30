import math
import re

from flask import jsonify, request
from flask.views import MethodView, MethodViewType, View
from functools import reduce
from sqlalchemy import inspect
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from .exceptions import NotAuthorized, BaseException
from .fields import Field, Relationship, ListRelationship
from .authorization import FullAuthorization


def convert_name(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def resource_route(arg=None, **kwargs):

    if hasattr(arg, '__call__'):
        func = arg
        route = '%s/' % func.func_name
        relative = True
        func._resource_route = {'route': route, 'relative': relative}
        func = classmethod(func)
        return func
    else:
        def make_route(func):
            if arg and arg.startswith('/'):
                relative = False
            else:
                relative = True
            func._resource_route = {'route': arg or func.func_name, 'relative': relative}
            func._resource_route.update(kwargs)
            func = classmethod(func)
            return func
        return make_route


class ModelTransformer(object):

    @classmethod
    def serialize_one(cls, resource, obj, **kwargs):

        if resource.meta.authorization:
            if not resource.meta.authorization.can_read(obj, **kwargs):
                raise NotAuthorized('Not authorized to read object')

        result = {}
        for key, field in resource._fields():
            result[key] = field.from_obj(obj)

        for key, relationship in resource._relationships():
            result[key] = relationship.encode(obj)

        return result

    @classmethod
    def serialize_list(cls, resource, objs, **kwargs):
        return [cls.serialize_one(resource, obj, **kwargs) for obj in objs]

    @classmethod
    def create_obj(cls, resource, obj_data):
        if resource.meta.authorization.can_create(obj_data):
            obj = resource.meta.model()
            obj = cls.to_obj(resource, obj, obj_data)
        return obj

    @classmethod
    def update_obj(cls, resource, obj_data):

        model_pks = (col.key for col in resource._primary_keys())

        obj_pks = tuple(obj_data[pk] for pk in model_pks)

        obj = resource.get_query.get(obj_pks)

        if obj and not resource.meta.authorization.can_read(obj):
            raise NotAuthorized('Not authorized to read object')

        if resource.meta.authorization.can_update(obj):
            return cls.to_obj(resource, obj, obj_data)
        else:
            raise NotAuthorized('Not authorized to edit object')

    @classmethod
    def to_obj(cls, resource, obj, obj_data):

        for key, field in resource._fields():
            # TODO: Better checking of field setting on creating
            if key in obj_data:
                value = obj_data[key]
                # Ignore fields that aren't writable
                if field.authorization.can_update(obj, value, **obj_data):
                    print key, field, obj, value, obj_data
                    field.to_obj(obj, value, **obj_data)

        for key, field in resource._relationships():
            # TODO: Better checking of field setting on creating
            if key in obj_data:
                value = obj_data[key]
                # Ignore fields that aren't writable
                if field.authorization.can_update(obj, value, **obj_data):
                    field.to_obj(obj, value, **obj_data)

        return obj

    @classmethod
    def deserialize_one(cls, resource, obj=None, **kwargs):
        pass

    @classmethod
    def deserialize_list(cls, resource, objs, **kwargs):
        return [cls.deserialize_one(resource, obj, **kwargs) for obj in objs]


class ModelResourceMetaclass(type):

    authorization = FullAuthorization
    query_options = ()
    method_options = {}
    results_per_page = 100
    transformers = [ModelTransformer]
    decorators = []

    def __new__(cls, name, bases, attrs):

        cls.setup_resource(name, bases, attrs)
        new_cls = super(ModelResourceMetaclass, cls).__new__(cls, name, bases, attrs)

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

        model = getattr(meta_cls, 'model', None)

        includes = getattr(meta_cls, 'includes', None)
        excludes = getattr(meta_cls, 'excludes', None)

        if resource_name is None:
            if model:
                resource_name = convert_name(model.__name__)
            else:
                resource_name = ''

        meta_cls.name = resource_name

        attrs['meta'] = meta_cls

        if includes and excludes:
            raise Exception(
                'Cannot define both includes and excludes for {}. Please remove one.'.format(resource_name))
        elif includes is not None:
            cls.process_includes(includes, attrs)
        elif excludes is not None:
            if not model:
                raise Exception('A model is required when using excludes for {}'.format(resource_name))

            cls.process_excludes(excludes, attrs, model)

        for attr, value in attrs.iteritems():

            if isinstance(value, Field):
                value.key = attr
                value.name = value.name or attr

                if model:
                    value.model = model
            elif isinstance(value, type) and issubclass(value, Field):
                field = value()
                field.key = attr
                field.name = attr
                attrs[attr] = field

                if model:
                    value.model = model

    @classmethod
    def process_includes(cls, includes, attrs):
        for value in includes:
            # don't override existing declared Fields
            if value not in attrs:
                attrs[value] = Field()

    @classmethod
    def process_excludes(cls, excludes, attrs, model):
        mapper = inspect(model)

        for column in mapper.columns:
            key = column.key
            # don't override existing declared Fields
            if key not in excludes and key not in attrs:
                attrs[key] = Field()


class Resource(object):

    __metaclass__ = ModelResourceMetaclass

    @classmethod
    def _fields(cls):
        for attr, value in cls.__dict__.iteritems():
            if isinstance(value, (Field)) and not isinstance(value, (Relationship, ListRelationship)):
                yield (attr, value)

    @classmethod
    def _primary_keys(cls):
        return inspect(cls.meta.model).primary_key

    @classmethod
    def _extra_routes(cls):
        for attr, value in cls.__dict__.iteritems():
            if hasattr(value, '__func__') and hasattr(value.__func__, '_resource_route'):
                func = getattr(cls, attr)
                options = dict(**value.__func__._resource_route)
                if cls.meta.decorators:
                    func = reduce(lambda func, decorator: decorator(func), cls.meta.decorators, func)

                options['view_func'] = func

                relative = options.pop('relative')
                if relative:
                    resource_name = cls.meta.name
                    resource_url = '/%s/' % resource_name
                    options['route'] = '%s%s/' % (resource_url, options['route'])

                yield options

    @classmethod
    def _relationships(cls):
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
    def _schema(cls):

        schema = {
            'id': cls.meta.name,
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'items': {
                'properties': {},
            }
        }

        if hasattr(cls.meta, 'description'):
            schema['description'] = cls.meta.description

        for attr, field in cls._fields():
            field_schema = field.json_schema()
            schema['items']['properties'][attr] = field_schema

        for attr, relationship in cls._relationships():
            relationship_schema = relationship.json_schema()
            schema['items']['properties'][attr] = relationship_schema

        required_fields = [field.key for attr, field in cls._fields() if field.required is True]

        if required_fields:
            schema['required'] = required_fields

        return schema

    @classmethod
    def _json_schema(cls):
        return jsonify(cls._schema())


class ModelResource(object):

    __metaclass__ = ModelResourceMetaclass

    class meta:
        pass

    @hybrid_method
    def to_dict(cls, obj_or_pk, **kwargs):

        # TODO(will): Check to see if this is an object, an int or a string
        if not isinstance(obj_or_pk, cls.meta.model):
            obj = cls.get_obj(obj_or_pk)
        else:
            obj = obj_or_pk

        if cls.meta.authorization:
            if not cls.meta.authorization.can_read(obj, **kwargs):
                raise NotAuthorized('Not authorized to read object')

        result = {}

        for key, field in cls._fields():
            result[key] = field.from_obj(obj)

        return result

    @hybrid_method
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
                raise NotAuthorized('Not authorized to read object')

        if obj is None:
            if cls.meta.authorization.can_create(obj_data):
                obj = Model()
                created = True
            else:
                raise NotAuthorized('Not authorized to create object')

        if created is True or cls.meta.authorization.can_update(obj):
            for key, field in cls._fields():
                # TODO: Better checking of field setting on creating
                if key in obj_data:
                    value = obj_data[key]
                    # Ignore fields that aren't writable
                    if field.authorization.can_update(obj, value, **obj_data):
                        field.to_obj(obj, value, **obj_data)
        elif not created:
            raise NotAuthorized('Not authorized to edit object')

        return obj

    @hybrid_method
    def update_obj(cls, obj_data):
        return

    @hybrid_method
    def get_obj(cls, obj_pk):

        if not isinstance(obj_pk, tuple):
            obj_pk = (obj_pk,)

        query = cls.query('get')

        obj = query.get(obj_pk)

        return obj

    @hybrid_method
    def search(cls, search_params={}, query=None):
        # TODO: what do we want to do here?
        raise NotImplemented()

    @hybrid_method
    def query(cls, mode='search'):

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

    @hybrid_method
    def _fields(cls):
        for attr, value in cls.__dict__.iteritems():
            if isinstance(value, Field):
                yield (attr, value)


class ApiResource(ModelResource):

    @hybrid_method
    def pre_get(cls, pk):
        return pk

    @hybrid_method
    def get(cls, pk):

        pk = cls.pre_get(pk)

        obj = cls.get_obj(pk)
        obj_data = cls.to_dict(obj)

        obj_data = cls.post_get(obj_data, obj, pk)

        return obj_data

    @hybrid_method
    def post_get(cls, obj_data, obj, pk):
        return obj_data

    @hybrid_method
    def pre_create(cls, obj_data):
        return obj_data

    @hybrid_method
    def create(cls, obj_data):

        obj_data = cls.pre_create(obj_data)

        obj = super(ApiResource, cls).to_obj(obj_data)

        obj = cls.post_create(obj, obj_data)

        return cls.to_dict(obj)

    @hybrid_method
    def post_create(cls, obj, obj_data):
        return obj

    @hybrid_method
    def pre_update(cls, obj_data):
        return obj_data

    @hybrid_method
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

    @hybrid_method
    def post_update(cls, obj, obj_data):
        return obj

    @hybrid_method
    def delete(cls, pk):
        raise NotImplemented("Delete does not have a default implementation")

    @hybrid_method
    def search(cls, search_params={}):

        search_result = search(None, cls.meta.model, search_params,
                               query=cls.query('search'))
        result_count = search_result.count()

        page = search_params.get('page', 1)
        results_per_page = search_params.get(
            'results_per_page') or cls.meta.results_per_page
        pages = int(math.ceil(float(result_count) / results_per_page))

        if search_params.get('single'):
            result = search_result.one()
            response = cls.to_dict(result)
        else:
            slice_start = (page - 1) * results_per_page
            slice_end = slice_start + results_per_page

            result = [cls.to_dict(obj)
                      for obj in search_result[slice_start:slice_end]]

            response = {
                'num_results': result_count,
                'total_pages': pages,
                'page': page,
                'objects': result
            }

        return response

    @hybrid_method
    def register_resource(cls, app):

        name_suffix = cls.meta.name or convert_name(cls.meta.model.__name__)

        @app.route('/%s/' % name_suffix, methods=['GET', 'POST'])
        def base_handler():

            if request.method is 'GET':
                return cls.search()
            elif request.method is 'POST':
                return cls.create()

        for func_name in ('get', 'update', 'search', 'create', 'delete'):
            name = '/%s/%s' % (name_suffix, func_name)
            func = getattr(cls, func_name)
            register_func = app.route(name)
            register_func(func)


class RestResourceMetaclass(ModelResourceMetaclass, MethodViewType, View):
    pass


class RestResource(MethodView, Resource):

    __metaclass__ = RestResourceMetaclass

    class meta:
        pass

    @hybrid_method
    def get(self, pk=None):
        if pk is None:
            # return a list of users
            result = dict(objects=self.get_list())
        else:
            pk = int(pk)
            result = self.get_one(pk)

        if result is None:
            return '', 404

        return jsonify(result)

    @hybrid_method
    def post(self):
        obj_data = request.json
        result = self.apply_transformers(obj_data, 'create_obj')
        session = self.meta.model.query.session  # oh god why
        session.add(result)
        session.commit()
        return jsonify(self.serialize(result)), 201

    @hybrid_method
    def delete(self, pk):
        pass

    @hybrid_method
    def put(self, pk):
        obj_data = request.json
        result = self.apply_transformers(obj_data, 'update_obj')
        session = self.meta.model.query.session  # oh god why
        session.merge(result)
        session.commit()
        return jsonify(self.serialize(result)), 200

    @hybrid_method
    def get_one(cls, pk, **kwargs):

        if not isinstance(pk, tuple):
            pk = (pk,)

        query = cls.get_query
        obj = query.get(pk)

        if obj is not None:
            obj_data = cls.apply_transformers(obj, 'serialize_one', **kwargs)
        else:
            obj_data = None

        return obj_data

    @hybrid_method
    def get_list(cls, **kwargs):
        objs = cls.search_query
        return cls.apply_transformers(objs, 'serialize_list', **kwargs)

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

    @hybrid_method
    def serialize(cls, obj, **kwargs):
        if isinstance(obj, (list, tuple, set)):
            return cls.apply_transformers(obj, 'serialize_list', **kwargs)
        else:
            return cls.apply_transformers(obj, 'serialize_one')

    @hybrid_method
    def deserialize(cls, obj, **kwargs):
        if isinstance(obj, (list, tuple, set)):
            return cls.apply_transformers(obj, 'serialize_list', **kwargs)
        else:
            return cls.apply_transformers(obj, 'serialize_one')

    @hybrid_method
    def apply_transformers(cls, obj, transform_func, **kwargs):
        for transformer in cls.meta.transformers:
            if hasattr(transformer, transform_func):
                transform = getattr(transformer, transform_func)
                obj = transform(cls, obj, **kwargs)
        return obj

    @classmethod
    def register_error_handlers(cls, app):

        def handle_alchemy_exception(error):
            response = jsonify(error.to_dict())
            response.status_code = error.status_code
            return response

        register_handler = app.errorhandler(BaseException)
        register_handler(handle_alchemy_exception)

        app.__resource_alchemy_errorhandlers_registered = True

    @hybrid_method
    def register_api(cls, app, pk='id', pk_type='int'):

        if not hasattr(app, '__resource_alchemy_errorhandlers_registered'):
            cls.register_error_handlers(app)

        resource_name = cls.meta.name
        resource_url = '/%s/' % resource_name

        view_func = cls.as_view(resource_name)

        if cls.meta.decorators:
            view_func = reduce(lambda func, decorator: decorator(func), cls.meta.decorators, view_func)

        app.add_url_rule(resource_url,
                         view_func=view_func,
                         methods=['GET', ])

        app.add_url_rule(resource_url,
                         view_func=view_func,
                         methods=['POST', ])

        app.add_url_rule('%s<pk>' % (resource_url),
                         view_func=view_func,
                         methods=['GET', 'PUT', 'DELETE'])

        register_func = app.route('%sschema/' % resource_url, endpoint='%s_schema' %
                                  resource_name, methods=['GET'])(cls._json_schema)

        for extra_route in cls._extra_routes():
            route = extra_route.pop('route')
            app.add_url_rule(route, **extra_route)

        return view_func
