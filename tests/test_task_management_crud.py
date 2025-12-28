import sys, os, json, importlib
os.environ.setdefault('TABLE_NAME', 'TEST_TABLE')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import task_management_crud
importlib.reload(task_management_crud)

class DummyTable:
    def __init__(self):
        self.items = {}
    def get_item(self, Key):
        k = (Key['PK'], Key['SK'])
        return {'Item': self.items.get(k)}
    def put_item(self, Item):
        self.items[(Item['PK'], Item['SK'])] = Item


def test_create_task_generates_id_and_creates(monkeypatch):
    dummy = DummyTable()
    monkeypatch.setattr(task_management_crud, 'table', dummy)
    event = {'body': json.dumps({'name': '搾乳', 'description': '牛の搾乳作業'})}
    res = task_management_crud.create_task(event)
    assert res['statusCode'] == 201
    body = json.loads(res['body'])
    assert body['task_type'] == 'milking'
    assert ('TASK', 'milking') in dummy.items


def test_create_task_duplicate_auto_suffix(monkeypatch):
    dummy = DummyTable()
    dummy.items[('TASK', 'milking')] = {'PK': 'TASK', 'SK': 'milking'}
    monkeypatch.setattr(task_management_crud, 'table', dummy)
    event = {'body': json.dumps({'name': '搾乳'})}
    res = task_management_crud.create_task(event)
    assert res['statusCode'] == 201
    body = json.loads(res['body'])
    # should have created a new unique id different from 'milking'
    assert body['task_type'] != 'milking'
    assert ('TASK', body['task_type']) in dummy.items
