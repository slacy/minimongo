# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import pytest
from bson import DBRef
from pymongo.errors import DuplicateKeyError

from .. import Collection, Index, Model


class TestCollection(Collection):
    def custom(self):
        return 'It works!'


class TestModel(Model):
    '''Model class for test cases.'''
    class Meta:
        database = 'minimongo_test'
        collection = 'minimongo_test'
        indices = (
            Index('x'),
        )

    def a_method(self):
        self.x = 123
        self.y = 456
        self.save()


class TestModelCollection(Model):
    '''Model class with a custom collection class.'''
    class Meta:
        database = 'minimongo_test'
        collection = 'minimongo_collection'
        collection_class = TestCollection


class TestModelUnique(Model):
    class Meta:
        database = 'minimongo_test'
        collection = 'minimongo_unique'
        indices = (
            Index('x', unique=True),
        )


class TestDerivedModel(TestModel):
    class Meta:
        database = 'minimongo_test'
        collection = 'minimongo_derived'


class TestNoAutoIndexModel(Model):
    class Meta:
        database = 'minimongo_test'
        collection = 'minimongo_noidex'
        indices = (
            Index('x'),
        )
        auto_index = False


class TestModelInterface(Model):
    class Meta:
        interface = True


class TestModelImplementation(TestModelInterface):
    class Meta:
        database = 'minimongo_test'
        collection = 'minimongo_impl'


class TestFieldMapper(Model):
    class Meta:
        database = 'minimongo_test'
        collection = 'minimongo_mapper'
        field_map = (
            (lambda k, v: k == 'x' and isinstance(v, int),
             lambda v: float(v * (4.0 / 3.0))),
        )


def setup():
    # Make sure we start with a clean, empty DB.
    TestModel.connection.drop_database(TestModel.database)

    # Create indices up front
    TestModel.auto_index()
    TestModelUnique.auto_index()


def teardown():
    # This will drop the entire minimongo_test database.  Careful!
    TestModel.connection.drop_database(TestModel.database)


def test_meta():
    assert hasattr(TestModel, '_meta')
    assert not hasattr(TestModel, 'Meta')

    meta = TestModel._meta

    for attr in ('host', 'port', 'indices', 'database',
                 'collection', 'collection_class'):
        assert hasattr(meta, attr)

    assert meta.database == 'minimongo_test'
    assert meta.collection == 'minimongo_test'
    assert meta.indices == (Index('x'), )


def test_dictyness():
    item = TestModel({'x': 642})

    assert item['x'] == item.x == 642

    item.y = 426
    assert item['y'] == item.y == 426

    assert set(item.keys()) == set(['x', 'y'])

    del item['x']
    assert item == {'y': 426}
    item.z = 3
    del item.y
    assert item == {'z': 3}


def test_creation():
    '''Test simple object creation and querying via find_one.'''
    object_a = TestModel({'x': 1, 'y': 1})
    object_a.z = 1
    object_a.save()

    object_b = TestModel.collection.find_one({'x': 1})

    # Make sure that the find_one method returns the right type.
    assert isinstance(object_b, TestModel)
    # Make sure that the contents are the same.
    assert object_b == object_a

    # Make sure that our internal representation is what we expect (and
    # no extra fields, etc.)
    assert object_a == {'x': 1, 'y': 1, 'z': 1, '_id': object_a._id}
    assert object_b == {'x': 1, 'y': 1, 'z': 1, '_id': object_b._id}


def test_find_one():
    model = TestModel({'x': 1, 'y': 1})
    model.save()

    assert model._id is not None

    found = TestModel.collection.find_one(model._id)
    assert found is not None
    assert isinstance(found, TestModel)
    assert found == model


def test_save_with_arguments():
    # Manipulate is what inserts the _id on save if it is missing
    model = TestModel(foo=0)
    model.save(manipulate=False)
    with pytest.raises(AttributeError):
        model._id

    # but the object was actually saved
    model = TestModel.collection.find_one({'foo': 0})
    assert model.foo == 0


