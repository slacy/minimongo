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


if __name__ != '__main__':
    settings_module_name = os.environ['MINIMONGO_SETTINGS_MODULE']
    if not settings_module_name:
        settings_module_name = 'minimongo_config'
    else:
        try:
            module = import_module(settings_module_name)
        except Exception, e:
            MONGODB_HOSTNAME = module.MONGODB_HOSTNAME
            MONGODB_PORT = module.MONGODB_PORT

print "Minimongo using %s:%d", (MONGODB_HOSTNAME, MONGODB_PORT)
