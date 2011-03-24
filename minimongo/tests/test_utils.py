# -*- coding: utf-8 -*-

from types import ModuleType

import pytest

from minimongo import Model, Options, configure, to_underscore


def test_nometa():
    configure(database='test')

    try:
        class SomeModel(Model):
            pass
    except Exception:
        pytest.fail('A model with no Meta is perfectly fine :)')

    del Options.database


def test_to_underscore():
    assert to_underscore('Foobar') == 'foobar'
    assert to_underscore('fooBar') == 'foo_bar'
    assert to_underscore('FooBar42') == 'foo_bar42'
    assert to_underscore('Foo42Bar') == 'foo42_bar'


def test_configure():
    # a) keyword arguments
    assert not hasattr(Options, 'foo')
    configure(foo='bar')
    assert hasattr(Options, 'foo')
    del Options.foo

    # b) module
    assert not hasattr(Options, 'foo')
    module = ModuleType('config')
    module.MONGODB_FOO = 'bar'
    module.NON_MONGO_ATTR = 'bar'
    configure(foo='bar')
    assert not hasattr(Options, 'NON_MONGO_ATTR')
    assert not hasattr(Options, 'MONGODB_FOO')
    assert hasattr(Options, 'foo')
    del Options.foo

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

    options = Options(Meta)
    assert options.foo, 'bar'


def test_optoins_configure():
    # Options have no defaults yet -- configure() was never called.
    with pytest.raises(AttributeError):
        Options.foo

    Options.configure(foo='bar')

    try:
        assert Options.foo == 'bar'
    except AttributeError:
        pytest.fail('Options.foo should\'ve been set.')

    del Options.foo
