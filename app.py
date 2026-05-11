"""
サンプルペッツライフ 在庫管理システム
Streamlit フロントエンド

【変更履歴】
  v2.0: FastAPI バックエンドに切り替え（SQL Server直接接続を廃止）
        ログイン機能追加（bcrypt によるパスワード認証 + セッション管理）
        グラフカラー更新

【接続先】
  FastAPI: 環境変数 API_BASE_URL（未設定時は http://localhost:8000）
"""

import streamlit as st
import requests
import pandas as pd
import altair as alt
import bcrypt
import os

# =============================================================
# ページ設定
# =============================================================
st.set_page_config(
    page_title="サンプルペッツライフ 管理システム",
    page_icon="🐾",
    layout="wide"
)

# =============================================================
# API 設定
# =============================================================
# Streamlit Community Cloud では st.secrets["API_BASE_URL"] を参照
# ローカル開発時は環境変数か http://localhost:8000 を使用
API_BASE_URL = st.secrets.get("API_BASE_URL", None) if hasattr(st, "secrets") else None
if not API_BASE_URL:
    API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


# =============================================================
# 認証設定
# ※ 実運用では st.secrets やDB管理を推奨
# =============================================================
USERS = {
    "admin": {
        "name": "管理者",
        # パスワード: petlife2026
        "hashed_password": "$2b$12$zWpG/oHYQ4/WmPC56Tc5xusVMib3kav9OKWQnKkhYSM7WBGn/0LPS",
        "role": "admin"   # 在庫更新ページにアクセス可
    },
    "staff": {
        "name": "スタッフ",
        # パスワード: staff2026
        "hashed_password": "$2b$12$aIssuXehKhxfxSoAFFvHYubjDUG/692t2dVjvm3s61fDGN2XI80TG",
        "role": "staff"   # 参照のみ
    },
}


# =============================================================
# 認証ヘルパー
# =============================================================
def check_password(username: str, password: str) -> bool:
    """入力パスワードをbcryptで検証する"""
    if username not in USERS:
        return False
    stored = USERS[username]["hashed_password"].encode()
    return bcrypt.checkpw(password.encode(), stored)


