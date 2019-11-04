import json
import pytest
from att.handlers import make_login_response


def test_none_user_id():
    assert json.loads(make_login_response(None).body) == {'error': 'auth failed'}


def test_empty_user_id():
    assert json.loads(make_login_response('').body) == {'user_id': ''}


def test_integer_user_id():
    assert json.loads(make_login_response(1).body) == {'user_id': '1'}


def test_string_user_id():
    assert json.loads(make_login_response('id').body) == {'user_id': 'id'}


def test_implemented():

    class TestID:
        def __str__(self):
            return 'Test ID'

    assert json.loads(make_login_response(TestID()).body) == {'user_id': 'Test ID'}


def test_not_implemented():

    class TestID:
        def __str__(self):
            raise NotImplementedError

    with pytest.raises(NotImplementedError):
        make_login_response(TestID())
