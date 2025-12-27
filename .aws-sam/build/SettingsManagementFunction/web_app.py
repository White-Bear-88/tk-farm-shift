import json
import os
import base64

def lambda_handler(event, context):
    # リクエストパスを取得
    path = event.get('path', '/')
    
    # faviconリクエストの場合は空のレスポンスを返す
    if path == '/favicon.ico':
        return {
            'statusCode': 204,
            'headers': {
                'Content-Type': 'image/x-icon',
                'Cache-Control': 'public, max-age=86400'
            },
            'body': ''
        }
    
    # パスに基づいてファイル名を決定
    if path == '/' or path == '/index.html':
        filename = 'index.html'
    elif path.endswith('.html'):
        filename = path.lstrip('/')
    else:
        filename = 'index.html'  # デフォルト
    
    # HTMLファイルの内容を読み込み
    html_file_path = os.path.join(os.path.dirname(__file__), filename)
    
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
    except FileNotFoundError:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'text/html; charset=utf-8'},
            'body': '<h1>404 Not Found</h1><p>ファイルが見つかりません</p>'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Failed to load HTML: {str(e)}'})
        }