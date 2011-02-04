#!/bin/python
import pymongo
from pymongo.dbref import DBRef
from minimongo import config
from pymongo.cursor import Cursor as PyMongoCursor
from pymongo.objectid import ObjectId

class MongoCollection(object):
    """Container class for connection to db & mongo collection settings."""
    def __init__(self,
                 host=None, port=None, database=None, collection=None):
        if not host:
            host = config.MONGODB_HOST
        if not port:
            port = config.MONGODB_PORT
        self.host = host
        self.port = port
        self.database = database
        self.collection = collection


def cursor_wrapped(wrapped):
    def method(cursor, *args, **kwargs):
        return Cursor(results=wrapped(cursor._results, *args, **kwargs),
                      obj_type=cursor._obj_type)
    cursor_wrapped.__doc__ = wrapped.__doc__
    return method


class Cursor(object):
    """Simple wrapper around the cursor (iterator) that comes back from
    pymongo.  We do this so that when you iterate through results from a
    find, you get a generator of Model objects, not a bunch of dicts. """
    def __init__(self, results, obj_type):
        self._obj_type = obj_type
        self._results = results

    def count(self):
        """Analog of the normal count() operation on MongoDB cursors.
        Returns the number of items matching this query."""
        return self._results.count()

    # rewind = cursor_wrapped(PyMongoCursor.rewind)
    clone = cursor_wrapped(PyMongoCursor.clone)
    limit = cursor_wrapped(PyMongoCursor.limit)
    skip = cursor_wrapped(PyMongoCursor.skip)
    sort = cursor_wrapped(PyMongoCursor.sort)

    def __iter__(self):
        for i in self._results:
            yield(self._obj_type(i))


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
        if name == 'Model':
            new_cls.db = None
            new_cls.collection = None
            return new_cls

        if not (host and port and dbname and collname):
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
        new_cls.db = connection[dbname]
        new_cls.collection = new_cls.db[collname]
        new_cls._collection_name = collname
        new_cls._database_name = dbname
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

    def collection_name(mcs):
        """Return the name of the MongDB collection for the current Model."""
        return mcs._collection_name

    def database_name(mcs):
        """Return the name of the MongDB database for the current Model."""
        return mcs._database_name

    def from_dbref(mcs, dbref):
        """Given a DBRef, return an instance."""
        return mcs.find_one({'_id': dbref.id})

    def find(mcs, *args, **kwargs):
        """Passthrough to pymongo's find() method, and wrap the results in a
        Cursor object so that we get Model objects while iterating."""
        results = mcs.collection.find(*args, **kwargs)
        return Cursor(results, mcs)

    def find_one(mcs, *args, **kwargs):
        """Passthrough to pymongo's find_one() method, and wrap the results
        in a Model object of the correct type."""
        data = mcs.collection.find_one(*args, **kwargs)
        if data:
            return mcs(data)
        return None

    def __getattribute__(mcs, *args):
        """This gets invoked for things that look like classmethods.  First
        we try the attribute from self, then from the collection, then from
        the db."""
        try:
            ret = object.__getattribute__(mcs, *args)
        except AttributeError:
            try:
                ret = object.__getattribute__(mcs.collection, *args)
            except AttributeError:
                ret = object.__getattribute__(mcs.db, *args)
        return ret


class Model(object):
    """Base class for all Minimongo objects.  Derive from this class."""
    __metaclass__ = Meta
    mongo = MongoCollection(host=None, port=None,
                            database=None, collection=None)

    def __init__(self, data=None):
        if data:
            self.__dict__ = data
        else:
            self.__dict__ = {}

    def dbref(self):
        """Return an instance of a DBRef for the current object."""
        if not self._id:
            self._id = ObjectId()
        assert self._id != None, "ObjectId must be valid to create DBRef"
        return DBRef(collection=self.collection_name,
                     id=self._id,
                     database=self.database_name)

    @property
    def id(self):
        """Return the MongoDB _id value."""
        return self._id

    @property
    def rawdata(self):
        """Return the raw document data as a dict."""
        return self.__dict__

    @property
    def database_name(self):
        """Return the name of the MongoDB Database for this class."""
        return type(self)._database_name

    @property
    def collection_name(self):
        """Return the name of the MongoDB collection for this class."""
        return type(self)._collection_name

    def remove(self):
        """Delete this object."""
        return self.collection.remove(self._id)

    def update(self):
        """Update (write) this object."""
        self.collection.update(
            {'_id': self._id},
            self.__dict__)
        return self

    def save(self):
        """Save this Model to it's mongo collection"""
        self.collection.save(self.__dict__)
        return self

    def __str__(self):
        ret = type(self).__name__ + '(' + str(self.__dict__) + ')'
        return ret

    def __unicode__(self):
        ret = type(self).__name__ + u'(' + str(self.__dict__) + u')'
        return ret


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


