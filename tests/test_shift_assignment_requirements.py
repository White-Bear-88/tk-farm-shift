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
        class BW:
            def __enter__(self_inner): return self_inner
            def __exit__(self_inner,*a): pass
            def delete_item(self_inner, Key):
                k=(Key['PK'], Key['SK'])
                if k in self.items: del self.items[k]
        return BW()


def test_generate_respects_provided_requirements(monkeypatch):
    dummy = DummyTable()
    # Insert employees with specific skills
    employees = [
        {'PK': 'EMPLOYEE', 'SK': 'E1', 'name': 'Alice', 'skills': ['milking']},
        {'PK': 'EMPLOYEE', 'SK': 'E2', 'name': 'Bob', 'skills': ['feeding']},
        {'PK': 'EMPLOYEE', 'SK': 'E3', 'name': 'Carol', 'skills': ['cleaning']},
        {'PK': 'EMPLOYEE', 'SK': 'E4', 'name': 'Dave', 'skills': ['patrol']},
    ]
    for emp in employees:
        dummy.items[(emp['PK'], emp['SK'])] = emp

    monkeypatch.setattr(shift_assignment, 'table', dummy)

    # Request generation with only 1 milking per day
    event = {'body': json.dumps({'month': '2025-12', 'overwrite': False, 'preview': True, 'requirements': {'milking': 1, 'feeding': 0, 'cleaning': 0, 'patrol': 0}})}
    res = shift_assignment.generate_monthly_shifts(event)
    assert res['statusCode'] == 200
    body = json.loads(res['body'])
    assert body['preview'] is True
    shifts = body['shifts']

    # December 2025 has 31 days; expect 31 milking shifts
    assert sum(1 for s in shifts if s['task_type'] == 'milking') == 31
    # No other task types should be present in the preview
    other_tasks = set(s['task_type'] for s in shifts if s['task_type'] != 'milking')
    assert other_tasks == set()
