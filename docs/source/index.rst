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

