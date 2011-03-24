Example
-------

Here's a very brief example of creating an object, querying for it, modifying
a field, and then saving it back again::

    from minimongo import Model, Index

    class Foo(Model):
        class Meta:
            # Here, we specify the database and collection names.
            # A connection to your DB is automatically created.
            database = "test"
            collection = "minimongo.example"

            # Now, we programatically declare what indices we want.
            # The arguments to the Index constructor are identical to
            # the args to pymongo"s ensure_index function.
            indices = (
                Index("a"),
            )


    if __name__ == "__main__":
        # Create & save an object, and return a local in-memory copy of it:
        foo = Foo({"x": 1, "y": 2}).save()

        # Find that object again, loading it into memory:
        foo = Foo.collection.find_one({"x": 1})

        # Change a field value, and save it back to the DB.
        foo.other = "some data"
        foo.save()
