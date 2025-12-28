import sys, os, json, importlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import shift_assignment
importlib.reload(shift_assignment)


def test_generate_past_month_rejected():
    # Pick a past month (assuming tests run in 2025-12 for consistency)
    event = {'body': json.dumps({'month': '2025-01', 'overwrite': False, 'preview': False})}
    res = shift_assignment.generate_monthly_shifts(event)
    assert res['statusCode'] == 400
    body = json.loads(res['body'])
    assert '過去' in body['error']
