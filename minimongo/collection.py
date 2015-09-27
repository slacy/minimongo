# -*- coding: utf-8 -*-

from pymongo.collection import Collection as PyMongoCollection
from pymongo.cursor import Cursor as PyMongoCursor


class Cursor(PyMongoCursor):

    def __init__(self, *args, **kwargs):
        self._wrapper_class = kwargs.pop('wrap')
        super(Cursor, self).__init__(*args, **kwargs)

    def next(self):
        return self._wrapper_class(super(Cursor, self).next())

    # XXX simple alias won't work here because of the super call.

    def __next__(self):
        return self._wrapper_class(super(Cursor, self).__next__())

    def __getitem__(self, index):
        if isinstance(index, slice):
            return super(Cursor, self).__getitem__(index)
        else:
            return self._wrapper_class(super(Cursor, self).__getitem__(index))


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
        self.document_class = kwargs.pop('document_class')
        super(Collection, self).__init__(*args, **kwargs)

    def find(self, *args, **kwargs):
        """Same as :meth:`pymongo.collection.Collection.find`, except
        it returns the right document class.
        """
        return Cursor(self, *args, wrap=self.document_class, **kwargs)

    def find_one(self, *args, **kwargs):
        """Same as :meth:`pymongo.collection.Collection.find_one`, except
        it returns the right document class.
        """
        data = super(Collection, self).find_one(*args, **kwargs)
        if data:
            return self.document_class(data)
        return None

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
            raise ValueError('DBRef points to an invalid collection.')
        elif dbref.database and not dbref.database == self.database.name:
            raise ValueError('DBRef points to an invalid database.')
        else:
            return self.find_one(dbref.id)


class DummyCollection(object):
    @classmethod
    def drop(*args, **kwargs):
        # It's okay to drop this bogus collection for convenience's sake.
        # We might actually want to find all classes derived from this guy
        # and drop all those models here.
        pass

    @classmethod
    def save(*args, **kwargs):
        raise Exception("Can't save on an interface collection")

    @classmethod
    def find(*args, **kwargs):
        # Union-find over all models derived from this one?
        raise Exception("Can't find on an interface collection")

    @classmethod
    def find_one(*args, **kwargs):
        # Union-find over all models derived from this one?
        raise Exception("Can't find_one on an interface collection")
