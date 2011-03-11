.. minimongo documentation master file, created by
   sphinx-quickstart on Fri Mar 11 23:00:20 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


:mod:`minimongo` -- Welcome to minimongo's documentation!
=========================================================

.. module:: minimongo
	 :synopsis: Minimal database Model management for MongoDB.

.. moduleauthor:: Steve Lacy <github@slacy.com>
.. moduleauthor:: Sergei Lebedev <superbobry@gmail.com>

:Author: Steve Lacy <github@slacy.com>
:Version: |release|
:Source: `github.com <https://github.com/slacy/minimongo>`_
:Bug tracker: `github.com/issues <https://github.com/slacy/minimongo/issues>`_


Features
--------

* **No schema declaration**

  ``minimongo`` has *no* schema declaration whatsoever. You do not pre-declare
  the names and types of your fields. ``minimongo`` takes a minimalist and flexible
  approach to schemas.  You can set any value on any Minimongo-derived object.

* **Automatic MongoDB Connection mangagement and connection pooling**

  ``minimongo`` automatically connects to your database for you, and has its
  own simple Connection pool. Connections are persistent and last the lifetime
  of your application.

* **Friendly support for DBRef types**

  ``minimongo`` can easily generate fully-specified DBRef objects, and store
  these into fields. Fetching via DBRef is simplified as well.

* **Uses pymongo_'s native query syntax**

  Query methods are passed directly to pymongo's API. ``minimongo`` provides
  very few custom methods, and delegates nearly all operations directly to
  pymongo. This means as features are added to pymongo, they will be
  automatically accessible via ``minimongo``.

* **Easy Index creation & management**

  Indices for a given collection can be specified at declaration time. This
  results in automatic calls to :meth:`pymongo.collection.Collection.ensure_index`
  method at the time your program starts up. Therefore, all the proper indices
  for your collections are always in place.

* **Easily extensible**

  Behind the scenes, ``minimongo`` objects are plain Python dicts which
  can be easily extended to add new functionality.


Example
-------

Here's a very brief example of creating an object, querying for it, modifying a field, and then saving it back again::

    from minimongo import Model, Index

    class MyCollection(Model):
        class Meta:
            # Here, we specify the database and collection names.
            # A connection to your DB is automatically created.
            database = "test"
            collection = "minimongo.example"

            # Now, we programatically declare what indices we want.
            # The arguments to the Index constructor are identical to
            # the args to pymongo's ensure_index function.
            indices = (
                Index("a"),
            )


    if __name__ == "__main__":
        # Create & save an object, and return a local in-memory copy of it:
        obj = MyCollection({'x': 1, 'y': 2}).save()

        # Find that object again, loading it into memory:
        res = MyCollection.collection.find_one({'x': 1})

        # Change a field value, and save it back to the DB.
        res.other = 'some data'
        res.save()


API
---

.. autofunction:: configure

.. autoclass:: Collection
      :members: document_class, find, find_one, from_dbref

.. autoclass:: Model
      :members: dbref, auto_index, save, remove, mongo_update

.. autoclass:: Index
      :members: __eq__, ensure


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

