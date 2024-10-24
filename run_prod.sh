#!/bin/bash
gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
#!/bin/bash

# 環境変数の設定
export FLASK_ENV=production
export FLASK_APP=wsgi.py

# Gunicornの起動
exec gunicorn --workers 4 \
    --bind 0.0.0.0:5000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --enable-stdio-inheritance \
    wsgi:app