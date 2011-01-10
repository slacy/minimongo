Minimongo usage & tutorial
==========================

Confirutanion
-------------

By default, minimongo will connect to a mongodb instance on
'localhost:27017'.  If this works for your setup, then you can continue to
the next step.

Otherwise, you'll need to provide minimongo with some configuration.

The easiest way to configure minimongo is to include a module named
'minimongo_config' on your import path.  It's contents should look like
this:
::

    MONGODB_HOSTNAME = 'your_mongodb_hostname or ip_addr'
    MONGODB_PORT = 27017
::

For example, copy minimongo_config.example to minimongo_config.py and edit
the required values, and you should be good to go.

If you're unable to create something that satisfies 'import
minimongo_config' or you want a slightly cleaner setup, then you can set
MINIMONGO_SETTINGS_MODULE and then set that to the name of a module that
provides MONGODB_HOSTNAME and MONGODB_PORT.

Declaring MongoDB object collections
------------------------------------

The next step is to write some code that imports and uses minimongo.  Here's
a quick example:

::

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
    found_objects = MyCollection.find({'x':1})

    # found_objects is an iterable, just like in pymongo.
    for obj in found_objects:
        if 'x' in obj:
          obj.x += 1
          obj.save()
        print obj
::

In short, all you need to do is:

* Derive from minimongo's Model class
* Assign a class variable named "mongo" to an instance of a MongoCollection.

That's it!  Database connection management is done for you automatically,
and you can assign fields right into the derived object, then call save().
It can't get easier than that.

Advanced Usage
--------------

If you need raw access to the internal fields, then each derived Model
provides a rawdata() method call.  You can use this to return the internal
dict of values that are going to be stored.


