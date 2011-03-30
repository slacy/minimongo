# -*- coding: utf-8 -*-
from __future__ import with_statement

import operator

import pytest
from pymongo.dbref import DBRef
from pymongo.errors import DuplicateKeyError

from minimongo import Collection, Index, Model

class TestCollection(Collection):
    def custom(self):
        return 'It works!'


class TestModel(Model):
    '''Model class for test cases.'''
    class Meta:
        database = 'test'
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
        database = 'test'
        collection = 'minimongo_collection'
        collection_class = TestCollection


class TestModelUnique(Model):
    class Meta:
        database = 'test'
        collection = 'minimongo_unique'
        indices = (
            Index('x', unique=True),
        )


class TestDerivedModel(TestModel):
    class Meta:
        database = 'test'
        collection = 'minimongo_derived'


class TestNoAutoIndexModel(Model):
    class Meta:
        database = 'test'
        collection = 'minimongo_noidex'
        indices = (
            Index('x'),
        )
        auto_index = False


def setup():
    TestModel.auto_index()
    TestModelUnique.auto_index()


def teardown():
    map(lambda m: m.collection.drop(),
        Model.__subclasses__() + [TestDerivedModel])


def test_meta():
    assert hasattr(TestModel, '_meta')
    assert not hasattr(TestModel, 'Meta')

    meta = TestModel._meta

    for attr in ('host', 'port', 'indices', 'database',
                 'collection', 'collection_class'):
        assert hasattr(meta, attr)

    assert meta.database == 'test'
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
    dummy_m = TestModel({'x': 1, 'y': 1})
    dummy_m.z = 1
    dummy_m.save()

    dummy_n = TestModel.collection.find_one({'x': 1})

    # Make sure that the find_one method returns the right type.
    assert isinstance(dummy_n, TestModel)
    # Make sure that the contents are the same.
    assert dummy_n == dummy_m

    # Make sure that our internal representation is what we expect (and
    # no extra fields, etc.)
    assert dummy_m == {'x': 1, 'y': 1, 'z': 1, '_id': dummy_m._id}
    assert dummy_n == {'x': 1, 'y': 1, 'z': 1, '_id': dummy_n._id}


def test_find_one():
    model = TestModel({'x': 1, 'y': 1})
    model.save()

    assert model._id is not None

    found = TestModel.collection.find_one(model._id)
    assert found is not None
    assert isinstance(found, TestModel)
    assert found == model


def test_index_existance():
    '''Test that indexes were created properly.'''
    indices = TestModel.collection.index_information()
    assert indices['x_1'] == {'key': [('x', 1)]}


def test_unique_index():
    '''Test behavior of indices with unique=True'''
    # This will work (y is undefined)
    TestModelUnique({'x': 1}).save()
    TestModelUnique({'x': 1}).save()
    # Assert that there's only one object in the collection, even though
    # we inserted two.  The uniqueness constraint on the index has dropped
    # one of the inserts (silently, I guess).
    assert TestModelUnique.collection.find().count() == 1

    # Even if we use dieferent values for y, it's still only one object:
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
    dummy_a = TestModel({'x': 1, 'y': 1}).save()
    dummy_b = TestModel({'x': 1, 'y': 2}).save()
    dummy_c = TestModel({'x': 2, 'y': 2}).save()
    dummy_d = TestModel({'x': 2, 'y': 1}).save()

    found_x1 = TestModel.collection.find({'x': 1})
    found_y1 = TestModel.collection.find({'y': 1})
    found_x2y2 = TestModel.collection.find({'x': 2, 'y': 2})

    list_x1 = list(found_x1)
    list_y1 = list(found_y1)
    list_x2y2 = list(found_x2y2)

    # make sure the types of the things coming back from find() are the
    # derived Model types, not just a straight dict.
    assert isinstance(list_x1[0], TestModel)

    assert dummy_a in list_x1
    assert dummy_b in list_x1
    assert dummy_a in list_y1
    assert dummy_d in list_y1
    assert dummy_c == list_x2y2[0]


def test_deletion():
    '''Test deleting an object from a collection.'''
    dummy_m = TestModel()
    dummy_m.x = 100
    dummy_m.y = 200
    dummy_m.save()

    dummy_n = TestModel.collection.find({'x': 100})
    assert dummy_n.count() == 1

    map(operator.methodcaller('remove'), dummy_n)

    dummy_m = TestModel.collection.find({'x': 100})
    assert dummy_m.count() == 0


def test_complex_types():
    '''Test lists as types.'''
    dummy_m = TestModel()
    dummy_m.l = ['a', 'b', 'c']
    dummy_m.x = 1
    dummy_m.y = {'m': 'n',
                 'o': 'p'}
    dummy_m.save()

    dummy_n = TestModel.collection.find_one({'x': 1})

    # Make sure the internal lists are equivalent.
    assert dummy_m.l == dummy_n.l

    # There's a bug in pymongo here.  The following assert will fire:
    # self.assertEqual(type(dummy_m.y), type(dummy_n.y))
    # with AssertionError: <type 'dict'> != <class '__main__.TestModel'>
    # because as_class is applied recursively.  Ugh!

    assert dummy_m == dummy_n


