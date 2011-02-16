import unittest

from minimongo.model import Model, MongoCollection, Index


class TestModel(Model):
    """Model class for test cases."""
    mongo = MongoCollection(database='test', collection='minimongo_test')
    indices = (Index('x'),)

    def a_method(self):
        self.x = 123
        self.y = 456
        self.save()

class TestModelUnique(Model):
    mongo = MongoCollection(database='test', collection='minimongo_unique')
    indices = (Index('x', unique=True),)


class TestDerivedModel(TestModel):
    mongo = MongoCollection(database='test', collection='minimongo_derived')



def assertContains(iterator, instance):
    """Given an iterable of Models, make sure that the instance (of a Model)
    is inside the iterable."""
    for i in iterator:
        if i == instance:
            return True
    return False

class TestSimpleModel(unittest.TestCase):
    """Main test case."""
    def setUp(self):
        """unittest setup, drop all collections, and rebuild indices before
        starting each test."""
        TestModel.collection.drop()
        TestModel.auto_index()

        TestModelUnique.collection.drop()
        TestModelUnique.auto_index()

        TestDerivedModel.collection.drop()

    def tearDown(self):
        """unittest teardown, drop all collections."""
        # TestModel.collection.drop()
        # TestModelUnique.collection.drop()
        # TestDerivedModel.collection.drop()

    def test_dictyness(self):
        item = TestModel({'x': 642})

        self.assertEqual(item['x'], 642)
        self.assertEqual(item.x, 642)

        item.y = 426
        self.assertEqual(item['y'], 426)
        self.assertEqual(item.y, 426)

        self.assertEqual(sorted(item.keys()), ['x', 'y'])


    def test_creation(self):
        """Test simple object creation and querying via find_one."""
        dummy_m = TestModel({'x': 1, 'y': 1})
        dummy_m.z = 1
        dummy_m.save()

        dummy_n = TestModel.collection.find_one({'x': 1})

        # Make sure that the find_one method returns the right type.
        self.assertEqual(type(dummy_n), TestModel)
        # Make sure that the contents are the same.
        self.assertEqual(dummy_n, dummy_m)

        # Make sure that our internal representation is what we expect (and
        # no extra fields, etc.)
        self.assertEqual(dummy_m, {'x': 1, 'y': 1, 'z': 1, '_id': dummy_m._id})
        self.assertEqual(dummy_n, {'x': 1, 'y': 1, 'z': 1, '_id': dummy_n._id})

    def test_index_existance(self):
        """Test that indexes were created properly."""
        indices = TestModel.collection.index_information()
        self.assertEqual(indices['x_1'],
                         {'key': [('x', 1)]})


    def test_unique_index(self):
        """Test behavior of indices with unique=True"""
        # This will work (y is undefined)
        x1_a = TestModelUnique({'x': 1}).save()
        x1_b = TestModelUnique({'x': 1}).save()
        # Assert that there's only one object in the collection, even though
        # we inserted two.  The uniqueness constraint on the index has
        # dropped one of the inserts (silently, I guess).x
        self.assertEqual(TestModelUnique.collection.find().count(), 1)

        # Even if we use different values for y, it's still only one object:
        x2_a = TestModelUnique({'x': 2, 'y': 1}).save()
        x2_b = TestModelUnique({'x': 2, 'y': 2}).save()
        # There are now 2 objects, one with x=1, one with x=2.
        self.assertEqual(TestModelUnique.collection.find().count(), 2)

    def test_queries(self):
        """Test some more complex query forms."""
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
        self.assertEqual(type(list_x1[0]), TestModel)

        self.assertTrue(assertContains(list_x1, dummy_a))
        self.assertTrue(assertContains(list_x1, dummy_b))
        self.assertTrue(assertContains(list_y1, dummy_a))
        self.assertTrue(assertContains(list_y1, dummy_d))
        self.assertEqual(list_x2y2[0], dummy_c)

    def test_deletion(self):
        """Test deleting an object from a collection."""
        dummy_m = TestModel()
        dummy_m.x = 100
        dummy_m.y = 200
        print "calling save"
        dummy_m.save()

        dummy_n = TestModel.collection.find({'x': 100})
        self.assertEqual(dummy_n.count(), 1)
        for i in dummy_n:
            i.remove()

        dummy_m = TestModel.collection.find({'x': 100})
        self.assertEqual(dummy_m.count(), 0)

    def test_complex_types(self):
        """Test lists as types."""
        dummy_m = TestModel()
        dummy_m.l = ['a', 'b', 'c']
        dummy_m.x = 1
        dummy_m.save()

        dummy_n = TestModel.collection.find_one({'x': 1})

        ml = dummy_m.l
        nl = dummy_n.l
        self.assertEqual(ml, nl)

    def test_delete_field(self):
        """Test deleting a single field from an object."""
        dummy_m = TestModel({'x': 1, 'y': 2})
        dummy_m.save()
        del(dummy_m.x)
        dummy_m.save()

        n = TestModel.collection.find_one({'y': 2})
        self.assertEqual(n, {'y': 2, '_id': dummy_m._id})

    def test_count_and_fetch(self):
        """Test counting methods on Cursors. """
        dummy_d = TestModel({'x': 1, 'y': 4}).save()
        dummy_b = TestModel({'x': 1, 'y': 2}).save()
        dummy_a = TestModel({'x': 1, 'y': 1}).save()
        dummy_c = TestModel({'x': 1, 'y': 3}).save()

        find_x1 = TestModel.collection.find({'x': 1}).sort('y')
        self.assertEqual(find_x1.count(), 4)
        list_x1 = list(find_x1)
        self.assertEqual(list_x1[0], dummy_a)
        self.assertEqual(list_x1[1], dummy_b)
        self.assertEqual(list_x1[2], dummy_c)
        self.assertEqual(list_x1[3], dummy_d)

    def test_fetch_and_limit(self):
        """Test counting methods on Cursors. """
        dummy_d = TestModel({'x': 1, 'y': 4}).save()
        dummy_b = TestModel({'x': 1, 'y': 2}).save()
        dummy_a = TestModel({'x': 1, 'y': 1}).save()
        dummy_c = TestModel({'x': 1, 'y': 3}).save()

        find_x1 = TestModel.collection.find({'x': 1}).limit(2).sort('y')
        # Huh, calling count() on a find() with a limit() returns the total
        # number of elements matched.  Maybe I'm calling it wrong?
        # self.assertEqual(find_x1.count(), 2)
        list_x1 = list(find_x1)
        self.assertEqual(len(list_x1), 2)
        self.assertEqual(list_x1[0], dummy_a)
        self.assertEqual(list_x1[1], dummy_b)

    def test_dbref(self):
        """Test generation of DBRef objects, and querying via DBRef
        objects."""
        dummy_a = TestModel({'x': 1, 'y': 999}).save()
        ref_a = dummy_a.dbref()

        dummy_b = TestModel.collection.from_dbref(ref_a)
        self.assertEqual(dummy_a, dummy_b)

    def test_db_and_collection_names(self):
        """Test the methods that return the current class's DB and
        Collection names."""
        dummy_a = TestModel({'x': 1})
        self.assertEqual(dummy_a.database.name, 'test')
        self.assertEqual(TestModel.database.name, 'test')
        self.assertEqual(dummy_a.collection.name, 'minimongo_test')
        self.assertEqual(TestModel.collection.name, 'minimongo_test')

    def test_derived(self):
        """Test Models that are derived from other models."""
        der = TestDerivedModel()
        der.a_method()

        self.assertEqual(der.database.name, 'test')
        self.assertEqual(der.collection.name, 'minimongo_derived')

        found = TestDerivedModel.collection.find_one({'x': 123})
        self.assertEqual(der, found)


if __name__ == '__main__':
    unittest.main()