def login_page():
    """ログイン画面を表示する"""
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://placehold.co/300x80/4f8ef7/white?text=🐾+PetsLife", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("管理システム ログイン")

        with st.form("login_form"):
            username = st.text_input("ユーザー名", placeholder="admin または staff")
            password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("ログイン", use_container_width=True, type="primary")

        if submitted:
            if check_password(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["name"]     = USERS[username]["name"]
                st.session_state["role"]     = USERS[username]["role"]
                st.rerun()
            else:
                st.error("ユーザー名またはパスワードが違います")

        st.markdown("---")
        st.caption("**デモ用アカウント**")
        st.caption("管理者: `admin` / `petlife2026`（更新可）")
        st.caption("スタッフ: `staff` / `staff2026`（閲覧のみ）")


def logout():
    """セッションをクリアしてログアウト"""
    for key in ["logged_in", "username", "name", "role"]:
        st.session_state.pop(key, None)
    st.rerun()


# =============================================================
# API データ取得
# =============================================================
@st.cache_data(ttl=60)
def load_stock_data() -> pd.DataFrame:
    """FastAPI から全在庫データを取得（60秒キャッシュ）"""
    resp = requests.get(f"{API_BASE_URL}/stock", timeout=10)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    df["要発注"] = df["要発注"].astype(bool)
    return df


def update_stock_api(sku_code: str, new_qty: int) -> dict:
    """FastAPI で在庫数を更新する"""
    resp = requests.put(
        f"{API_BASE_URL}/stock/{sku_code}",
        json={"現在庫数": new_qty},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()


# =============================================================
# ログイン判定
# =============================================================
if not st.session_state.get("logged_in"):
    login_page()
    st.stop()


# =============================================================
# サイドバー（ログイン後）
# =============================================================
st.sidebar.title("🐾 サンプルペッツライフ")
st.sidebar.caption("株式会社サンプルペッツライフ")
st.sidebar.markdown("---")

# ユーザー情報
st.sidebar.markdown(f"👤 **{st.session_state['name']}** としてログイン中")
if st.sidebar.button("ログアウト", use_container_width=True):
    logout()

st.sidebar.markdown("---")

# ロールによってメニューを切り替え
if st.session_state["role"] == "admin":
    pages = ["📦 在庫ダッシュボード", "📊 分析グラフ", "✏️ 在庫更新"]
else:
    pages = ["📦 在庫ダッシュボード", "📊 分析グラフ"]

page = st.sidebar.radio("メニュー", pages)


# =============================================================
# ページ① : 在庫ダッシュボード
# =============================================================
if page == "📦 在庫ダッシュボード":
    st.title("📦 在庫ダッシュボード")

    try:
        df = load_stock_data()
    except Exception as e:
        st.error(f"データ取得エラー: {e}\n\nFastAPI サーバー ({API_BASE_URL}) に接続できません。")
        st.stop()

    reorder_df = df[df["要発注"] == True]
    normal_df  = df[df["要発注"] == False]

    # --- KPI メトリクス ---
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 総商品数",  len(df))
    col2.metric("⚠️ 要発注",   len(reorder_df))
    col3.metric("✅ 正常",      len(normal_df))

    st.markdown("---")

    # --- 要発注アラート ---
    if len(reorder_df) > 0:
        st.error(f"⚠️ 要発注商品が {len(reorder_df)} 件あります！")
        st.subheader("要発注商品一覧")
        st.dataframe(
            reorder_df[["SKUコード", "商品名", "カテゴリ", "現在庫数", "発注点", "消費期限"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ 要発注商品はありません")

    st.markdown("---")

    # --- 在庫一覧 + カテゴリフィルター ---
    st.subheader("在庫一覧")
    categories = ["すべて"] + sorted(df["カテゴリ"].dropna().unique().tolist())
    selected_cat = st.selectbox("カテゴリで絞り込み", categories)

    display_df = df if selected_cat == "すべて" else df[df["カテゴリ"] == selected_cat]
    st.dataframe(
        display_df[["SKUコード", "商品名", "カテゴリ", "保管場所", "現在庫数", "発注点", "消費期限"]],
        use_container_width=True,
        hide_index=True
    )


# =============================================================
# ページ② : 分析グラフ
# =============================================================
elif page == "📊 分析グラフ":
    st.title("📊 在庫分析グラフ")

    try:
        df = load_stock_data()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        st.stop()

    # --- カテゴリ別 現在庫数（縦棒グラフ）---
    st.subheader("カテゴリ別 現在庫数")
    cat_df = df.groupby("カテゴリ")["現在庫数"].sum().reset_index()
    bar_chart = (
        alt.Chart(cat_df)
        .mark_bar(color="#6366F1")           # 変更: インディゴ
        .encode(
            x=alt.X("カテゴリ:N", sort="-y", title="カテゴリ"),
            y=alt.Y("現在庫数:Q", title="在庫数（合計）"),
            tooltip=["カテゴリ", "現在庫数"]
        )
        .properties(height=350)
    )
    st.altair_chart(bar_chart, use_container_width=True)

    st.markdown("---")

    # --- 要発注 vs 正常（ドーナツグラフ）---
    st.subheader("在庫ステータス内訳")
    status_df = (
        df["要発注"]
        .map({True: "⚠️ 要発注", False: "✅ 正常"})
        .value_counts()
        .reset_index()
    )
    status_df.columns = ["ステータス", "件数"]
    donut = (
        alt.Chart(status_df)
        .mark_arc(innerRadius=60)
        .encode(
            theta=alt.Theta("件数:Q"),
            color=alt.Color(
                "ステータス:N",
                scale=alt.Scale(
                    domain=["⚠️ 要発注", "✅ 正常"],
                    range=["#F59E0B", "#10B981"]   # 変更: アンバー & エメラルド
                )
            ),
            tooltip=["ステータス", "件数"]
        )
        .properties(height=300)
    )
    st.altair_chart(donut, use_container_width=True)

    st.markdown("---")

    # --- カテゴリ別 要発注状況（積み上げ棒グラフ）---
    st.subheader("カテゴリ別 要発注状況")
    status_by_cat = (
        df.groupby(["カテゴリ", "要発注"])
        .size()
        .reset_index(name="件数")
    )
    status_by_cat["ステータス"] = status_by_cat["要発注"].map({True: "要発注", False: "正常"})
    stacked = (
        alt.Chart(status_by_cat)
        .mark_bar()
        .encode(
            x=alt.X("カテゴリ:N"),
            y=alt.Y("件数:Q"),
            color=alt.Color(
                "ステータス:N",
                scale=alt.Scale(
                    domain=["要発注", "正常"],
                    range=["#F59E0B", "#10B981"]   # 変更: アンバー & エメラルド
                )
            ),
            tooltip=["カテゴリ", "ステータス", "件数"]
        )
        .properties(height=350)
    )
    st.altair_chart(stacked, use_container_width=True)


# =============================================================
# ページ③ : 在庫更新（管理者のみ）
# =============================================================
elif page == "✏️ 在庫更新":
    st.title("✏️ 在庫数更新")
    st.caption("FastAPI 経由で在庫数を更新します。次回バッチ実行時にkintoneにも反映されます。")

    try:
        df = load_stock_data()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        st.stop()

    # --- 商品選択 ---
    sku_list = df["SKUコード"].tolist()
    selected_sku = st.selectbox(
        "商品を選択してください",
        sku_list,
        format_func=lambda x: f"{x}  {df[df['SKUコード'] == x]['商品名'].values[0]}"
    )

    if selected_sku:
        current = df[df["SKUコード"] == selected_sku].iloc[0]

        # --- 現在の情報を表示 ---
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**商品名**: {current['商品名']}")
            st.info(f"**カテゴリ**: {current['カテゴリ']}")
        with col2:
            st.info(f"**現在庫数**: {int(current['現在庫数'])} 個")
            st.info(f"**発注点**:   {int(current['発注点'])} 個")

        if current["要発注"]:
            st.warning("⚠️ この商品は現在「要発注」状態です")

        st.markdown("---")

        # --- ルックアップ表示（APIから取得） ---
        with st.expander("🔍 APIから最新データを確認する（ルックアップ機能）"):
            if st.button("APIから取得"):
                try:
                    resp = requests.get(f"{API_BASE_URL}/stock/{selected_sku}", timeout=5)
                    data = resp.json()
                    st.json(data)
                except Exception as e:
                    st.error(f"取得エラー: {e}")

        # --- 新しい在庫数の入力 ---
        new_qty = st.number_input(
            "新しい在庫数を入力してください",
            min_value=0,
            max_value=99999,
            value=int(current["現在庫数"]),
            step=1
        )

        if st.button("✅ 在庫数を更新する", type="primary"):
            try:
                result = update_stock_api(selected_sku, new_qty)
                st.success(
                    f"✅ {selected_sku}（{current['商品名']}）の在庫数を "
                    f"{int(current['現在庫数'])} → **{new_qty}** に更新しました！"
                )
                load_stock_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"更新エラー: {e}")
