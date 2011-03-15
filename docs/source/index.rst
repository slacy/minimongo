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

``minimongo`` is a lightweight, schemaless, Pythonic Object-Oriented
interface to MongoDB.

It provides a very thin, dynamicly typed (schema-less) object management
layer for any data stored in any MongoDB collection. ``minimongo`` directly
calls the existing pymongo_ query syntax.

``minimongo`` can easily layer on top of existing MongoDB collections, and
will work properly with almost any existing schema, even from third party
applications.


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

* **Uses pymongo's native query syntax**

  Query methods are passed directly to pymongo_'s API. ``minimongo`` provides
  very few custom methods, and delegates nearly all operations directly to
  pymongo_. This means as features are added to pymongo_, they will be
  automatically accessible via ``minimongo``.

* **Easy index creation and management**

  Indices for a given collection can be specified at declaration time. This
  results in automatic calls to :meth:`pymongo.collection.Collection.ensure_index`
  method at the time your program starts up. Therefore, all the proper indices
  for your collections are always in place.


Documentation
-------------

Contents:

.. toctree::
   :maxdepth: 2

   example
   usage
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _pymongo: http://api.mongodb.org/python/1.9%2B/index.html
