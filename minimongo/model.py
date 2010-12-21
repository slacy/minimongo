import pymongo

class Cursor(object):
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

    def __iter__(self):
        for i in self._results:
            yield(self._obj_type(i))


class Meta(type):
    def __new__(mcs, name, bases, data):
        dbname = data['mongo_database']
        collname = data['mongo_collection']
        print "dbname is %s" % dbname
        print "collname is %s" % collname
        new_cls = super(Meta, mcs).__new__(mcs, name, bases, data)
        if dbname and collname:
            new_cls.collection = pymongo.Connection()[dbname][collname]
        return new_cls


class Model(object):
    __metaclass__ = Meta
    mongo_database = None
    mongo_collection = None

    def __init__(self, data=None):
        if data:
            self.__dict__['_data'] = data
        else:
            self.__dict__['_data'] = {}

    @property
    def rawdata(self):
        return self._data

    @classmethod
    def find(cls, *args, **kwargs):
        results = cls.collection.find(*args, **kwargs)
        return Cursor(results, cls)

    @classmethod
    def find_one(cls, *args, **kwargs):
        data = cls.collection.find_one(*args, **kwargs)
        return cls(data)

    @classmethod
    def insert(cls, *args, **kwargs):
        return cls.collection.insert(*args, **kwargs)

    @classmethod
    def remove(cls, spec):
        return cls.collection.remove(spec)

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

    @classmethod
    def drop_collection(cls):
        return cls.collection.drop()

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
