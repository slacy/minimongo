Minimongo usage & tutorial
==========================

Confirutanion
-------------

By default, minimongo will connect to a mongodb instance on
'localhost:27017'.  If this works for your setup, then you can continue.
Otherwise, you'll need to manually configure minimongo.

To configure minimongo, it needs to be able to import a module named
'minimongo_config'.  (It will execute.  Thus, you'll need to create a file
named minimongo_config on your import path.  It's contents should look like
this:

    MONGODB_HOSTNAME = 'your_mongodb_hostname or ip_addr'
    MONGODB_PORT = 27017

Note: If you're unable to create something that satisfies 'import
minimongo_config', then you can set MINIMONGO_SETTINGS_MODULE and then set
that to the name of a module that provides MONGODB_HOSTNAME and
MONGODB_PORT.

