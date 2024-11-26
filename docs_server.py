from flask import Flask, render_template_string
import markdown2
import os

app = Flask(__name__)

@app.route('/')
def show_docs():
    with open('docs/replit_checkpoint_guide_ja.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    html_content = markdown2.markdown(content)
    
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Replitチェックポイントガイド</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1, h2 { color: #333; }
            code { background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }
        </style>
    </head>
    <body>
        {{content|safe}}
    </body>
    </html>
    '''
    
    return render_template_string(template, content=html_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
