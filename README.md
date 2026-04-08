# YOHAKU OS Dashboard

YOHAKU Civilization OS v2.1 の管理ダッシュボード。
Phase A: Next.js 14 + Vercel 基盤。

## 技術スタック

- Next.js 14 (App Router)
- TypeScript + Tailwind CSS
- Supabase (PostgreSQL)
- Vercel デプロイ

## ローカル起動

```bash
# .env.local に SUPABASE_ANON_KEY を追記してから実行
npm install
npm run dev
# → http://localhost:3000
```

## 認証

`DASHBOARD_PASSWORD` 環境変数に設定したパスワードでログイン。
Cookie ベース HMAC セッション（7日間有効）。

## Vercel デプロイ

1. vercel.com でこのリポジトリを import
2. Environment Variables に以下を設定:
   - `DASHBOARD_PASSWORD` — ログインパスワード
   - `DASHBOARD_SECRET` — セッション署名キー（32文字以上のランダム文字列）
   - `SUPABASE_URL` — `https://xdcsnkojyepenyocdaql.supabase.co`
   - `SUPABASE_ANON_KEY` — Supabase Anon Key
   - `YOHAKU_OS_PHASE` — `Phase 3`
3. デプロイ後 `https://yohaku-os.vercel.app` で確認

## ブランチ構成

| ブランチ | 内容 |
|---------|------|
| `main` | Next.js 本番（Vercel 接続先） |
| `legacy/streamlit` | 旧 Streamlit 版（参照用・削除禁止） |
| `feature/phase-a-nextjs-foundation` | Phase A 実装ブランチ |

## Streamlit Cloud の対応

既存の Streamlit Community Cloud デプロイは
ブランチを `legacy/streamlit` に変更することで継続稼働させられます。
