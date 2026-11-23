# Streamlit Cloudでデータを永続化する

教科書情報はSupabaseに保存します。Streamlit Cloud上のファイルは再起動で失われることがあるため、Cloudで使うにはSupabaseとStreamlit Secretsの設定が必要です。設定がない場合、アプリは一時ファイルへ保存せず、設定エラーを表示します。

## 1. Supabaseテーブルを作成

SupabaseプロジェクトのSQL Editorで次のSQLを実行します。

```sql
create table if not exists public.textbook_store (
    id text primary key check (id = 'main'),
    records jsonb not null default '[]'::jsonb
);

alter table public.textbook_store enable row level security;
```

アプリはサーバー側からSupabaseのsecret/service-role keyで接続するため、テーブルに公開アクセス用のRLSポリシーは作成しません。

## 2. Streamlit Cloudに接続情報を登録

SupabaseのProject URLとsecret/service-role keyを取得し、Streamlit Community Cloudで対象アプリの **Settings → Secrets** に以下を設定します。値は自分のSupabaseプロジェクトのものに置き換えてください。

```toml
[textbook_storage]
backend = "supabase"

[supabase]
url = "https://YOUR_PROJECT_ID.supabase.co"
service_role_key = "YOUR_SUPABASE_SECRET_KEY"
```

secret/service-role keyは秘密情報です。GitHubやこのリポジトリには登録せず、Streamlit CloudのSecretsにだけ設定してください。設定を保存するとアプリが再起動し、以後の教科書情報・評価・レビューはSupabaseに保存されます。

## 既存データについて

Supabaseテーブルが空の場合、初回読み込み時にリポジトリの`sample_data/textbooks.json`を初期データとして一度だけ登録します。以前のCloud実行環境にだけ存在し、再起動で消えたデータは復旧できません。

ローカルで従来どおりJSONファイルを使う場合は、`.streamlit/secrets.toml`に次を設定してください。

```toml
[textbook_storage]
backend = "json"
```