def test_mongo_update():
    """Test update. note that update does not sync back the server copy."""
    model = TestModel(counter=10, x=0, y=1)
    model.save()

    # NOTE: These tests below could be thought of outlining existing
    # edge-case behavior (i.e. they're bugs) and they should be fixed and
    # the behavior made more correct/consistent.

    # Update will not delete missing attributes, so at this point our
    # local copy is out of sync with what's on the server.
    model.y = 1
    del model.x
    model.update()
    assert model.get('x', 'foo') == 'foo'

    # $inc changes the server, not the local copy.
    model.mongo_update({'$inc': {'counter': 1}})
    assert model.counter == 10

    # reload the model.  This will pull in the "true" document from the server.
    model = TestModel.collection.find_one({'_id': model._id})
    assert model.counter == 11
    assert model.x == 0
    assert model.y == 1


def test_load():
    """Partial loading of documents.x"""
    # object_a and object_b are 2 instances of the same document
    object_a = TestModel(x=0, y=1).save()
    object_b = TestModel(_id=object_a._id)
    with pytest.raises(AttributeError):
        object_b.x

    # Partial load. only the x value
    object_b.load(fields={'x': 1})
    assert object_b.x == object_a.x
    with pytest.raises(AttributeError):
        object_b.y

    # Complete load. change the value first
    object_a.x = 2
    object_a.save()
    object_b.load()
    assert object_b.x == 2
    assert object_b.y == object_a.y


def test_load_and_field_mapper():
    object_a = TestFieldMapper(x=12, y=1).save()
    object_b = TestFieldMapper(_id=object_a._id)

    # X got mapped (multiplied by 4/3 and converted to object_a float)
    assert object_a.x == 16.0
    assert object_a.y == 1

    object_b.load(fields={'x': 1})
    assert object_b.x == 16.0
    with pytest.raises(AttributeError):
        object_b.y  # object_b does not have the 'y' field

    object_b.load()
    assert object_b.y == 1


def test_index_existance():
    '''Test that indexes were created properly.'''
    indices = TestModel.collection.index_information()
    # Even though PyMongo documents that indices should not contain
    # "ns", the seem to do in practice.
    assert "x_1" in indices
    assert indices["x_1"]["key"] == [("x", 1)]


@pytest.mark.xfail(reason="drop_dups is unsupported since MongoDB 2.7.5")
def test_unique_index():
    '''Test behavior of indices with unique=True'''
    # This will work (y is undefined)
    TestModelUnique({'x': 1}).save()
    TestModelUnique({'x': 1}).save()

    # Assert that there's only one object in the collection, even though
    # we inserted two.  The uniqueness constraint on the index has dropped
    # one of the inserts (silently, I guess).
    assert TestModelUnique.collection.find().count() == 1

    # Even if we use different values for y, it's still only one object:
    TestModelUnique({'x': 2, 'y': 1}).save()
    TestModelUnique({'x': 2, 'y': 2}).save()
    # There are now 2 objects, one with x=1, one with x=2.
    assert TestModelUnique.collection.find().count() == 2


def test_unique_constraint():
    x1_a = TestModelUnique({'x': 1, 'y': 1})
    x1_b = TestModelUnique({'x': 1, 'y': 2})
    x1_a.save(safe=True)

    with pytest.raises(DuplicateKeyError):
        x1_b.save(safe=True)

    x1_c = TestModelUnique({'x': 2, 'y': 1})
    x1_c.save()


def test_queries():
    '''Test some more complex query forms.'''
    object_a = TestModel({'x': 1, 'y': 1}).save()
    object_b = TestModel({'x': 1, 'y': 2}).save()
    object_c = TestModel({'x': 2, 'y': 2}).save()
    object_d = TestModel({'x': 2, 'y': 1}).save()

    found_x1 = TestModel.collection.find({'x': 1})
    found_y1 = TestModel.collection.find({'y': 1})
    found_x2y2 = TestModel.collection.find({'x': 2, 'y': 2})

    list_x1 = list(found_x1)
    list_y1 = list(found_y1)
    list_x2y2 = list(found_x2y2)

    # make sure the types of the things coming back from find() are the
    # derived Model types, not just a straight dict.
    assert isinstance(list_x1[0], TestModel)

    assert object_a in list_x1
    assert object_b in list_x1
    assert object_a in list_y1
    assert object_d in list_y1
    assert object_c == list_x2y2[0]


def test_deletion():
    '''Test deleting an object from a collection.'''
    object_a = TestModel()
    object_a.x = 100
    object_a.y = 200
    object_a.save()

    object_b = TestModel.collection.find({'x': 100})
    assert object_b.count() == 1
    object_b[0].remove()

    object_a = TestModel.collection.find({'x': 100})
    assert object_a.count() == 0


