import types
from minimongo.collection import Collection


def configure(module=None, prefix='MONGODB_', **kwargs):
    '''Sets defaults for ``class Meta`` declarations.

    Arguments can either be extracted from a `module` (in that case
    all attributes starting from `prefix` are used):

    >>> import foo
    >>> configure(foo)

    or passed explicictly as keyword arguments:

    >>> configure(database='foo')

    .. warning:: Current implementation is by no means thread-safe --
                 use it wisely.
    '''
    if module is not None and isinstance(module, types.ModuleType):
        # Search module for MONGODB_* attributes and converting them
        # to _Options' values, ex: MONGODB_PORT ==> port.
        attrs = module.__dict__.iteritems()
        attrs = ((attr.replace(prefix, '').lower(), value)
                 for attr, value in attrs if attr.startwith(prefix))

        _Options._configure(**dict(attrs))
    elif kwargs:
        _Options._configure(**kwargs)


class _Options(object):
    '''Container class for model metadata.

    You shouldn't modify this class directly, :func:`_configure` should
    be used instead.
    '''

    host = 'localhost'
    port = 27017
    indices = ()
    database = None
    collection = None
    auto_index = True
    collection_class = Collection

    def __init__(self, meta):
        if meta is not None:
            self.__dict__.update(meta.__dict__)

    @classmethod
    def _configure(cls, **defaults):
        '''Updates class-level defaults for :class:`_Options` container.'''
        for attr, value in defaults.iteritems():
            setattr(cls, attr, value)
