# -*- coding: utf-8 -*-

import os
import sys
import subprocess

try:
    from setuptools import find_packages, setup, Command
except ImportError:
    from distutils.core import find_packages, setup, Command


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README.rst")).read()
CHANGES = open(os.path.join(here, "CHANGES.txt")).read()


class PyTest(Command):
    """Unfortunately :mod:`setuptools` support only :mod:`unittest`
    based tests, thus, we have to overider build-in ``test`` command
    to run :mod:`pytest`."""
    user_options = []
    initialize_options = finalize_options = lambda self: None

    def run(self):
        errno = subprocess.call([sys.executable, "runtests.py"])
        raise SystemExit(errno)


requires = ["pymongo"]

setup(
    name="minimongo",
    version="0.2.5",
    packages=find_packages(),
    cmdclass={"test": PyTest},

    install_requires = ["pymongo>=1.9"],
    zip_safe=False,
    include_package_data=True,

    author="Steve Lacy",
    author_email="slacy@slacy.com",
    description="Minimal database Model management for MongoDB",
    long_description=README + "\n\n" + CHANGES,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Database",
    ],
    keywords=["mongo", "mongodb", "pymongo", "orm"],
    url="http://github.com/slacy/minimongo",
)
