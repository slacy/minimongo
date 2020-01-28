# -*- coding: utf-8 -*-
from __future__ import absolute_import

import copy
import re

import six
from bson import DBRef, ObjectId
from pymongo import MongoClient as Connection

from .collection import DummyCollection
from .exceptions import DoesNotExist
from .options import _Options


class ModelBase(type):
    """Metaclass for all models.

    .. todo:: add Meta inheritance -- so that missing attributes are
              populated from the parrent's Meta if any.
    """

    # A very rudimentary connection pool.
    _connections = {}

    def __new__(mcs, name, bases, attrs):
        new_class = super(ModelBase,
                          mcs).__new__(mcs, name, bases, attrs)
        parents = [b for b in bases if isinstance(b, ModelBase)]
        if not parents:
            # If this isn't a subclass of Model, don't do anything special.
            return new_class

        # Processing Model metadata.
        try:
            meta = getattr(new_class, 'Meta')
        except AttributeError:
            meta = None
        else:
            # Won't need the original metadata container anymore.
            delattr(new_class, 'Meta')

        options = _Options(meta)
        options.collection = options.collection or to_underscore(name)

        if options.interface:
            new_class._meta = None
            new_class.database = None
            new_class.collection = DummyCollection
            return new_class

        if not (options.host and options.port and options.database):
            raise Exception(
                'Model %r improperly configured: %s %s %s' % (
                    name, options.host, options.port, options.database))

        # Checking connection pool for an existing connection.
        hostport = options.host, options.port
        if hostport in mcs._connections:
            connection = mcs._connections[hostport]
        else:
            # _connect=False option
            # creates :class:`pymongo.connection.Connection` object without
            # establishing connection. It's required if there is no running
            # mongodb at this time but we want to create :class:`Model`.
            # False option doesn't work with pymongo 2.4 using master/slave
            # cluster
            connection = Connection(*hostport)
            mcs._connections[hostport] = connection

        new_class._meta = options
        new_class.connection = connection
        new_class.database = connection[options.database]
        if options.username and options.password:
            new_class.database.authenticate(options.username, options.password)
        new_class.collection = options.collection_class(
            new_class.database, options.collection, document_class=new_class)

        if options.auto_index:
            new_class.auto_index()   # Generating required indices.

        return new_class

    def auto_index(mcs):
        """Builds all indices, listed in model's Meta class.

           >>> class SomeModel(Model)
           ...     class Meta:
           ...         indices = (
           ...             Index('foo'),
           ...         )

        .. note:: this will result in calls to
                  :meth:`pymongo.collection.Collection.ensure_index`
                  method at import time, so import all your models up
                  front.
        """
        for index in mcs._meta.indices:
            index.ensure(mcs.collection)


class AttrDict(dict):
    def __init__(self, initial=None, **kwargs):
        # Make sure that during initialization, that we recursively apply
        # AttrDict.  Maybe this could be better done with the builtin
        # defaultdict?
        if initial:
            for key, value in six.iteritems(initial):
                # Can't just say self[k] = v here b/c of recursion.
                self.__setitem__(key, value)

        # Process the other arguments (assume they are also default values).
        # This is the same behavior as the regular dict constructor.
        for key, value in six.iteritems(kwargs):
            self.__setitem__(key, value)

        super(AttrDict, self).__init__()

    # These lines make this object behave both like a dict (x['y']) and like
    # an object (x.y).  We have to translate from KeyError to AttributeError
    # since model.undefined raises a KeyError and model['undefined'] raises
    # a KeyError.  we don't ever want __getattr__ to raise a KeyError, so we
    # 'translate' them below:
    def __getattr__(self, attr):
        try:
            return super(AttrDict, self).__getitem__(attr)
        except KeyError as excn:
            raise AttributeError(excn)

    def __setattr__(self, attr, value):
        try:
            # Okay to set directly here, because we're not recursing.
            self[attr] = value
        except KeyError as excn:
            raise AttributeError(excn)

    def __delattr__(self, key):
        try:
            return super(AttrDict, self).__delitem__(key)
        except KeyError as excn:
            raise AttributeError(excn)

    def __setitem__(self, key, value):
        # Coerce all nested dict-valued fields into AttrDicts
        new_value = value
        if isinstance(value, dict):
            new_value = AttrDict(value)
        return super(AttrDict, self).__setitem__(key, new_value)


@six.python_2_unicode_compatible
@six.add_metaclass(ModelBase)
class Model(AttrDict):
    """Base class for all Minimongo objects.

    >>> class Foo(Model):
    ...     class Meta:
    ...         database = 'somewhere'
    ...         indices = (
    ...             Index('bar', unique=True),
    ...         )
    ...
    >>> foo = Foo(bar=42)
    >>> foo
    {'bar': 42}
    >>> foo.bar == 42
    True
    """

    DoesNotExist = DoesNotExist

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           super(Model, self).__str__())

    def __setitem__(self, key, value):
        # Go through the defined list of field mappers.  If the fild
        # matches, then modify the field value by calling the function in
        # the mapper.  Mapped fields must have a different type than their
        # counterpart, otherwise they'll be mapped more than once as they
        # come back in from a find() or find_one() call.
        if self._meta and self._meta.field_map:
            for matcher, mogrify in self._meta.field_map:
                if matcher(key, value):
                    new_value = mogrify(value)
                    if type(new_value) == type(value):
                        raise Exception(
                            "Field mapper didn't change field type!")
                    value = new_value

        super(Model, self).__setitem__(key, value)

    def dbref(self, with_database=True, **kwargs):
        """Returns a DBRef for the current object.

        If `with_database` is False, the resulting :class:`pymongo.dbref.DBRef`
        won't have a :attr:`database` field.

        Any other parameters will be passed to the DBRef constructor, as per
        the mongo specs.
        """
        if not hasattr(self, '_id'):
            self._id = ObjectId()

        database = self._meta.database if with_database else None
        return DBRef(self._meta.collection, self._id, database, **kwargs)

    def remove(self):
        """Remove this object from the database."""
        return self.collection.remove(self._id)

    def mongo_update(self, values=None, **kwargs):
        """Update database data with object data."""
        # Allow to update external values as well as the model itself
        if not values:
            # Remove the _id and wrap self into a $set statement.
            self_copy = copy.copy(self)
            del self_copy._id
            values = {'$set': self_copy}
        self.collection.update({'_id': self._id}, values, **kwargs)

        return self

    def save(self, *args, **kwargs):
        """Save this object to it's mongo collection."""
        self.collection.save(self, *args, **kwargs)
        return self

    def load(self, fields=None, **kwargs):
        """Allow partial loading of a document.
        :attr:fields is a dictionary as per the pymongo specs

        self.collection.find_one( self._id, fields={'name': 1} )

        """
        values = self.collection.find_one({'_id': self._id},
                                          fields=fields, **kwargs)
        # Merge the loaded values with whatever is currently in self.
        self.update(values)
        return self

    @classmethod
    def get(cls, **kwargs):
        """
        Return a single instance of the Model.
        Will throw a `DoesNotExist` exception if an instance does not exist.
        """

        instance = cls.collection.find_one(kwargs)
        if not instance:
            raise cls.DoesNotExist()

        return cls(**instance)

# Utils.

def to_underscore(string):
    """Converts a given string from CamelCase to under_score.

    >>> to_underscore('FooBar')
    'foo_bar'
    """
    new_string = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', string)
    new_string = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', new_string)
    return new_string.lower()
