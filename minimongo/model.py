# -*- coding: utf-8 -*-

__all__ = ('Collection', 'Index', 'Model')

import re

from pymongo import Connection
from pymongo.collection import Collection as PyMongoCollection
from pymongo.dbref import DBRef
from pymongo.errors import InvalidId
from pymongo.objectid import ObjectId


class Collection(PyMongoCollection):
    """A Wrapper around pymongo.Collection that provides the same
    functionality, but stores the document class of the Collection we're
    working with, so that find and find_one can return the right classes."""

    def __init__(self, *args, **kwargs):
        self._document_class = kwargs.pop("document_class")
        super(Collection, self).__init__(*args, **kwargs)

    def find(self, *args, **kwargs):
        """same as pymongo.Collection.find except it returns the right
        document type."""
        kwargs["as_class"] = self._document_class
        return super(Collection, self).find(*args, **kwargs)

    def find_one(self, spec_or_id, *args, **kwargs):
        """same as pymongo.Collection.find_one except it returns the right
        document type"""
        kwargs["as_class"] = self._document_class

        # The problem with default find_one() method is that, it fails
        # to fetch a document, if a given id is a string. So, we try to
        # convert `spec_or_id` to ObjectId and fail silently on exception.
        if isinstance(spec_or_id, basestring):
            try:
                spec_or_id = ObjectId(spec_or_id)
            except InvalidId:
                pass

        return super(Collection, self).find_one(spec_or_id, *args, **kwargs)

    def from_dbref(self, dbref):
        """Given a DBRef, return an instance of this type."""
        # Making sure a given DBRef points to a proper collection
        # and database.
        if not dbref.collection == self.name:
            raise ValueError("DBRef points to an invalid collection.")
        elif dbref.database and not dbref.database == self.database.name:
            raise ValueError("DBRef points to an invalid database.")
        else:
            return self.find_one(dbref.id)


class Options(object):
    """Container class for model metadata."""
    host = None
    port = None
    indices = ()
    database = None
    collection = None
    collection_class = Collection

    def __init__(self, meta):
        self.__dict__.update(meta.__dict__)

    @classmethod
    def configure(cls, **defaults):
        """Updates class-level defaults for Options container."""
        for attr, value in defaults.iteritems():
            setattr(cls, attr, value)


class ModelBase(type):
    """Metaclass for all models."""

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
            meta = getattr(new_class, "Meta")
        except AttributeError:
            raise TypeError("Model %r is missing Meta declaration." % name)
        else:
            delattr(new_class, "Meta")  # Won't need the original metadata
                                        # container anymore.

        options = Options(meta)
        options.collection = options.collection or to_underscore(name)

        if not (options.host and options.port and options.database):
            raise Exception(
                "Model %r improperly configured: %s %s %s" %
                (name, options.host, options.port, options.database)
            )

        # Checking connection pool for an existing connection.
        hostport = options.host, options.port
        if hostport in mcs._connections:
            connection = mcs._connections[hostport]
        else:
            connection = mcs._connections[hostport] = Connection(*hostport)

        new_class._meta = options
        new_class.database = connection[options.database]
        new_class.collection = options.collection_class(
            new_class.database, options.collection, document_class=new_class)

        # Generating required indices.
        # Note: this will result in calls to pymongo's ensure_index()
        # method at import time, so import all your models up front.
        new_class.auto_index()

        return new_class

    def auto_index(mcs):
        """Build all indices for this collection specified in the definition
        of the Model."""
        for index in mcs._meta.indices:
            index.ensure(mcs.collection)


class Model(dict):
    """Base class for all Minimongo objects.  Derive from this class."""
    __metaclass__ = ModelBase

    def __init__(self, initial_value=None):
        if initial_value:
            super(Model, self).__init__(initial_value)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           super(Model, self).__str__())

    def __unicode__(self):
        return str(self).decode("utf-8")

    # These lines make this object behave both like a dict (x['y']) and like
    # an object (x.y).  We have to translate from KeyError to AttributeError
    # since model.undefined raises a KeyError and model['undefined'] raises
    # a KeyError.  we don't ever want __getattr__ to raise a KeyError, so we
    # "translate" them below:
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError as excn:
            raise AttributeError(excn)

    def __setattr__(self, attr, value):
        try:
            self[attr] = value
        except KeyError as excn:
            raise AttributeError(excn)

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as excn:
            raise AttributeError(excn)

    def dbref(self):
        """Returns a DBRef for the current object."""
        if not hasattr(self, '_id'):
            self._id = ObjectId()
        elif self._id is None:
            # FIXME: is this really an issue?
            raise ValueError("ObjectId must be valid to create a DBRef.")

        return DBRef(collection=self._meta.collection,
                     database=self._meta.database,
                     id=self._id)

    def remove(self):
        """Delete this object."""
        return self.collection.remove(self._id)

    def mongo_update(self):
        """Update (write) this object."""
        self.collection.update({'_id': self._id}, self)
        return self

    def save(self, *args, **kwargs):
        """Save this Model to it's mongo collection"""
        self.collection.save(self, *args, **kwargs)
        return self


class Index(object):
    """Just a simple container class holding the arguments that are passed
    directly to pymongo's ensure_index method."""
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def __eq__(self, other):
        """Two indices are equal, when the have equal arguments."""
        return self.__dict__ == other.__dict__

    def ensure(self, collection):
        """Call pymongo's ensure_index on the given collection with the
        stored args."""
        return collection.ensure_index(*self._args, **self._kwargs)


# Utils.

def to_underscore(string):
    """Converts a given string from CamelCase to under_score.

    >>> to_underscore("FooBar")
    'foo_bar'
    """
    return re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", string).lower()
