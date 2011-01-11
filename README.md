# Minimongo

Minimongo is a lightweight, Pythonic Object-Oriented interface to MongoDB.

It provides a very thin, and dynamicly typed object management layer for any
data stored in any MongoDB collection.

Minimongo can easily layer on top of existing MongoDB collections, and will
work properly with almost any existing schema, even from 3rd party
applications.

Author:

    Steve Lacy <github@slacy.com>
    Twitter: @sklacy
    http://slacy.com/blog

For an introduction to all it's features, please see [the USAGE
file](http://github.com/slacy/minimongo/blob/master/USAGE.rst).

## Major features

* No schema declaration

    Minimongo has *no* schema declaration.  You do not pre-declare the names
    and types of your fields.  Minimongo takes a minimalist and flexible
    approach to schemas.  You can set any value on any Minimongo-derived
    object.

* Declared database & collection names.

    Miminogo allows you to progromaticaly declare your database and
    collection names.

    You'll only need to put your collection name in one place, and Minimongo
    provides classmethods for accessing the DB and Collection names
    programatically.  This means you can easily switch DB or Collection
    names without having to change all your code.

* Automatic MongoDB Connection mangagement and connection pooling.

* Friendly support for DBRef types.

    Minimongo can easily generate fully-specified (DB name included) DBRef
    objects, and store these into fields.  Fetching via DBRef is simplified
    as well.

* Uses Pymongo's query syntax.

    Query methods are passed directly to Pymongo's API.  Minimongo provides
    very few custom methods, and delegates nearly all operations directly to
    Pymongo.  This means as features are added to Pymongo, they will be
    automatically accessible via Minimongo.

* Easily extensible.

    Minimongo-derived objects can be easily extended to add new functionality.

* Easy object creation via initalization from Dicts.


## Example

    from minimongo import Model, MongoCollection

    class MyCollection(Model):
        mongo = MongoCollection(database='test', collection='minimongo.example')

    if __name__ == '__main__':
        obj = MyCollection({'x': 1, 'y': 2}).save()

        res = MyCollection.find({'x': 1})
        res.other = 'some data'
        res.save()

## TODOs & Upcoming features:

* DB Connection management and pooling.  Existing code is very crude when it
  comes to DB Connection management.  Implement DB connection pools, etc.

* Easier configuration management.

* More template-friendly member accessing.  Return None for missing fields?

* Per-object configuration directives.  Read-only, Rigid (no schema change
  allowed after read), etc.

* Support for automatic DBRef field dereferencing.

* Better support for SON and field ordering.  Right now, most things are
  Python dict, which means that ordering is not defined.

* Delta modification tracking so that when you call save(), it doesn't send
  the whole document back to the server to modify one field.

* Support for the mongodb atomic operations like $inc, $push, $pull, etc.

* Better support for nested Model objects. (Right now, nested data must be
  of a native Python type, not of another Model).

# Feedback welcome!

Please email github@slacy.com with comments, suggestions, or comment via
http://github.com/slacy/minimongo

