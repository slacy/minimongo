Minimongo
===========

Minimongo is a lightweight, schemaless, Pythonic Object-Oriented interface
to MongoDB.

It provides a very thin, dynamicly typed (schema-less) object management
layer for any data stored in any MongoDB collection.  Minimongo directly
calls the existing pymongo_ query syntax.

Minimongo can easily layer on top of existing MongoDB collections, and will
work properly with almost any existing schema, even from 3rd party
applications.

Contact::

    Steve Lacy <github@slacy.com>
    Twitter: @sklacy
    http://slacy.com/blog

For an introduction to all it's features, please see the USAGE_ file.

Major features
--------------

* **No schema declaration**

  Minimongo has *no* schema declaration.  You do not pre-declare the names
  and types of your fields.  Minimongo takes a minimalist and flexible
  approach to schemas.  You can set any value on any Minimongo-derived
  object.

* **Declared database & collection names.**

  Miminogo allows you to progromaticaly declare your database and collection
  names.

  You'll only need to put your collection name in one place, and Minimongo
  provides classmethods for accessing the DB and Collection names
  programatically.  This means you can easily switch DB or Collection names
  without having to change all your code.

* **Automatic MongoDB Connection mangagement and connection pooling.**

  Minimongo automatically connects to your database for you, and has its own
  simple Connection pool.  Connections are persistent and last the lifetime
  of your application.

* **Friendly support for DBRef types.**

  Minimongo can easily generate fully-specified (DB name included) DBRef
  objects, and store these into fields.  Fetching via DBRef is simplified as
  well.

* **Uses Pymongo_'s native query syntax.**

  Query methods are passed directly to Pymongo_'s API.  Minimongo provides
  very few custom methods, and delegates nearly all operations directly to
  Pymongo_.  This means as features are added to Pymongo_, they will be
  automatically accessible via Minimongo.

* **Easy Index creation & management.**

  Indices for a given collection can be specified at declaration time.  This
  results in automatic calls to pymongo_'s ensure_index() function at the
  time your program starts up.  Therefore, all the proper indices for your
  collections are always in place.

* **Easily extensible.**

  Minimongo-derived objects can be easily extended to add new functionality.

* **Easy object creation via initalization from Dicts.**


Example
-------

Here's a very brief example of creating an object, querying for it,
modifying a field, and then saving it back again.::

  from minimongo import Model, MongoCollection

  class MyCollection(Model):
      # Here, we specify the database and collection names.
      # A connection to your DB is automatically created.
      mongo = MongoCollection(database='test', collection='minimongo.example')

      # Now, we programatically declare what indices we want.
      # The arguments to the Index constructor are identical to the args to
      # pymongo's ensure_index function.
      indices = (Index('x'),)

  if __name__ == '__main__':
      # Create & save an object, and return a local inmemory copy of it:
      obj = MyCollection({'x': 1, 'y': 2}).save()

      # Find that object again, loading it into memory:
      res = MyCollection.collection.find_one({'x': 1})

      # Change a field value, and save it back to the DB.
      res.other = 'some data'
      res.save()


TODOs & Upcoming features:
--------------------------

* Per-object configuration directives.  Read-only, Rigid (no schema change
  allowed after read), Type-Rigid (allow changing values, but not changing
  types), etc.

* Support for automatic DBRef field dereferencing via wrapper types.

* Better support for SON and field ordering.  Right now, most things are
  Python dict, which means that ordering is not defined.

* Delta modification tracking so that when you call save(), it doesn't send
  the whole document back to the server to modify one field.

* Support for the mongodb atomic operations like $inc, $push, $pull, etc via
  native Python primitives.

* Better support for nested Model objects. (Right now, nested data must be
  of a native Python type, not of another Model).

Feedback welcome!
-----------------

Please email github@slacy.com with comments, suggestions, or comment via
http://github.com/slacy/minimongo

.. _pymongo: http://api.mongodb.org/python/1.9%2B/index.html
.. _usage: http://github.com/slacy/minimongo/blob/master/USAGE.rst#readme
