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
this
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

Declaring MongoDB object collections:
-------------------------------------

The next step is to write some code that imports and uses minimongo.  Here's
a quick example

::
from minimongo.model import Model, MongoCollection

class MyCollection(Model):
    mongo = MongoCollection(database='test', collection='minimongo.test')

new_obj = MyCollection()
new_obj.x = 1
new_obj.y = 2
new_obj.save()

another_obj = MyCollection({'x':1, 'y':3}).save()

found_objects = MyCollection.find({'x':1})

for obj in found_objects:
    print obj
::
