# -*- coding: utf-8 -*-
from types import ModuleType

import pytest

from minimongo import Model, configure, AttrDict
from minimongo.options import _Options
from minimongo.model import to_underscore


def test_nometa():
    configure(database='test')

    try:
        class SomeModel(Model):
            pass
    except Exception:
        pytest.fail('A model with no Meta is perfectly fine :)')

    del _Options.database


def test_to_underscore():
    assert to_underscore('Foobar') == 'foobar'
    assert to_underscore('fooBar') == 'foo_bar'
    assert to_underscore('FooBar42') == 'foo_bar42'
    assert to_underscore('Foo42Bar') == 'foo42_bar'


def test_configure():
    # a) keyword arguments
    assert not hasattr(_Options, 'foo')
    configure(foo='bar')
    assert hasattr(_Options, 'foo')
    del _Options.foo

    # b) module
    assert not hasattr(_Options, 'foo')
    module = ModuleType('config')
    module.MONGODB_FOO = 'bar'
    module.NON_MONGO_ATTR = 'bar'
    configure(foo='bar')
    assert not hasattr(_Options, 'NON_MONGO_ATTR')
    assert not hasattr(_Options, 'MONGODB_FOO')
    assert hasattr(_Options, 'foo')
    del _Options.foo

    # c) non-module (fails silently)
    try:
        configure(42)
        configure(None)
        configure('foobar')
    except Exception:
        pytest.fail('configure() should fail silently on invalid input.')


def test_options_init():
    class Meta:
        foo = 'bar'

    options = _Options(Meta)
    assert options.foo, 'bar'


def test_optoins_configure():
    # Options have no defaults yet -- configure() was never called.
    with pytest.raises(AttributeError):
        _Options.foo

    configure(foo='bar')

    try:
        assert _Options.foo == 'bar'
    except AttributeError:
        pytest.fail('Options.foo should\'ve been set.')

    del _Options.foo


def test_attr_dict():
    d = AttrDict()
    d.x = 1
    d.y = {}
    d.y.z = 2
    d.q = AttrDict()
    d.q.r = 3
    d.q.s = AttrDict(AttrDict({}))  # I'm just being weird
    d['q']['s']['t'] = 4

    assert d.x == 1
    assert d.y.z == d['y']['z']
    assert d.y.z == 2
    assert d.q.r == d['q']['r']
    assert d.q.r == 3
    assert d.q.s.t == d['q'].s['t']  # Don't do this in real code.
    assert isinstance(d, dict)
    assert isinstance(d.y, dict)
    assert isinstance(d['y'], dict)
    assert isinstance(d.q.s, dict)
    assert isinstance(d['q']['s'], dict)
    assert isinstance(d.q.s, dict)
    assert isinstance(d['q']['s'], dict)

    # We can say AttrDict(AttrDict({'foo': 'bar'})) with no ill effects.
    e = AttrDict(d)
    assert e == d
    assert e.x == 1
    assert e.y.z == d['y']['z']
    assert e.y.z == 2
    assert e.q.r == d['q']['r']
    assert e.q.r == 3
    assert isinstance(e, dict)
    assert isinstance(e.y, dict)
    assert isinstance(e['y'], dict)
    # etc.

