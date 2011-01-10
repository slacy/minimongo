import pymongo
from pymongo.dbref import DBRef
from pymongo.son_manipulator import AutoReference
from collections import namedtuple
from minimongo.config import MONGODB_HOST, MONGODB_PORT


class MongoCollection(object):
    """Container class for connection to db & mongo collection settings."""
    def __init__(self,
                 host=None, port=None, database=None, collection=None):
        if not host:
            host = MONGODB_HOST
        if not port:
            port = MONGODB_PORT
        self.host = host
        self.port = port
        self.database = database
        self.collection = collection


class Cursor(object):
    """Simple wrapper around the cursor (iterator) that comes back from
    pymongo.  We do this so that when you iterate through results from a
    find, you get a generator of Model objects, not a bunch of dicts. """
    def __init__(self, results, obj_type):
        self._obj_type = obj_type
        self._results = results

    def count(self):
        return self._results.count()

    def sort(self, *args, **kwargs):
        return Cursor(results=self._results.sort(*args, **kwargs),
                      obj_type=self._obj_type)

    def limit(self, *args, **kwargs):
        return Cursor(results=self._results.limit(*args, **kwargs),
                      obj_type=self._obj_type)

    def skip(self, *args, **kwargs):
        return Cursor(results=self._results.skip(*args, **kwargs),
                      obj_type=self._obj_type)

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
            # Check the connection pool for an existing connection.
            if (host, port) in mcs._connections:
                connection = mcs._connections[(host, port)]
            else:
                connection = pymongo.Connection(host, port)
                mcs._connections[(host, port)] = connection
            new_cls.db = connection[dbname]
            new_cls.collection = new_cls.db[collname]
            new_cls._collection_name = collname
            new_cls._database_name = dbname
            # new_cls.db.add_son_manipulator(AutoReference(new_cls.db))
        return new_cls


class Model(object):
    __metaclass__ = Meta
    mongo = MongoCollection(host=None, port=None,
                            database=None, collection=None)

    def __init__(self, data=None):
        if data:
            self.__dict__['_data'] = data
        else:
            self.__dict__['_data'] = {}

    def dbref(self):
        return DBRef(collection=self.collection_name(),
                     id=self._data['_id'],
                     database=self.database_name())

    @classmethod
    def from_dbref(cls, dbref):
        return cls.find_one({'_id': dbref.id})

    @property
    def id(self):
        return self._id

    @property
    def rawdata(self):
        return self._data

    @classmethod
    def collection_name(cls):
        return cls._collection_name

    @classmethod
    def database_name(cls):
        return cls._database_name

    @classmethod
    def find(cls, *args, **kwargs):
        results = cls.collection.find(*args, **kwargs)
        return Cursor(results, cls)

    @classmethod
    def find_one(cls, *args, **kwargs):
        data = cls.collection.find_one(*args, **kwargs)
        if data:
            return cls(data)
        return None

    @classmethod
    def insert(cls, *args, **kwargs):
        return cls.collection.insert(*args, **kwargs)

    @classmethod
    def remove(cls, spec):
        return cls.collection.remove(spec)

    @classmethod
    def ensure_index(cls, *args, **kwargs):
        return cls.collection.ensure_index(*args, **kwargs)

    @classmethod
    def drop_collection(cls):
        return cls.collection.drop()

    def delete(self):
        return self.collection.remove(self._data['_id'])

    def update(self):
        self.collection.update(
            {'_id': self._data['_id']},
            self._data)
        return self

    def save(self):
        self.collection.save(self._data)
        return self

    def __setitem__(self, key, value):
        self._data[key] = value

    def __getitem__(self, key):
        return self._data[key]

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return self._data[attr]

    def __setattr__(self, attr, value):
        self._data[attr] = value

    def __delattr__(self, attr):
        del self._data[attr]

    def __str__(self):
        ret = str(self._data)
        return ret

    def __contains__(self, item):
        return item in self._data
