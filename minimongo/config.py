#!/bin/python
"""
Provides the 2 symbols MONGODB_HOST and MONGODB_PORT that are used my
minimingo to connect to the proper database.

Uses the following 3 strategies:
1. import os.environ['MINIMONGO_SETTINGS_MODULE']
2. import 'minimongo.app_config'
3. default values (localhost, 27017)
"""
import os
import sys

#####################################################################
# DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED #
# DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED #
# DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED #
# DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED DEPRECATED #
#####################################################################

# Default values for MONGODB_HOST and MONGODB_PORT if no custom config
# module is specified, or if we're unable to 'from minimongo.app_config import
# MONGODB_HOST, MONGODB_PORT'
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017


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

    settings_modules = []

    try:
        settings_modules.append(os.environ['MINIMONGO_SETTINGS_MODULE'])
    except KeyError, e:
        pass

    # Here are the other 2 places that we try to import configs from:
    settings_modules.append('minimongo.app_config')
    settings_modules.append('minimongo_config')

    for module_name in settings_modules:
        try:
            module = import_module(module_name)
            MONGODB_HOST = module.MONGODB_HOST
            MONGODB_PORT = module.MONGODB_PORT
            # Once we get a successfull config module import, we break out
            # of the loop above.
            break
        except ImportError, exc:
            # Error importing this modlue, so we continue
            pass

