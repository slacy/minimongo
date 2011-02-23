#!/bin/python
import pymongo
import pymongo.collection
import pymongo.database
import pymongo.dbref
import pymongo.objectid
from minimongo import config


class Collection(pymongo.collection.Collection):
    """A Wrapper around pymongo.Collection that provides the same
    functionality, but stores the document class of the Collection we're
    working with, so that find and find_one can return the right classes."""
    def __init__(self, database, name, options=None,
                 create=False, **kwargs):
        self._document_class = kwargs['document_class']
        del kwargs['document_class']
        return super(Collection, self).__init__(
            database, name, options, create, **kwargs)

    def find(self, *args, **kwargs):
        """same as pymongo.Collection.find except it returns the right
        document type."""
        kwargs['as_class'] = self._document_class
        return super(Collection, self).find(*args, **kwargs)

    def find_one(self, *args, **kwargs):
        """same as pymongo.Collection.find_one except it returns the right
        document type"""
        kwargs['as_class'] = self._document_class
        return super(Collection, self).find_one(*args, **kwargs)

    def from_dbref(self, dbref):
        """Given a DBRef, return an instance of this type."""
        return self.find_one({'_id': dbref.id})


class MongoCollection(object):
    """Container class for connection to db & mongo collection settings."""
    def __init__(self, host=None, port=None, database=None, collection=None,
                 placeholder=False):
        if placeholder:
            if host or port or database or collection:
                raise Exception("Placeholder configs can't also specify other params")
        if not host:
            host = config.MONGODB_HOST
        if not port:
            port = config.MONGODB_PORT
        self.host = host
        self.port = port
        self.database = database
        self.collection = collection
        self.placeholder = placeholder


class Meta(type):
    """Metaclass for our model class.  Inspects the class variables, looks
    for 'mongo' and uses that to connect to the database. """

    # A very rudimentary connection pool:
    _connections = {}

    def __new__(mcs, name, bases, data):
        # Pull fields out of the MongoCollection object to get the database
        # connection parameters, etc.
        collection_info = data['mongo']
        if 'indices' in data:
            index_info = data['indices']
        else:
            index_info = []
        host = collection_info.host
        port = collection_info.port
        dbname = collection_info.database
        collname = collection_info.collection

        new_cls = super(Meta, mcs).__new__(mcs, name, bases, data)

        # This constructor runs on the Model class as well as the derived
        # classes.  When we're a Model, we don't have a proper
        # configuration, so we just skip the connection stuff below.
        if collection_info.placeholder:
            new_cls.database = None
            new_cls.collection = None
            return new_cls

        if (not collection_info.placeholder
            and not (host and port and dbname and collname)):
            raise Exception(
                'minimongo Model %s %s improperly configured: %s %s %s %s' % (
                    mcs, name, host, port, dbname, collname))

        hostport = (host, port)
        # Check the connection pool for an existing connection.
        if hostport in mcs._connections:
            connection = mcs._connections[hostport]
        else:
            connection = pymongo.Connection(host, port)
        mcs._connections[hostport] = connection
        new_cls.database = connection[dbname]
        new_cls.collection = Collection(new_cls.database,
                                        collname,
                                        document_class=new_cls)
        new_cls._index_info = index_info

        # Generate all our indices automatically when the class is
        # instantiated.  This will result in calls to pymongo's
        # ensure_index() method at import time, so import all your models up
        # front.
        new_cls.auto_index()

        return new_cls

    def auto_index(mcs):
        """Build all indices for this collection specified in the definition
        of the Model."""
        for index in mcs._index_info:
            index.ensure(mcs.collection)


class Model(dict):
    """Base class for all Minimongo objects.  Derive from this class."""
    __metaclass__ = Meta
    mongo = MongoCollection(placeholder=True)

    # These lines make this object behave both like a dict (x['y']) and like
    # an object (x.y).  We have to translate from KeyError to AttributeError
    # since model.undefined raises a KeyError and model['undefined'] raises
    # a KeyError.  we don't ever want __getattr__ to raise a KeyError, so we
    # "translate" them below:
    def __getattr__(*args, **kwargs):
        try:
            return dict.__getitem__(*args, **kwargs)
        except KeyError, excn:
            raise AttributeError(excn)

    def __setattr__(*args, **kwargs):
        try:
            return dict.__setitem__(*args, **kwargs)
        except KeyError, excn:
            raise AttributeError(excn)

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, excn:
            raise AttributeError(excn)

    def __init__(self, initial_value=None):
        if initial_value:
            super(Model, self).__init__(initial_value)

    def dbref(self):
        """Return an instance of a DBRef for the current object."""
        if not hasattr(self, '_id'):
            self._id = pymongo.objectid.ObjectId()
        assert self._id != None, "ObjectId must be valid to create DBRef"
        return pymongo.dbref.DBRef(collection=self.collection.name,
                                   id=self._id,
                                   database=self.database.name)

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

    def __str__(self):
        return type(self).__name__ + '(' + str(dict(self)) + ')'

    def __unicode__(self):
        return type(self).__name__ + u'(' + str(dict(self)) + u')'


class Index(object):
    """Just a simple container class holding the arguments that are passed
    directly to pymongo's ensure_index method."""
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def ensure(self, collection):
        """Call pymongo's ensure_index on the given collection with the
        stored args."""
        return collection.ensure_index(*self._args, **self._kwargs)
