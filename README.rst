minimongo
=========

:Info: Minimal database Model management for MongoDB.
:Author: Harry Marr (http://github.com/hmarr)


About
-----

``minimongo`` is a lightweight, schemaless, Pythonic Object-Oriented
interface to MongoDB.

It provides a very thin, dynamicly typed (schema-less) object management
layer for any data stored in any MongoDB collection. ``minimongo`` directly
calls the existing pymongo_ query syntax.

``minimongo`` can easily layer on top of existing MongoDB collections, and
will work properly with almost any existing schema, even from third party
applications.

Contact::

    Steve Lacy <github@slacy.com>
    Twitter: @sklacy
    http://slacy.com/blog


Installation
------------

If you have `setuptools <http://peak.telecommunity.com/DevCenter/setuptools>`_
you can use ``easy_install -U mongoengine``. Otherwise, you can download the
source from `GitHub <http://github.com/slacy/minimongo>`_ and run ``python
setup.py install``.


Dependencies
============
- pymongo_ 1.9+
- `sphinx <http://sphinx.pocoo.org>`_ (optional -- for documentation generation)


Example
-------

Here's a very brief example of creating an object, querying for it, modifying
a field, and then saving it back again::

    from minimongo import Model, Index

    class Foo(Model):
        class Meta:
            # Here, we specify the database and collection names.
            # A connection to your DB is automatically created.
            database = "minimongo"
            collection = "rocks"

            # Now, we programatically declare what indices we want.
            # The arguments to the Index constructor are identical to
            # the args to pymongo"s ensure_index function.
            indices = (
                Index("a"),
            )


    if __name__ == "__main__":
        # Create & save an object, and return a local in-memory copy of it:
        foo = Foo({"x": 1, "y": 2}).save()

        # Find that object again, loading it into memory:
        foo = Foo.collection.find_one({"x": 1})

        # Change a field value, and save it back to the DB.
        foo.other = "some data"
        foo.save()


Feedback welcome!
-----------------

Please email github@slacy.com with comments, suggestions, or comment via
http://github.com/slacy/minimongo

.. _pymongo: http://api.mongodb.org/python/1.9%2B/index.html
