# CRMアプリケーションのWindows Server インストールガイド

このガイドでは、Windows serverにCRMアプリケーションをインストールして構成するプロセスについて詳しく説明します。

## 前提条件

- Windows Server 2016以降
- サーバーへの管理者アクセス

## ステップ1: Pythonのインストール

1. Python 3.9以降を公式ウェブサイトからダウンロードします: https://www.python.org/downloads/windows/
2. インストーラーを実行し、インストール中に「Add Python to PATH」を選択します。
3. コマンドプロンプトを開き、次のコマンドを実行してインストールを確認します:
   ```
   python --version
   ```

## ステップ2: PostgreSQLのインストール

1. PostgreSQLを公式ウェブサイトからダウンロードします: https://www.postgresql.org/download/windows/
2. インストーラーを実行し、プロンプトに従います。postgresユーザーに設定したパスワードを覚えておいてください。
3. PostgreSQLのbinディレクトリ（通常はC:\Program Files\PostgreSQL\13\bin）をシステムのPATHに追加します。

## ステップ3: データベースの作成

1. コマンドプロンプトを開き、PostgreSQLに接続します:
   ```
   psql -U postgres
   ```
2. CRMアプリケーション用の新しいデータベースを作成します:
   ```sql
   CREATE DATABASE crm_database;
   ```
3. `\q`と入力してEnterを押し、psqlを終了します。

## ステップ4: アプリケーションのセットアップ

1. CRMアプリケーションのコードをサーバーにクローンまたはダウンロードします。
2. コマンドプロンプトでアプリケーションディレクトリに移動します。
3. 仮想環境を作成します:
   ```
   python -m venv venv
   ```
4. 仮想環境をアクティベートします:
   ```
   venv\Scripts\activate
   ```
5. 必要なパッケージをインストールします:
   ```
   pip install -r requirements.txt
   ```

## ステップ5: アプリケーションの設定

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

## ステップ6: メール設定の構成

1. 自動フォローアップの送信用にメールアカウントを設定します。GmailアカウントやSMTPをサポートする他のメールサービスを使用できます。
2. Gmailを使用する場合、セキュリティ強化のために「アプリパスワード」を作成する必要がある場合があります。手順は以下の通りです:
   a. Googleアカウント設定に移動します。
   b. 左パネルの「セキュリティ」を選択します。
   c. 「Googleへのログイン」の下にある「アプリパスワード」を選択します。
   d. 「メール」と「Windowsコンピュータ」用の新しいアプリパスワードを生成します。
3. `.env`ファイルをメール設定で更新します:
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   ```
   プレースホルダーを実際のメール設定に置き換えてください。

## ステップ7: アプリケーションをWindowsサービスとして実行

1. `nssm`（Non-Sucking Service Manager）をインストールします:
   - https://nssm.cc/download からダウンロード
   - nssm.exeファイルをC:\Windows\System32に展開

2. 管理者としてコマンドプロンプトを開き、以下を実行します:
   ```
   nssm install CRMService
   ```

3. NSSMサービスインストーラーで:
   - 「Path」を仮想環境内のPython実行ファイルに設定します（例：C:\path\to\your\app\venv\Scripts\python.exe）
   - 「Startup directory」をアプリケーションディレクトリに設定します
   - 「Arguments」を"app.py"に設定します
   - 「Install service」をクリックします

4. サービスを開始します:
   ```
   nssm start CRMService
   ```

## ステップ8: IISをリバースプロキシとして設定（オプション）

HTTPSを処理するためにIISをリバースプロキシとして使用する場合:

1. IISとURL Rewrite Moduleをインストールします。
2. IISマネージャーで新しいウェブサイトを作成します。
3. URL Rewriteルールを設定して、リクエストをFlaskアプリケーションに転送します。

## トラブルシューティング

- Windows Event ViewerでCRMServiceに関連するエラーログを確認してください。
- すべての環境変数が正しく設定されていることを確認してください。
- PostgreSQLサービスが実行されていることを確認してください。
- メールが送信されない場合は、メール設定を再確認し、メールプロバイダーがSMTP経由でのメール送信を許可していることを確認してください。

追加のサポートが必要な場合は、当社の技術サポートチームにお問い合わせください。
