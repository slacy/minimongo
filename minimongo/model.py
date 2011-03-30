# -*- coding: utf-8 -*-
import re
from pymongo import Connection
from pymongo.dbref import DBRef
from pymongo.objectid import ObjectId
import minimongo.options


class ModelBase(type):
    '''Metaclass for all models.

    .. todo:: add Meta inheritance -- so that missing attributes are
              populated from the parrent's Meta if any.
    '''

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
            delattr(new_class, 'Meta')  # Won't need the original metadata
                                        # container anymore.

        options = minimongo.options._Options(meta)
        options.collection = options.collection or to_underscore(name)

        if not (options.host and options.port and options.database):
            raise Exception(
                'Model %r improperly configured: %s %s %s' %
                (name, options.host, options.port, options.database)
            )

        # Checking connection pool for an existing connection.
        hostport = options.host, options.port
        if hostport in mcs._connections:
            connection = mcs._connections[hostport]
        else:
            # _connect=False option
            # creates :class:`pymongo.connection.Connection` object without
            # establishing connection. It's required if there is no running
            # mongodb at this time but we want to create :class:`Model`.
            connection = Connection(*hostport, _connect=False)
            mcs._connections[hostport] = connection

        new_class._meta = options
        new_class.database = connection[options.database]
        new_class.collection = options.collection_class(
            new_class.database, options.collection, document_class=new_class)

        if options.auto_index:
            new_class.auto_index()   # Generating required indices.

        return new_class

    def auto_index(mcs):
        '''Builds all indices, listed in model's Meta class.

           >>> class SomeModel(Model)
           ...     class Meta:
           ...         indices = (
           ...             Index('foo'),
           ...         )

        .. note:: this will result in calls to
                  :meth:`pymongo.collection.Collection.ensure_index`
                  method at import time, so import all your models up
                  front.
        '''
        for index in mcs._meta.indices:
            index.ensure(mcs.collection)


class Model(dict):
    '''Base class for all Minimongo objects.

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
    '''

    __metaclass__ = ModelBase

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           super(Model, self).__str__())

    def __unicode__(self):
        return str(self).decode('utf-8')

    # These lines make this object behave both like a dict (x['y']) and like
    # an object (x.y).  We have to translate from KeyError to AttributeError
    # since model.undefined raises a KeyError and model['undefined'] raises
    # a KeyError.  we don't ever want __getattr__ to raise a KeyError, so we
    # 'translate' them below:
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

    def dbref(self, with_database=True):
        '''Returns a DBRef for the current object.

        If `with_database` is False, the resulting :class:`pymongo.dbref.DBRef`
        won't have a :attr:`database` field.
        '''
        if not hasattr(self, '_id'):
            self._id = ObjectId()

        database = self._meta.database if with_database else None
        return DBRef(self._meta.collection, self._id, database)

    def remove(self):
        '''Remove this object from the database.'''
        return self.collection.remove(self._id)

    def mongo_update(self):
        '''Update database data with object data.'''
        self.collection.update({'_id': self._id}, self)
        return self

    def save(self, *args, **kwargs):
        '''Save this object to it's mongo collection.'''
        self.collection.save(self, *args, **kwargs)
        return self


# Utils.

def to_underscore(string):
    '''Converts a given string from CamelCase to under_score.

    >>> to_underscore('FooBar')
    'foo_bar'
    '''
    return re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', string).lower()



