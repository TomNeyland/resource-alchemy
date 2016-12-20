# Resource Alchemy

[![Build Status](https://travis-ci.org/TomNeyland/resource-alchemy.svg?branch=master)](https://travis-ci.org/TomNeyland/resource-alchemy)
[![RTD Status](https://readthedocs.org/projects/resource-alchemy/badge/?version=latest)](http://resource-alchemy.readthedocs.org/en/latest/)
[![Coverage Status](https://coveralls.io/repos/TomNeyland/resource-alchemy/badge.svg?branch=master)](https://coveralls.io/r/TomNeyland/resource-alchemy?branch=master)

Easily generate Resources with [Flask](http://flask.pocoo.org/) and [SQLAlchemy](http://www.sqlalchemy.org/)

## Getting Started

```
pip install resource-alchemy
```

## Example Usage

```python
# models.py
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

engine = sa.create_engine('sqlite://')
Session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = Session.query_property()


# Create some models
class User(Base):
    __tablename__ = 'users'

    user_id = sa.Column(sa.Integer, primary_key=True)
    first_name = sa.Column(sa.String)
    last_name = sa.Column(sa.String)
    age = sa.Column(sa.Integer, nullable=False)
    savings = sa.Column(sa.Float, nullable=False)
    is_active = sa.Column(sa.Boolean)
    biography = sa.Column(sa.Text)

    orders = relationship('Order')


class Order(Base):
    __tablename__ = 'orders'

    order_id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.user_id'))
    user = relationship('User', back_populates='orders')
```

```python
# resource.py
from resource_alchemy import RestResource, Field, Relationship, ListRelationship

from .models import User, Order

class UserResource(RestResource):
    user_id = Field()
    first_name = Field(required=True, read_only=False)
    last_name = Field(read_only=False)
    age = Field()
    savings = Field()
    is_active = Field()
    biography = Field()

    orders = ListRelationship(lambda: OrderResource, read_only=True)

    class meta:
      model = User
      name = 'users'
      description = 'User resource'


class OrderResource(RestResource):
    order_id = Field()
    user = Relationship(lambda: UserResource)

    class meta:
        model = Order
        name = 'orders'
```

The above will generate the following endpoints:

```
GET    /users/
POST   /users/
GET    /users/<pk>/
PUT    /users/<pk>/
DELETE /users/<pk>/
```

It will also automatically generate the JSON schema for the resource:

```
GET /users/schema/
```

```json
{
  "description": "User resource",
  "items": {
    "properties": {
      "first_name": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ]
      },
      "last_name": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ]
      },
      "user_id": {
        "readonly": true,
        "type": "integer",
        "description": "The user id"
      },
      "age": {
        "readonly": true,
        "type": "integer"
      },
      "is_active": {
        "readonly": true,
        "anyOf": [
          {
            "type": "boolean"
          },
          {
            "type": "null"
          }
        ]
      },
      "savings": {
        "readonly": true,
        "type": "number"
      },
      "orders": {
        "items": {
          "type": "object",
          "properties": {
            "order_id": {
              "readonly": true,
              "type": "integer"
            }
          },
          "title": "Orders"
        },
        "readonly": true,
        "type": "array"
      },
      "biography": {
        "readonly": true,
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ]
      }
    }
  },
  "required": [
    "first_name"
  ],
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "id": "user"
}
```

## Resource Authorization

Authorization for resources is specified at the `meta` level.

```python
from resource_alchemy import RestResource, Field, FullAuthorization

from .models import User


class UserResource(RestResource):

    user_id = Field()
    first_name = Field()

    class meta:
        model = User
        authorization = FullAuthorization
```

With `FullAuthorization` the consumer can perform any of the CRUD methods.

The other available authorization strategies are:

```python
NoAuthorization
UserManagedAuthorization
ReadOnlyAuthorization
PropertyAuthorization
```

### Creating your own authorization

There are two classes that can be used as base classes:

```python
from resource_alchemy import FullAuthorization, NoAuthorization
```

The methods available for overriding are:

```
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
```

## Field Authorization

Authorization can also be provided at the `Field` level.

```python
from resource_alchemy import RestResource, Field, FullFieldAuthorization

from .models import User


class UserResource(RestResource):

    user_id = Field()
    first_name = Field(authorization=FullFieldAuthorization)

    class meta:
        model = User
```

You can also provide the `read_only` argument to `Field`:

```python
name = Field(read_only=False)
```

By default, all fields are `read_only`.

### Creating your own Field authorization

Much like `Resource` level authorization, you can create your own `Field` level authorization by using the following classes as a base:

```python
from resource_alchemy import ReadOnlyFieldAuthorization, FullFieldAuthorization
```

Or by creating your own class with the following interface. Ensure they are [`hybrid_method`s](http://docs.sqlalchemy.org/en/latest/orm/extensions/hybrid.html).

```python
from sqlalchemy.ext.hybrid import hybrid_method

class MyFieldAuth(object):
    @hybrid_method
    def can_read(self, obj, **kwargs):
        return True

    @hybrid_method
    def can_update(self, obj, value, **obj_data):
        return True
```

## Includes and Excludes

You can add an `includes` or `excludes` property on the `meta` class as a shorthand way of declaring `Field`s

Given the `User` model above:

```python
from resource_alchemy import RestResource

from .models import User


class UserResource(RestResource):
    class meta:
        model = User
        includes = ('user_id', 'first_name', 'last_name',)
```

is equivalent to:

```python
from resource_alchemy import RestResource, Field

from .models import User


class UserResource(RestResource):
    user_id = Field()
    first_name = Field()
    last_name = Field()

    class meta:
        model = User
```

`excludes` is exactly what you would expect:

```python
from resource_alchemy import RestResource

from .models import User


class UserResource(RestResource):
    class meta:
        model = User
        excludes = ('user_id', 'first_name', 'last_name',)
```

and is equivalent to:

```python
from resource_alchemy import RestResource, Field

from .models import User


class UserResource(RestResource):
    age = Field()
    savings = Field()
    is_active = Field()
    biography = Field()

    class meta:
        model = User
```

It is important to note that __only primitive primitives will be added as `Field`s__. Relationships must still be declared.
