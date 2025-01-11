import pytest

from heartfelt_hooks.check_snake_case import _is_sausage
from heartfelt_hooks.check_snake_case import _is_sausage_snake
from heartfelt_hooks.check_snake_case import _is_snake


@pytest.mark.parametrize("name", ("-foo", "foo-bar", "f-o-o"))
def test_is_sausage(name):
    assert _is_sausage(name)


@pytest.mark.parametrize("name", ("foo", "foo_bar", "foo-bar_baz"))
def test_is_not_sausage(name):
    assert not _is_sausage(name)


@pytest.mark.parametrize("name", ("_foo", "foo_bar", "f_o_o"))
def test_is_snake(name):
    assert _is_snake(name)


@pytest.mark.parametrize("name", ("-foo", "foo-bar", "foo-bar_baz"))
def test_is_not_snake(name):
    assert not _is_snake(name)


@pytest.mark.parametrize("name", ("_foo-", "foo-bar_baz", "f_o-o"))
def test_is_sausage_snake(name):
    assert _is_sausage_snake(name)


@pytest.mark.parametrize("name", ("-foo", "foo-bar", "foo_bar", "_foo"))
def test_is_not_sausage_snake(name):
    assert not _is_sausage_snake(name)
