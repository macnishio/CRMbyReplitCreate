# CRMアプリケーションのUbuntu Linuxインストールガイド

このガイドでは、Ubuntu LinuxサーバーにCRMアプリケーションをインストールして構成するプロセスについて詳しく説明します。

## 前提条件

- Ubuntu 20.04 LTS以降
- サーバーへのSudoアクセス

## ステップ1: システムパッケージの更新

1. ターミナルを開き、パッケージリストを更新します:
   ```
   sudo apt update
   ```
2. インストールされているパッケージをアップグレードします:
   ```
   sudo apt upgrade -y
   ```

## ステップ2: Pythonのインストール

1. Python 3とpipをインストールします:
   ```
   sudo apt install python3 python3-pip -y
   ```
2. インストールを確認します:
   ```
   python3 --version
   pip3 --version
   ```

## ステップ3: PostgreSQLのインストール

1. PostgreSQLをインストールします:
   ```
   sudo apt install postgresql postgresql-contrib -y
   ```
2. PostgreSQLサービスを開始し、自動起動を有効にします:
   ```
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

## ステップ4: データベースの作成

1. postgresユーザーに切り替えます:
   ```
   sudo -i -u postgres
   ```
2. CRMアプリケーション用の新しいデータベースを作成します:
   ```
   createdb crm_database
   ```
3. postgresユーザーセッションを終了します:
   ```
   exit
   ```

## ステップ5: アプリケーションのセットアップ

1. CRMアプリケーションのコードをサーバーにクローンまたはダウンロードします。
2. ターミナルでアプリケーションディレクトリに移動します。
3. 必要なパッケージをインストールします:
   ```
   pip3 install -r requirements.txt
   ```

## ステップ6: アプリケーションの設定

1. アプリケーションディレクトリに`.env`ファイルを作成し、以下の内容を記述します:
   ```
   DATABASE_URL=postgresql://postgres:your_password@localhost/crm_database
   SECRET_KEY=your_secret_key
   MAIL_SERVER=your_mail_server
   MAIL_PORT=your_mail_port
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@example.com
   MAIL_PASSWORD=your_email_password
   ```
   プレースホルダーを実際のデータベースとメール設定に置き換えてください。

2. データベースを初期化します:
   ```
   flask db upgrade
   ```

## ステップ7: メール設定の構成

1. 自動フォローアップの送信用にメールアカウントを設定します。GmailアカウントやSMTPをサポートする他のメールサービスを使用できます。
2. Gmailを使用する場合、セキュリティ強化のために「アプリパスワード」を作成する必要がある場合があります。手順は以下の通りです:
   a. Googleアカウント設定に移動します。
   b. 左パネルの「セキュリティ」を選択します。
   c. 「Googleへのログイン」の下にある「アプリパスワード」を選択します。
   d. 「メール」と「その他（カスタム名）」用の新しいアプリパスワードを生成します。
3. `.env`ファイルをメール設定で更新します:
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   ```
   プレースホルダーを実際のメール設定に置き換えてください。

## ステップ8: アプリケーションの実行

1. アプリケーションを起動します:
   ```
   python3 app.py
   ```

## ステップ9: Systemdサービスのセットアップ（オプション）

アプリケーションをサービスとして実行するには:

1. 新しいサービスファイルを作成します:
   ```
   sudo nano /etc/systemd/system/crm.service
   ```
2. 以下の内容を追加します:
   ```
   [Unit]
   Description=CRM Application
   After=network.target

   [Service]
   User=your_username
   WorkingDirectory=/path/to/your/app
   ExecStart=/usr/bin/python3 /path/to/your/app/app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   `your_username`と`/path/to/your/app`を適切な値に置き換えてください。

3. ファイルを保存してエディタを終了します。
4. systemdデーモンをリロードします:
   ```
   sudo systemctl daemon-reload
   ```
5. サービスを開始します:
   ```
   sudo systemctl start crm
   ```
6. ブート時にサービスが自動的に開始されるようにします:
   ```
   sudo systemctl enable crm
   ```

## ステップ10: Nginxをリバースプロキシとして設定（オプション）

HTTPSを処理するためにNginxをリバースプロキシとして使用する場合:

1. Nginxをインストールします:
   ```
   sudo apt install nginx -y
   ```
2. 新しいNginx設定ファイルを作成します:
   ```
   sudo nano /etc/nginx/sites-available/crm
   ```
3. 以下の内容を追加します:
   ```
   server {
       listen 80;
       server_name your_domain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   `your_domain.com`を実際のドメイン名に置き換えてください。

4. シンボリックリンクを作成してサイトを有効にします:
   ```
   sudo ln -s /etc/nginx/sites-available/crm /etc/nginx/sites-enabled
   ```
5. Nginx設定をテストします:
   ```
   sudo nginx -t
   ```
6. テストが成功したら、Nginxを再起動します:
   ```
   sudo systemctl restart nginx
   ```

## トラブルシューティング

- アプリケーションログでエラーメッセージを確認してください。
- `.env`ファイルですべての環境変数が正しく設定されていることを確認してください。
- PostgreSQLサービスが実行されていることを確認します:
  ```
  sudo systemctl status postgresql
  ```
- メールが送信されない場合は、メール設定を再確認し、メールプロバイダーがSMTP経由でのメール送信を許可していることを確認してください。

追加のサポートが必要な場合は、当社の技術サポートチームにお問い合わせください。
