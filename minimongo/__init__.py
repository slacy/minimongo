# -*- coding: utf-8 -*-

__all__ = ('Collection', 'Index', 'Model', 'MongoCollection')

import types

from .model import Collection, Index, Model, Options


def configure(module=None, **kwargs):
    if module is not None and isinstance(module, types.ModuleType):
        # Search module for MONGODB_* attributes and converting them
        # to Options' values, ex: MONGODB_PORT ==> port.
        attrs = module.__dict__.itervalues()
        attrs = ((attr.replace("MONGODB_", "").lower(), value)
                 for attr in attrs if attr.startwith("MONGODB_"))

        Options.configure(**dict(attrs))
    elif kwargs:
        Options.configure(**kwargs)
