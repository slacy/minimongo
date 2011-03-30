# -*- coding: utf-8 -*-
from types import ModuleType

import pytest

from minimongo import Model, configure
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