def test_complex_types():
    '''Test lists as types.'''
    object_a = TestModel()
    object_a.l = ['a', 'b', 'c']
    object_a.x = 1
    object_a.y = {'m': 'n',
                  'o': 'p'}
    object_a['z'] = {'q': 'r',
                     's': {'t': ''}}

    object_a.save()

    object_b = TestModel.collection.find_one({'x': 1})

    # Make sure the internal lists are equivalent.
    assert object_a.l == object_b.l

    # Make sure that everything is of the right type, including the types of
    # the nested fields that we read back from the DB, and that we are able
    # to access fields as both attrs and items.
    assert type(object_a) == type(object_b) == TestModel
    assert isinstance(object_a.y, dict)
    assert isinstance(object_b.y, dict)
    assert isinstance(object_a['z'], dict)
    assert isinstance(object_b['z'], dict)
    assert isinstance(object_a.z, dict)
    assert isinstance(object_b.z, dict)

    # These nested fields are actually instances of AttrDict, which is why
    # we can access as both attributes and values.  Thus, the "isinstance"
    # dict check.
    assert isinstance(object_a['z']['s'], dict)
    assert isinstance(object_b['z']['s'], dict)
    assert isinstance(object_a.z.s, dict)
    assert isinstance(object_b.z.s, dict)

    assert object_a == object_b


def test_type_from_cursor():
    for i in range(6):
        TestModel({'x': i}).save()

    objects = TestModel.collection.find()
    for single_object in objects:
        assert type(single_object) == TestModel
        # Make sure it's both a dict and a TestModel, which is also an object
        assert isinstance(single_object, dict)
        assert isinstance(single_object, object)
        assert isinstance(single_object, TestModel)
        assert isinstance(single_object['x'], int)


def test_delete_field():
    '''Test deleting a single field from an object.'''
    object_a = TestModel({'x': 1, 'y': 2})
    object_a.save()
    del object_a.x
    object_a.save()

    assert TestModel.collection.find_one({'y': 2}) == {
        'y': 2, '_id': object_a._id
    }


def test_count_and_fetch():
    '''Test counting methods on Cursors. '''
    object_d = TestModel({'x': 1, 'y': 4}).save()
    object_b = TestModel({'x': 1, 'y': 2}).save()
    object_a = TestModel({'x': 1, 'y': 1}).save()
    object_c = TestModel({'x': 1, 'y': 3}).save()

    find_x1 = TestModel.collection.find({'x': 1}).sort('y')
    assert find_x1.count() == 4

    list_x1 = list(find_x1)
    assert list_x1[0] == object_a
    assert list_x1[1] == object_b
    assert list_x1[2] == object_c
    assert list_x1[3] == object_d


def test_fetch_and_limit():
    '''Test counting methods on Cursors. '''
    object_a = TestModel({'x': 1, 'y': 1}).save()
    object_b = TestModel({'x': 1, 'y': 2}).save()
    TestModel({'x': 1, 'y': 4}).save()
    TestModel({'x': 1, 'y': 3}).save()

    find_x1 = TestModel.collection.find({'x': 1}).limit(2).sort('y')

    assert find_x1.count(with_limit_and_skip=True) == 2
    assert object_a in find_x1
    assert object_b in find_x1


def test_dbref():
    '''Test generation of DBRef objects, and querying via DBRef
    objects.'''
    object_a = TestModel({'x': 1, 'y': 999}).save()
    ref_a = object_a.dbref()

    object_b = TestModel.collection.from_dbref(ref_a)
    assert object_a == object_b

    # Making sure, that a ValueError is raised for DBRefs from a
    # 'foreign' collection or database.
    with pytest.raises(ValueError):
        ref_a = DBRef('foo', ref_a.id)
        TestModel.collection.from_dbref(ref_a)

    with pytest.raises(ValueError):
        ref_a = DBRef(ref_a.collection, ref_a.id, 'foo')
        TestModel.collection.from_dbref(ref_a)

    # Testing ``with_database`` option.
    ref_a = object_a.dbref(with_database=False)
    assert ref_a.database is None

    ref_a = object_a.dbref(with_database=True)
    assert ref_a.database is not None

    ref_a = object_a.dbref()  # True by default.
    assert ref_a.database is not None

    # Testing additional fields
    ref_a = object_a.dbref(name="foo")
    assert ref_a.name == 'foo'


