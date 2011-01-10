# Minimongo

Minimongo is a micro-ORM written in Python for MongoDB.

It provides very lightweight and dynamicly typed object management for any
data stored in any MongoDB collection.

Minimongo can easily layer on top of existing MongoDB data, and will work
properly with any existing schema, even from 3rd party applications.

Steve Lacy <github@slacy.com>
Twitter: @sklacy
http://slacy.com/blog

# Major features

## No schema declaration

Minimongo has *no* schema declaration.  You do not pre-declare the names and
types of your fields.  Minimongo takes a minimalist and flexible approach to
schemas.  You can set any value on any Minimongo-derived object.

## Declared database & collection names.

Miminogo allows you to progromaticaly declare your database and collection
names.

You'll only need to put your collection name in one place, and Minimongo
provides classmethods for accessing the DB and Collection names
programatically.  This means you can easily switch DB or Collection names
without having to change all your code.

## Friendly support for DBRef types.

Minimongo can easily generate fully-specified (DB name included) DBRef
objects, and store these into fields.  Fetching via DBRef is simplified as
well.

## Uses Pymongo's query syntax.

Query methods are passed directly to Pymongo's API.  Minimongo provides very
few custom methods, and delegates nearly all operations directly to Pymongo.
This means as features are added to Pymongo, they will be automatically
accessible via Minimongo.

## Easy object creation via initalization from Dicts.

A simple example:

    from minimongo import Model, MongoCollection

    class MyCollection(Model):
        mongo = MongoCollection(database='test', collection='minimongo.example')

    if __name__ == '__main__':
        obj = MyCollection({'x': 1, 'y': 2}).save()

        res = MyCollection.find({'x': 1})

# TODOs & Upcoming features:

* DB Connection management and pooling.  Existing code is very crude when it
  comes to DB Connection management.  Implement DB connection pools, etc.

* More template-friendly member accessing.  Return None for missing fields?

* Per-object configuration directives.  Read-only, "Rigid" (no schema change
  allowed), etc.

* Support for automatic DBRef field dereferencing.

# Feedback welcome!

Please email github@slacy.com with comments, suggestions, or find
