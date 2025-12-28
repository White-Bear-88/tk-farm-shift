import sys, os, json, importlib
os.environ.setdefault('TABLE_NAME', 'TEST_TABLE')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import shift_crud
importlib.reload(shift_crud)

class DummyTable:
    def __init__(self):
        self.items = {}
        # Pre-populate one shift
        pk = 'SHIFT#2025-12-01'
        sk = 'EMP#E1#milking'
        self.items[(pk, sk)] = {
            'PK': pk, 'SK': sk, 'start_time': '05:00', 'end_time': '07:00', 'status': 'scheduled'
        }
        self.put_called = False
        self.delete_called = False
    def query(self, KeyConditionExpression=None, ExpressionAttributeValues=None, IndexName=None):
        pk = ExpressionAttributeValues[':pk']
        items = [v for k,v in self.items.items() if k[0] == pk]
        return {'Items': items}
    def get_item(self, Key):
        k = (Key['PK'], Key['SK'])
        return {'Item': self.items.get(k)}
    def put_item(self, Item):
        self.items[(Item['PK'], Item['SK'])] = Item
        self.put_called = True
    def delete_item(self, Key):
        k = (Key['PK'], Key['SK'])
        if k in self.items: del self.items[k]
        self.delete_called = True
    def update_item(self, Key, UpdateExpression, ExpressionAttributeValues):
        k = (Key['PK'], Key['SK'])
        item = self.items.get(k)
        if item:
            for token, value in ExpressionAttributeValues.items():
                # naive parsing: token like ':start_time'
                field = token.lstrip(':')
                item[field] = value


def test_get_shifts_by_date_returns_shift_id(monkeypatch):
    dummy = DummyTable()
    monkeypatch.setattr(shift_crud, 'table', dummy)
    event = {'pathParameters': {'date': '2025-12-01'}}
    res = shift_crud.get_shifts_by_date(event)
    assert res['statusCode'] == 200
    body = json.loads(res['body'])
    assert isinstance(body, list)
    assert body[0]['shift_id'] == 'SHIFT#2025-12-01#E1#milking'


def test_update_shift_reassigns_employee(monkeypatch):
    dummy = DummyTable()
    monkeypatch.setattr(shift_crud, 'table', dummy)
    event = {'pathParameters': {'id': 'SHIFT#2025-12-01#E1#milking'}, 'body': json.dumps({'employee_id': 'E2'})}
    res = shift_crud.update_shift(event)
    assert res['statusCode'] == 200
    assert dummy.put_called is True
    assert dummy.delete_called is True


def test_get_shifts_for_employee_by_month(monkeypatch):
    dummy = DummyTable()
    # prepare an item with GSI fields
    dummy.items = {}
    pk = 'SHIFT#2025-12-01'
    sk = 'EMP#E1#milking'
    dummy.items[(pk, sk)] = {
        'PK': pk, 'SK': sk, 'GSI1PK': 'E1', 'GSI1SK': '2025-12-01', 'start_time': '05:00', 'end_time': '07:00'
    }
    monkeypatch.setattr(shift_crud, 'table', dummy)

    event = {'path': '/employees/E1/shifts', 'queryStringParameters': {'month': '2025-12'}}
    res = shift_crud.get_shifts_for_employee(event)
    assert res['statusCode'] == 200
    body = json.loads(res['body'])
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]['employee_id'] == 'E1'
    assert body[0]['date'] == '2025-12-01'
