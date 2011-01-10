import sys
import os

# Taken from Django, which says "Taken from Python 2.7..."
def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                              "package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]


MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

if __name__ != '__main__':
    try:
        settings_module_name = os.environ['MINIMONGO_SETTINGS_MODULE']
    except KeyError, e:
        settings_module_name = None

    if not settings_module_name:
        settings_module_name = 'minimongo_config'

    module = import_module(settings_module_name)
    MONGODB_HOST = module.MONGODB_HOST
    MONGODB_PORT = module.MONGODB_PORT

