# -*- coding: utf-8 -*-
"""
    minimongo
    ~~~~~~~~~

    Minimongo is a lightweight, schemaless, Pythonic Object-Oriented
    interface to MongoDB.
"""

__all__ = ("Collection", "Index", "Model")

import re
import types

from pymongo import Connection
from pymongo.collection import Collection as PyMongoCollection
from pymongo.dbref import DBRef
from pymongo.errors import InvalidId
from pymongo.objectid import ObjectId


def configure(module=None, prefix="MONGODB_", **kwargs):
    """Sets defaults for ``class Meta`` declarations.

    Arguments can either be extracted from a `module` (in that case
    all attributes starting from `prefix` are used):

    >>> import foo
    >>> configure(foo)

    or passed explicictly as keyword arguments:

    >>> configure(database="foo")

    .. warning:: Current implementation is by no means thread-safe --
                 use it wisely.
    """
    if module is not None and isinstance(module, types.ModuleType):
        # Search module for MONGODB_* attributes and converting them
        # to Options" values, ex: MONGODB_PORT ==> port.
        attrs = module.__dict__.iteritems()
        attrs = ((attr.replace(prefix, "").lower(), value)
                 for attr, value in attrs if attr.startwith(prefix))

        Options.configure(**dict(attrs))
    elif kwargs:
        Options.configure(**kwargs)


class Collection(PyMongoCollection):
    """A wrapper around :class:`pymongo.collection.Collection` that
    provides the same functionality, but stores the document class of
    the collection we're working with. So that
    :meth:`pymongo.collection.Collection.find` and
    :meth:`pymongo.collection.Collection.find_one` can return the right
    classes instead of plain :class:`dict`.
    """

    #: A reference to the model class, which uses this collection.
    document_class = None

    def __init__(self, *args, **kwargs):
        self.document_class = kwargs.pop("document_class")
        super(Collection, self).__init__(*args, **kwargs)

    def find(self, *args, **kwargs):
        """Same as :meth:`pymongo.collection.Collection.find`, except
        it returns the right document class.
        """
        kwargs["as_class"] = self.document_class
        return super(Collection, self).find(*args, **kwargs)

    def find_one(self, spec_or_id, *args, **kwargs):
        """Same as :meth:`pymongo.collection.Collection.find_one`, except
        it returns the right document class.

        .. note:: If a given `spec_or_id` is an instance of :func:`str`
                  or :func:`unicode`, we try coercing it to
                  :class:`pymongo.objectid.ObjectId` and fail silently in
                  case of an error.
        """
        kwargs["as_class"] = self.document_class

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
        """Given a :class:`pymongo.dbref.DBRef`, dereferences it and
        returns a corresponding document, wrapped in an appropriate model
        class.

        .. note:: If a given `dbref` point to a different database and
                  / or collection, :exc:`ValueError` is raised.
        """
        # Making sure a given DBRef points to a proper collection
        # and database.
        if not dbref.collection == self.name:
            raise ValueError("DBRef points to an invalid collection.")
        elif dbref.database and not dbref.database == self.database.name:
            raise ValueError("DBRef points to an invalid database.")
        else:
            return self.find_one(dbref.id)


class Options(object):
    """Container class for model metadata.

    You shouldn't modify this class directly, :func:`configure` should
    be used instead.
    """

    host = "localhost"
    port = 27017
    indices = ()
    database = None
    collection = None
    collection_class = Collection

    def __init__(self, meta):
        if meta is not None:
            self.__dict__.update(meta.__dict__)

    @classmethod
    def configure(cls, **defaults):
        """Updates class-level defaults for :class:`Options` container."""
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
            meta = None
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

        new_class.auto_index()   # Generating required indices.

        return new_class

    def auto_index(mcs):
        """Builds all indices, listed in model's Meta class.

           >>> class SomeModel(Model)
           ...     class Meta:
           ...         indices = (
           ...             Index("foo"),
           ...         )

        .. note:: this will result in calls to
                  :meth:`pymongo.collection.Collection.ensure_index`
                  method at import time, so import all your models up
                  front.
        """
        for index in mcs._meta.indices:
            index.ensure(mcs.collection)


class Model(dict):
    """Base class for all Minimongo objects.

    >>> class Foo(Model):
    ...     class Meta:
    ...         database = "somewhere"
    ...         indices = (
    ...             Index("bar", unique=True),
    ...         )
    ...
    >>> foo = Foo(bar=42)
    >>> foo
    {'bar': 42}
    >>> foo.bar == 42
    True
    """

    __metaclass__ = ModelBase

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           super(Model, self).__str__())

    def __unicode__(self):
        return str(self).decode("utf-8")

    # These lines make this object behave both like a dict (x["y"]) and like
    # an object (x.y).  We have to translate from KeyError to AttributeError
    # since model.undefined raises a KeyError and model["undefined"] raises
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

    def dbref(self, with_database=True):
        """Returns a DBRef for the current object.

        If `with_database` is False, the resulting :class:`pymongo.dbref.DBRef`
        won't have a :attr:`database` field.
        """
        if not hasattr(self, "_id"):
            self._id = ObjectId()

        database = self._meta.database if with_database else None
        return DBRef(self._meta.collection, self._id, database)

    def remove(self):
        """Remove this object from the database."""
        return self.collection.remove(self._id)

    def mongo_update(self):
        """Update database data with object data."""
        self.collection.update({"_id": self._id}, self)
        return self

    def save(self, *args, **kwargs):
        """Save this object to it"s mongo collection."""
        self.collection.save(self, *args, **kwargs)
        return self


class Index(object):
    """A simple wrapper for arguments to
    :meth:`pymongo.collection.Collection.ensure_index`."""

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def __eq__(self, other):
        """Two indices are equal, when the have equal arguments.

        >>> Index(42, foo="bar") == Index(42, foo="bar")
        True
        >>> Index(foo="bar") == Index(42, foo="bar")
        False
        """
        return self.__dict__ == other.__dict__

    def ensure(self, collection):
        """Calls :meth:`pymongo.collection.Collection.ensure_index`
        on the given `collection` with the stored arguments.
        """
        return collection.ensure_index(*self._args, **self._kwargs)


# Utils.

def to_underscore(string):
    """Converts a given string from CamelCase to under_score.

    >>> to_underscore("FooBar")
    "foo_bar"
    """
    return re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", string).lower()
