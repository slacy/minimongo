import unittest

from minimongo.model import Model, MongoCollection

class TestModel(Model):
    mongo = MongoCollection(database='test', collection='minimongo_test')


def assertContains(iterator, instance):
    for i in iterator:
        if i.rawdata == instance.rawdata:
            return True
    return False


class TestSimpleModel(unittest.TestCase):
    def setUp(self):
        TestModel.drop_collection()

    def test_creation(self):
        m = TestModel({'x':1, 'y':1})
        m.save()
        n = TestModel.find_one({'x': 1})
        self.assertEqual(n.rawdata, m.rawdata)

    def test_queries(self):
        a = TestModel({'x': 1, 'y': 1}).save()
        b = TestModel({'x': 1, 'y': 2}).save()
        c = TestModel({'x': 2, 'y': 2}).save()
        d = TestModel({'x': 2, 'y': 1}).save()

        x1 = TestModel.find({'x': 1})
        y1 = TestModel.find({'y': 1})
        x2y2 = TestModel.find({'x': 2, 'y': 2})

        lx1 = list(x1)
        ly1 = list(y1)
        lx2y2 = list(x2y2)
        self.assertTrue(assertContains(lx1, a))
        self.assertTrue(assertContains(lx1, b))
        self.assertTrue(assertContains(ly1, a))
        self.assertTrue(assertContains(ly1, d))
        self.assertEqual(lx2y2[0].rawdata, c.rawdata)

    def test_deletion(self):
        m = TestModel()
        m.x = 100
        m.y = 200
        m.save()

        n = TestModel.find({'x': 100})
        self.assertEqual(n.count(), 1)
        for i in n:
            i.delete()

        m = TestModel.find({'x': 100})
        self.assertEqual(m.count(), 0)

    def test_complex_types(self):
        m = TestModel()
        m.l = ['a', 'b', 'c']
        m.x = 1
        m.save()

        n = TestModel.find_one({'x': 1})
        self.assertEqual(m.l, n.l)

    def test_delete_field(self):
        m = TestModel({'x': 1, 'y': 2})
        m.save()
        del(m.x)
        m.save()

        n = TestModel.find_one({'y': 2})
        self.assertEqual(n.rawdata, {'y': 2, '_id': m._id})

    def test_count_and_fetch(self):
        a = TestModel({'x': 1, 'y': 1}).save()
        b = TestModel({'x': 1, 'y': 2}).save()
        c = TestModel({'x': 1, 'y': 3}).save()
        d = TestModel({'x': 1, 'y': 4}).save()

        m = TestModel.find({'x': 1}).sort('y')
        self.assertEqual(m.count(), 4)
        l = list(m)
        self.assertEqual(l[0].rawdata, a.rawdata)
        self.assertEqual(l[1].rawdata, b.rawdata)
        self.assertEqual(l[2].rawdata, c.rawdata)
        self.assertEqual(l[3].rawdata, d.rawdata)


if __name__ == '__main__':
    unittest.main()
