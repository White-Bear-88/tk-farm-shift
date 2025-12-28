import sys
import os
import json
import importlib
import types

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock boto3 module at import-time so tests don't need real boto3
mock_boto3 = types.SimpleNamespace(resource=lambda *a, **kw: types.SimpleNamespace(Table=lambda *args, **kwargs: types.SimpleNamespace()))
import sys as _sys
_sys.modules['boto3'] = mock_boto3
# Provide a dummy TABLE_NAME so module import doesn't fail
import os as _os
_os.environ['TABLE_NAME'] = 'DUMMY_TABLE'

import employee_shifts
importlib.reload(employee_shifts)

class DummyTable:
    def __init__(self, items):
        self._items = items
    def query(self, IndexName=None, KeyConditionExpression=None, ExpressionAttributeValues=None):
        # ignore parameters, just return our items
        return {'Items': self._items}


def make_event(emp_id, params):
    return {
        'pathParameters': {'id': emp_id},
        'queryStringParameters': params
    }


def test_month_returns_array(monkeypatch):
    items = [
        {'GSI1SK': '2025-12-01', 'SK': 'EMP#E1#milking', 'start_time': '05:00', 'end_time': '07:00'},
        {'GSI1SK': '2025-12-15', 'SK': 'EMP#E1#feeding', 'start_time': '08:00', 'end_time': '09:00'}
    ]
    monkeypatch.setattr(employee_shifts, 'table', DummyTable(items))

    evt = make_event('E1', {'month': '2025-12'})
    res = employee_shifts.lambda_handler(evt, None)
    assert res['statusCode'] == 200
    body = json.loads(res['body'])
    assert isinstance(body, list)
    assert any(s['date'] == '2025-12-01' for s in body)


def test_date_returns_array(monkeypatch):
    items = [
        {'GSI1SK': '2025-12-15', 'SK': 'EMP#E1#feeding', 'start_time': '08:00', 'end_time': '09:00'}
    ]
    monkeypatch.setattr(employee_shifts, 'table', DummyTable(items))

    evt = make_event('E1', {'date': '2025-12-15'})
    res = employee_shifts.lambda_handler(evt, None)
    assert res['statusCode'] == 200
    body = json.loads(res['body'])
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]['date'] == '2025-12-15'


def test_default_range_returns_array(monkeypatch):
    items = [
        {'GSI1SK': '2025-11-30', 'SK': 'EMP#E1#milking', 'start_time': '05:00', 'end_time': '07:00'},
        {'GSI1SK': '2025-12-02', 'SK': 'EMP#E1#feeding', 'start_time': '08:00', 'end_time': '09:00'}
    ]
    monkeypatch.setattr(employee_shifts, 'table', DummyTable(items))

    evt = make_event('E1', {})
    res = employee_shifts.lambda_handler(evt, None)
    assert res['statusCode'] == 200
    body = json.loads(res['body'])
    assert isinstance(body, list)
    assert len(body) == 2
