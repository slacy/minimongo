import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = ['pymongo']

setup(name='minimongo',
      version='0.1.2',
      description='Minimal database Model management for MongoDB',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Database",
        ],
      author='Steve Lacy',
      author_email='slacy@slacy.com',
      url='http://github.com/slacy/minimongo',
      keywords=['mongo', 'mongodb', 'pymongo', 'orm'],
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="minimongo",
      )
