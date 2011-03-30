# -*- coding: utf-8 -*-
'''
    minimongo
    ~~~~~~~~~

    Minimongo is a lightweight, schemaless, Pythonic Object-Oriented
    interface to MongoDB.
'''
from minimongo.index import Index
from minimongo.collection import Collection
from minimongo.model import Model, AttrDict
from minimongo.options import configure

__all__ = ('Collection', 'Index', 'Model', 'configure', 'AttrDict')


