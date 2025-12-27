import json
import os

def lambda_handler(event, context):
    # HTMLファイルの内容を読み込み
    html_file_path = os.path.join(os.path.dirname(__file__), 'index.html')
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html; charset=utf-8',
                'Cache-Control': 'no-cache'
            },
            'body': html_content
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Failed to load HTML: {str(e)}'})
        }