def test_db_and_collection_names():
    '''Test the methods that return the current class's DB and
    Collection names.'''
    object_a = TestModel({'x': 1})
    assert object_a.database.name == 'minimongo_test'
    assert TestModel.database.name == 'minimongo_test'
    assert object_a.collection.name == 'minimongo_test'
    assert TestModel.collection.name == 'minimongo_test'


def test_derived():
    '''Test Models that are derived from other models.'''
    derived_object = TestDerivedModel()
    derived_object.a_method()

    assert derived_object.database.name == 'minimongo_test'
    assert derived_object.collection.name == 'minimongo_derived'

    assert TestDerivedModel.collection.find_one({'x': 123}) == derived_object


def test_collection_class():
    model = TestModelCollection()

    assert isinstance(model.collection, TestCollection)
    assert hasattr(model.collection, 'custom')
    assert model.collection.custom() == 'It works!'


def test_str():
    assert str(TestModel()) == 'TestModel({})'
    assert str(TestModel({'foo': 'bar'})) == 'TestModel({\'foo\': \'bar\'})'

    assert str(TestModel({'foo': 'bar'})) == 'TestModel({\'foo\': \'bar\'})'


def test_auto_collection_name():
    try:
        class SomeModel(Model):
            class Meta:
                database = 'minimongo_test'
    except Exception:
        pytest.fail('`collection_name` should\'ve been constructed.')

    assert SomeModel.collection.name == 'some_model'


def test_no_auto_index():
    TestNoAutoIndexModel({'x': 1}).save()

    indices = TestNoAutoIndexModel.collection.index_information()
    assert indices["_id_"]["key"] == [("_id", 1)]

    TestNoAutoIndexModel.auto_index()

    indices = TestNoAutoIndexModel.collection.index_information()
    assert indices["_id_"]["key"] == [("_id", 1)]
    assert indices["x_1"]["key"] == [("x", 1)]


def test_interface_models():
    test_interface_instance = TestModelInterface()
    test_interface_instance.x = 5
    with pytest.raises(Exception):
        test_interface_instance.save()

    test_model_instance = TestModelImplementation()
    test_model_instance.x = 123
    test_model_instance.save()

    test_model_instance_2 = TestModelImplementation.collection.find_one(
        {'x': 123})
    assert test_model_instance == test_model_instance_2


def test_field_mapper():
    test_mapped_object = TestFieldMapper()
    # x is going to be multiplied by 4/3 automatically.
    test_mapped_object.x = 6
    test_mapped_object.y = 7
    test_mapped_object.z = 6.0
    assert test_mapped_object.x == 8.0
    assert test_mapped_object.y == 7
    assert test_mapped_object.z == 6.0
    assert type(test_mapped_object.x) == float
    assert type(test_mapped_object.y) == int
    assert type(test_mapped_object.z) == float
    test_mapped_object.save()

    loaded_mapped_object = TestFieldMapper.collection.find_one()

    # When the object was loaded from the database, the mapper automatically
    # multiplied every integer field by 4.0/3.0 and converted it to a float.
    # This is a crazy use case only used for testing here.
    assert test_mapped_object.x == 8.0
    assert test_mapped_object.y == 7
    assert test_mapped_object.z == 6.0

    assert type(loaded_mapped_object.x) == float
    assert type(test_mapped_object.x) == float

    assert type(loaded_mapped_object.y) == int
    assert type(loaded_mapped_object.z) == float


def test_slicing():
    object_a = TestModel({'x': 1}).save()
    object_b = TestModel({'x': 2}).save()
    object_c = TestModel({'x': 3}).save()
    object_d = TestModel({'x': 4}).save()
    object_e = TestModel({'x': 5}).save()

    objects = TestModel.collection.find().sort('x')
    obj_list = list(objects[:2])
    assert obj_list == [object_a, object_b]
    assert type(obj_list[0]) == TestModel
    assert type(obj_list[1]) == TestModel

    # We can't re-slice an already sliced cursor, so we query again.
    objects = TestModel.collection.find().sort('x')
    obj_list = list(objects[2:])
    assert obj_list == [object_c, object_d, object_e]
    assert type(obj_list[0] == TestModel)
    assert type(obj_list[1] == TestModel)
    assert type(obj_list[2] == TestModel)
