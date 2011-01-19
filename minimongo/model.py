#!/bin/python
import pymongo
from pymongo.dbref import DBRef
from minimongo import config
from pymongo.cursor import Cursor as PyMongoCursor


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
        print "cursor_wrapped %s %s %s" % (wrapped, args, kwargs)
        return Cursor(results=wrapped(cursor._results, *args, **kwargs),
                      obj_type=cursor._obj_type)
    cursor_wrapped.__doc__ = wrapped.__doc__
    return method

class Cursor(object):
    """Simple wrapper around the cursor (iterator) that comes back from
    pymongo.  We do this so that when you iterate through results from a
    find, you get a generator of Model objects, not a bunch of dicts. """
    def __init__(self, results, obj_type):
        print "Making a cursor for %s" % results
        self._obj_type = obj_type
        self._results = results

    def count(self):
        return self._results.count()

    sort = cursor_wrapped(PyMongoCursor.sort)
    limit = cursor_wrapped(PyMongoCursor.limit)
    skip = cursor_wrapped(PyMongoCursor.skip)

    def __iter__(self):
        for i in self._results:
            yield(self._obj_type(i))


class Meta(type):
    """Metaclass for our model class.  Inspects the class variables, looks
    for 'mongo' and uses that to connect to the database. """

    # A very rudimentary connection pool:
    _connections = {}

    def __new__(mcs, name, bases, data):
        host = data['mongo'].host
        port = data['mongo'].port
        dbname = data['mongo'].database
        collname = data['mongo'].collection
        new_cls = super(Meta, mcs).__new__(mcs, name, bases, data)
        if host and port and dbname and collname:
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
        return new_cls

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
        except AttributeError, _err:
            try:
                ret = object.__getattribute__(mcs.collection, *args)
            except AttributeError, _err:
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
        return DBRef(collection=self.collection_name,
                     id=self._id,
                     database=self.database_name)

    @property
    def id(self):
        return self._id

    @property
    def rawdata(self):
        """Return the raw document data as a dict."""
        return self.__dict__

    @property
    def database_name(self):
        return type(self)._database_name

    @property
    def collection_name(self):
        return type(self)._collection_name

    def delete(self):
        return self.collection.remove(self._id)

    def update(self):
        self.collection.update(
            {'_id': self._id},
            self.__dict__)
        return self

    def save(self):
        self.collection.save(self.__dict__)
        return self

    def __str__(self):
        ret = 'Model(' + str(self.__dict__) + ')'
        return ret
