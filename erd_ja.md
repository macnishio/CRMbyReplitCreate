# エンティティ関連図（ERD）説明 - CRMアプリケーション

## 1. 概要
このドキュメントでは、CRMアプリケーションのデータベース設計におけるエンティティ間の関係を説明します。主要なエンティティとその関連性を詳細に記述します。

## 2. 主要エンティティ

### 2.1 User（ユーザー）
属性:
- id (PK): 整数
- username: 文字列
- email: 文字列
- password_hash: 文字列
- role: 文字列

### 2.2 Lead（リード）
属性:
- id (PK): 整数
- name: 文字列
- email: 文字列
- phone: 文字列
- status: 文字列
- score: 浮動小数点
- created_at: 日時
- last_contact: 日時
- user_id (FK): 整数

### 2.3 Opportunity（案件）
属性:
- id (PK): 整数
- name: 文字列
- amount: 浮動小数点
- stage: 文字列
- close_date: 日付
- created_at: 日時
- user_id (FK): 整数
- account_id (FK): 整数
- lead_id (FK): 整数

### 2.4 Account（取引先）
属性:
- id (PK): 整数
- name: 文字列
- industry: 文字列
- website: 文字列
- created_at: 日時
- user_id (FK): 整数

## 3. リレーションシップ

### 3.1 User - Lead
- 関係: 1対多
- 説明: 1人のユーザーは複数のリードを持つことができる

### 3.2 User - Opportunity
- 関係: 1対多
- 説明: 1人のユーザーは複数の案件を持つことができる

### 3.3 User - Account
- 関係: 1対多
- 説明: 1人のユーザーは複数の取引先を管理できる

### 3.4 Lead - Opportunity
- 関係: 1対多
- 説明: 1つのリードから複数の案件が生成される可能性がある

### 3.5 Account - Opportunity
- 関係: 1対多
- 説明: 1つの取引先に複数の案件が関連付けられる可能性がある

## 4. 追加の考慮事項

### 4.1 インデックス
- User.email
- Lead.email
- Lead.user_id
- Opportunity.user_id
- Opportunity.account_id
- Account.user_id

### 4.2 制約
- User.email: ユニーク制約
- Lead.email: ユニーク制約
- Opportunity.amount: 正の値のみ
- Account.website: 有効なURL形式

### 4.3 カスケード削除
- User削除時: 関連するLead、Opportunity、Accountも削除
- Account削除時: 関連するOpportunityも削除

## 5. データの整合性
- 外部キー制約を使用して、関連するエンティティ間の整合性を保証
- トランザクションを使用して、複数のテーブルに跨る操作の一貫性を確保

## 6. スケーラビリティの考慮
- 将来的なシャーディングを考慮したプライマリキーの設計
- 大量のデータに対応するためのパーティショニング戦略の検討

この ERD 説明は、CRMアプリケーションのデータモデルの基本構造を提供します。実際の実装時には、具体的なデータ型やその他の詳細な属性を追加する必要があります。
