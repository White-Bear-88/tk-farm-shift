import sys, os, json, importlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import shift_assignment
importlib.reload(shift_assignment)

class DummyTable:
    def __init__(self):
        self.items = {}
    def query(self, KeyConditionExpression=None, ExpressionAttributeValues=None, IndexName=None):
        pk = ExpressionAttributeValues[':pk']
        items = [v for (k,v) in self.items.items() if k[0] == pk]
        return {'Items': items}
    def put_item(self, Item, ConditionExpression=None):
        self.items[(Item['PK'], Item['SK'])] = Item
    def delete_item(self, Key):
        k=(Key['PK'], Key['SK'])
        if k in self.items: del self.items[k]
    def batch_writer(self):
        # dummy context manager
        class BW:
            def __enter__(self_inner): return self_inner
            def __exit__(self_inner,*a): pass
            def delete_item(self_inner, Key):
                k=(Key['PK'], Key['SK'])
                if k in self.items: del self.items[k]
        return BW()


def test_preview_does_not_write(monkeypatch):
    dummy = DummyTable()
    monkeypatch.setattr(shift_assignment, 'table', dummy)
    # Call preview - should not write
    event = {'body': json.dumps({'month': '2025-12', 'overwrite': False, 'preview': True})}
    res = shift_assignment.generate_monthly_shifts(event)
    body = json.loads(res['body'])
    assert body['preview'] is True
    assert 'shifts' in body
    assert dummy.items == {}  # nothing written

