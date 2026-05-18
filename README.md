# サンプルペッツライフ 在庫管理システム（Streamlit フロントエンド）
 
ペットショップの在庫を管理するための社内向け Web アプリ。
**Streamlit** + **Altair** + **bcrypt 認証** で実装し、**Streamlit Community Cloud** にデプロイしています。
バックエンドは別リポジトリの REST API（[petlife-api](https://github.com/HM19Lab/petlife-api)）から在庫データを取得・更新します。
 
---
 
## ライブデモ
 
- **アプリ**: <https://petlife-app-8hljdcqkdf4f58if7ctgqk.streamlit.app/>
- **ログイン情報（デモ用）**:
  - 管理者: `admin` / `petlife2026`（在庫更新可）
  - スタッフ: `staff` / `staff2026`（閲覧のみ）
<!-- スクリーンショットは後で docs/ に追加してここに挿入 -->
 
---
 
## 概要
 
3ページ構成の在庫管理ダッシュボード。バックエンドの FastAPI から在庫データを取得し、可視化・更新ができる。ログインしたユーザーのロールに応じて利用できる画面が変わる。
 
---
 
## 主な機能
 
### ログイン認証
- bcrypt によるパスワードハッシュ照合
- 「管理者」「スタッフ」の 2 ロール対応
- ロールに応じて表示メニューを切り替え
### 📦 在庫ダッシュボード
- 総商品数 / 要発注 / 正常 の KPI 表示
- 要発注商品の自動ハイライト（要発注がある場合はアラート表示）
- カテゴリでの絞り込み
### 📊 分析グラフ
- カテゴリ別 現在庫数（縦棒グラフ）
- 要発注 vs 正常（ドーナツグラフ）
- カテゴリ別 要発注状況（積み上げ棒グラフ）
### ✏️ 在庫更新（管理者のみ）
- 商品選択 → 在庫数を入力 → API 経由で更新
- 更新後は自動でキャッシュをクリアして再表示
- API ルックアップ機能（最新データの確認）
---
 
## 設計メモ
 
- **フロント／バック分離構成**: バックエンド（[petlife-api](https://github.com/HM19Lab/petlife-api)）と HTTP で通信して在庫データを取得・更新する。API の接続先は環境変数 `API_BASE_URL`（または `st.secrets`）で切り替え可能なので、ローカル開発と本番で同じコードが動く。
- **ロールベースのアクセス制御**: ログイン後、ユーザーのロール（admin / staff）に応じて表示メニューが変わる。在庫更新は admin のみ。
- **パスワードはハッシュ保存**: 平文ではなく bcrypt でハッシュ化した値だけをコード内に保持。照合は `bcrypt.checkpw` で実施。
- **API レスポンスを 60 秒キャッシュ**: `@st.cache_data(ttl=60)` で頻繁な API 呼び出しを抑制。更新操作の直後は明示的にキャッシュをクリアして整合性を担保。
---
 
## 技術スタック
 
| 区分 | 内容 |
|---|---|
| 言語 | Python 3 |
| UI フレームワーク | Streamlit |
| グラフ | Altair |
| 認証 | bcrypt |
| API クライアント | requests |
| データ整形 | pandas |
| ホスティング | Streamlit Community Cloud |
 
---
 
## ローカルでの動かし方
 
```bash
# 1. リポジトリをクローン
git clone https://github.com/HM19Lab/petlife-streamlit.git
cd petlife-streamlit
 
# 2. 依存パッケージをインストール
pip install -r requirements.txt
 
# 3. バックエンドの API URL を設定（公開済みの Railway 版でも動きます）
export API_BASE_URL=https://web-production-3267c.up.railway.app
 
# 4. 起動
streamlit run app.py
```
 
ブラウザで <http://localhost:8501> が開きます。
 
---
 
## デプロイ
 
[Streamlit Community Cloud](https://streamlit.io/cloud) にデプロイしています。
API の接続先は `st.secrets["API_BASE_URL"]` で管理しています。
 
---
 
## 関連リポジトリ
 
- **バックエンド**: [petlife-api](https://github.com/HM19Lab/petlife-api) — このフロントエンドから叩いている FastAPI 在庫API
---
 
## 作成者
 
[@HM19Lab](https://github.com/HM19Lab)
