Minimongo Tutorial
==========================

.. currentmodule:: minimongo

Configuration
-------------

By default, minimongo will connect to a mongodb instance on ``localhost:27017``.
If this works for your setup, then you can continue to the next step. Otherwise, you'll
need to provide minimongo with some configuration.

The easiest way to call :func:`configure` right before declaring your models::

    from minimongo import configure

    configure(host="example.com", port=27018)

If you prefer putting all the settings in a single module -- for example ``config.py``,
you can simply pass it to :func:`configure` and all variables prefixed with ``MONGODB_``
will be loaded automatically::

    from minimongo import configure
    from myapp import config

    configure(config)


Defining models
---------------

The next step is to write some code that imports and uses minimongo. Here's
a quick example::

  from minimongo import Model

  class Foo(Model):
      class Meta:
          database = "minimongo"
          collection = "rocks"

As you might have noticed ``minimongo`` has no schema declarations, so the
only thing that can be declared is a special ``class Meta`` container, which
provides a way to change models' behaviour.

Here's a list of ``Meta`` options available so far:

+---------------------------------+------------------------------------------------+
| Option                          | Description                                    |
+=================================+================================================+
| database                        | name of the database to connect to             |
+---------------------------------+------------------------------------------------+
| host (default: ``"localhost"``) | --                                             |
+---------------------------------+------------------------------------------------+
| port (default: ``27017``)       | --                                             |
+---------------------------------+------------------------------------------------+
| auto_index (default: ``True``)  | if ``True`` indices a created automatically on |
|                                 | module import, else -- you're expected to call |
|                                 | :meth:`Model.auto_index` yourself              |
+---------------------------------+------------------------------------------------+
| collection (default: ``None``)  | name of the collection the Model works with, if|
|                                 | not given explicitly, is constructed           |
|                                 | automatically from class name, for example:    |
|                                 | ``SomeThing --> "some_thing"``                 |
+---------------------------------+------------------------------------------------+
| collection_class (default:      | collection class, which will be available via  |
| :class:`Collection`)            | ``Model.collection``                           |
+---------------------------------+------------------------------------------------+

.. warning:: ``minimongo`` is alpha software, so some options *might* be removed or
             replaced in the future.


Creating and saving objects
---------------------------

::

  # Constructing an instance. Not saved until you call save()
  foo = Foo(x=1)

  # ... adding more attributes
  foo.y = 2
  foo.z = 3

  # .. and finally -- saving it to MongoDB.
  foo.save()

  # Note, that Foo accepts any type of values the built-in dict() accepts
  Foo({"x": 1, "y": 3}).save()
  Foo(("x", 1), ("y", 3)).save()


Query syntax is exactly the same as :mod:`pymongo`, so for instance the following
returns :class:`pymongo.cursor.Cursor`::

   Foo.collection.find({"x": 1})


Summing up
----------
All you need to do is:

  * Subclass :class:`Model`
  * Define an inner ``Meta`` class with a single required argument ``database``
  * ... and you're done :)


.. note:: Database connection management is done for you automatically; and you
          can assign fields right into the derived object, then call
          :meth:`Model.save`. It can't get easier than that!


Working with DBRefs
-------------------

``minimongo`` provides easy support for stored references via :class:`bson.dbref.DBRef`
fields. To generate a *DBRef*, just call :meth:`Model.dbref` method. If you have
a fied that you know is a *DBRef*, then you can use :meth:`Collection.from_dbref`
method to query via that field. For example::

    from minimongo import configure, Model

    configure(database="minimongo")

    class First(Model):
        pass

    class Second(Model):
        pass


    first = First({"x": 1}).save()

    # Create an object that references the first.  Can be in a different
    # collection and an different database.
    second = Second({"y": 1, "first": first.dbref()}).save()

    # Given the reference, fetch the object. `re_first` and `first`
    # are now two instances of the same object.
    re_first = First.collection.from_dbref(second.first)


Adding indices
--------------

Indices can be specified per collection, and are created automatically at the
time your :class:`Model` subclasses are imported, unless stated otherwise
(via ``auto_index = False`` in the ``Meta`` container). The synax is as follows::

  class Foo(Model):
      class Meta:
          database = "test"
          indices = (
              Index("x"),
              Index("y"),
          )


This would result in two calls to :mod:`pymongo` as follows::

  collection.ensure_index("x")
  collection.ensure_index("y")

The arguments to the :class:`Index` constructor are passed **unmodified**
directly to :meth:`pymongo.collection.Collection.ensure_index`. So, please
see :mod:`pymongo` documentation for :class:`Collection` for the possible
options to use there.


Additional Info
---------------

Please see unittests for additional usage scenarios, and feel free to contact me
at github@slacy.com with any feature requests or additions you'd like to see.
