# -*- coding: utf-8 -*-

from __future__ import absolute_import

import types

from .collection import Collection


def configure(module=None, prefix='MONGODB_', **kwargs):
    """Sets defaults for ``class Meta`` declarations.

    Arguments can either be extracted from a `module` (in that case
    all attributes starting from `prefix` are used):

    >>> import foo
    >>> configure(foo)

    or passed explicictly as keyword arguments:

    >>> configure(database='foo')

    .. warning:: Current implementation is by no means thread-safe --
                 use it wisely.
    """
    if module is not None and isinstance(module, types.ModuleType):
        # Search module for MONGODB_* attributes and converting them
        # to _Options' values, ex: MONGODB_PORT ==> port.
        attrs = ((attr.replace(prefix, '').lower(), value)
                 for attr, value in vars(module).items()
                 if attr.startswith(prefix))

        _Options._configure(**dict(attrs))
    elif kwargs:
        _Options._configure(**kwargs)


class _Options(object):
    """Container class for model metadata.

    You shouldn't modify this class directly, :func:`_configure` should
    be used instead.
    """

    # Host & port of MongoDB server
    host = 'localhost'
    port = 27017
    # Indexes that should be generated for this model
    indices = ()

    # Current database and connection
    database = None
    collection = None

    # Authentication credentials
    username = None
    password = None

    # Should indices be created at startup?
    auto_index = True

    # What is the base class for Collections.
    collection_class = Collection

    # A list of tuples.  Each tuple's first element is function that will be
    # called for every __setitem__, and takes the key & value.  It should
    # return a boolean value as to whether or not the second function should
    # be called on the value to modify the value in place.  This can be used
    # for things like mapping dict to defaultdict, mapping document classes
    # or dbref's that are coming in from a loaded object, etc.
    field_map = ()

    # Is this an interface (i.e. will we derive from it and declare Meta
    # properly in the subclasses.)
    interface = False

    def __init__(self, meta):
        if meta is not None:
            self.__dict__.update(meta.__dict__)

    @classmethod
    def _configure(cls, **defaults):
        """Updates class-level defaults for :class:`_Options` container."""
        for attr in defaults:
            setattr(cls, attr, defaults[attr])
