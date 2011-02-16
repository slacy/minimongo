Minimongo usage & tutorial
==========================

Configuration
-------------

By default, minimongo will connect to a mongodb instance on
'localhost:27017'.  If this works for your setup, then you can continue to
the next step.

Otherwise, you'll need to provide minimongo with some configuration.

The easiest way to configure minimongo is to include a module named
'minimongo.app_config' on your import path.  It's contents should look like
this::
MONGODB_HOSTNAME = 'your_mongodb_hostname or ip_addr'
MONGODB_PORT = 27017

For example, copy minimongo/minimongo/app.config.py.example to
app_config.py and edit the required values, and you should be good to
go.

If you're unable to create something that satisfies 'import
minimongo_config' or you want a slightly cleaner setup, then you can set
MINIMONGO_SETTINGS_MODULE and then set that to the name of a module that
provides MONGODB_HOSTNAME and MONGODB_PORT.

Declaring MongoDB object collections
------------------------------------

The next step is to write some code that imports and uses minimongo.  Here's
a quick example::

  from minimongo.model import Model, MongoCollection

  # Declare our collection
  class MyCollection(Model):
      mongo = MongoCollection(database='test', collection='minimongo.test')

  # Construct an instance.  Not saved until you call save()
  new_obj = MyCollection()

  # Assign some arbitry members
  new_obj.x = 1
  new_obj.y = 2

  # Save it to mongodb
  new_obj.save()

  # You can also do dict-base initialization.
  another_obj = MyCollection({'x':1, 'y':3}).save()

  # And the query syntax is exactly the same as pymongo.
  found_objects = MyCollection.collection.find({'x':1})

  # found_objects is an iterable, just like in pymongo.
  for obj in found_objects:
      if 'x' in obj:
        obj.x += 1
        obj.save()
      print obj


In short, all you need to do is:

* Derive from minimongo's Model class
* Assign a class variable named "mongo" to an instance of a MongoCollection.

That's it!  Database connection management is done for you automatically,
and you can assign fields right into the derived object, then call save().
It can't get easier than that.

Additional Features
-------------------

**DBRef Support** Minimongo provides easy support for stored references via DBRef fields.  To generate a DBRef, just call the dbref() method.  If you have a fied that you know is a DBRef, then you can use the from_dbref() method to query via that field.  For example::

  from minimongo import Model, MongoCollection
  class First(Model):
      mongo = MongoCollection(database='test_1', collection='test_coll_1')

  class Second(Model):
      mongo = MongoCollection(database='test_2', collection='test_coll_2')

  if __name__ == '__main__':
      # Create an object
      first = First({'x': 1}).save()\

      # Create an object that references the first.  Can be in a different
      # collection and an different database.
      second = Second({'y':1, 'first': first.dbref()}).save()

      # Given the reference, fetch the object.  're_first' and 'first'
      # are now two instances of the same object.
      re_first = First.collection.from_dbref(second.first)


**Index Support** Indices can be specified per collection, and are created (via
ensure_inedex) at the time your Model classes are imported.  The synax is as follows::

  class MyCollection(Model):
      mongo = MongoCollection(database='test', collection='tmp')
      indices = (Index('x'),
                 Index('y'),)


This would result in two calls to pymongo as follows::

  collection.ensure_index('x')
  collection.ensure_index('y')

The arguments to the Index constructor are passed directly to ensure_index,
unmodified.  So, please see the pymongo documentation for create_index and
ensure_index for the possible options to use there.

**Raw Field Support** If you need raw access to the internal fields, then
each derived Model provides a rawdata() method call.  You can use this to
return the internal dict of values that are going to be stored.


Additional Info
---------------

Please see the unit tests for additional usage scenarios, and feel free to
contact me at github@slacy.com with any feature requests or additions you'd
like to see.