def test_delete_field():
    '''Test deleting a single field from an object.'''
    dummy_m = TestModel({'x': 1, 'y': 2})
    dummy_m.save()
    del dummy_m.x
    dummy_m.save()

    assert TestModel.collection.find_one({'y': 2}) == \
           {'y': 2, '_id': dummy_m._id}


def test_count_and_fetch():
    '''Test counting methods on Cursors. '''
    dummy_d = TestModel({'x': 1, 'y': 4}).save()
    dummy_b = TestModel({'x': 1, 'y': 2}).save()
    dummy_a = TestModel({'x': 1, 'y': 1}).save()
    dummy_c = TestModel({'x': 1, 'y': 3}).save()

    find_x1 = TestModel.collection.find({'x': 1}).sort('y')
    assert find_x1.count() == 4

    list_x1 = list(find_x1)
    assert list_x1[0] == dummy_a
    assert list_x1[1] == dummy_b
    assert list_x1[2] == dummy_c
    assert list_x1[3] == dummy_d


def test_fetch_and_limit():
    '''Test counting methods on Cursors. '''
    dummy_a = TestModel({'x': 1, 'y': 1}).save()
    dummy_b = TestModel({'x': 1, 'y': 2}).save()
    TestModel({'x': 1, 'y': 4}).save()
    TestModel({'x': 1, 'y': 3}).save()

    find_x1 = TestModel.collection.find({'x': 1}).limit(2).sort('y')

    assert find_x1.count(with_limit_and_skip=True) == 2
    assert dummy_a in find_x1
    assert dummy_b in find_x1

def test_dbref():
    '''Test generation of DBRef objects, and querying via DBRef
    objects.'''
    dummy_a = TestModel({'x': 1, 'y': 999}).save()
    ref_a = dummy_a.dbref()

    dummy_b = TestModel.collection.from_dbref(ref_a)
    assert dummy_a == dummy_b

    # Making sure, that a ValueError is raised for DBRefs from a
    # 'foreign' collection or database.
    with pytest.raises(ValueError):
        ref_a = DBRef('foo', ref_a.id)
        TestModel.collection.from_dbref(ref_a)

    with pytest.raises(ValueError):
        ref_a = DBRef(ref_a.collection, ref_a.id, 'foo')
        TestModel.collection.from_dbref(ref_a)

    # Testing ``with_database`` option.
    ref_a = dummy_a.dbref(with_database=False)
    assert ref_a.database is None

    ref_a = dummy_a.dbref(with_database=True)
    assert ref_a.database is not None

    ref_a = dummy_a.dbref()  # True by default.
    assert ref_a.database is not None


def test_db_and_collection_names():
    '''Test the methods that return the current class's DB and
    Collection names.'''
    dummy_a = TestModel({'x': 1})
    assert dummy_a.database.name == 'test'
    assert TestModel.database.name == 'test'
    assert dummy_a.collection.name == 'minimongo_test'
    assert TestModel.collection.name == 'minimongo_test'


def test_derived():
    '''Test Models that are derived from other models.'''
    der = TestDerivedModel()
    der.a_method()

    assert der.database.name == 'test'
    assert der.collection.name == 'minimongo_derived'

    assert TestDerivedModel.collection.find_one({'x': 123}) == der


def test_collection_class():
    model = TestModelCollection()

    assert isinstance(model.collection, TestCollection)
    assert hasattr(model.collection, 'custom')
    assert model.collection.custom() == 'It works!'


def test_str_and_unicode():
    assert str(TestModel()) == 'TestModel({})'
    assert str(TestModel({'foo': 'bar'})) == 'TestModel({\'foo\': \'bar\'})'

    assert unicode(TestModel({'foo': 'bar'})) == \
           u'TestModel({\'foo\': \'bar\'})'

    # __unicode__() doesn't decode any bytestring values to unicode,
    # leaving it up to the user.
    assert unicode(TestModel({'foo': '←'})) ==  \
           u'TestModel({\'foo\': \'\\xe2\\x86\\x90\'})'
    assert unicode(TestModel({'foo': u'←'})) == \
           u'TestModel({\'foo\': u\'\\u2190\'})'


def test_auto_collection_name():
    try:
        class SomeModel(Model):
            class Meta:
                database = 'test'
    except Exception:
        pytest.fail('`collection_name` should\'ve been constructed.')

    assert SomeModel.collection.name == 'some_model'


def test_no_auto_index():
    TestNoAutoIndexModel({'x': 1}).save()

    assert TestNoAutoIndexModel.collection.index_information() == \
           {u'_id_': {u'key': [(u'_id', 1)]}}

    TestNoAutoIndexModel.auto_index()

    assert TestNoAutoIndexModel.collection.index_information() == \
           {u'_id_': {u'key': [(u'_id', 1)]},
            u'x_1': {u'key': [(u'x', 1)]}}
