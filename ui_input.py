import streamlit as st
import datetime
import time
import const as c
import gsheets

def render(worksheet, today_jst):
    st.subheader("収支入力")
    
    # ── スマホで「縦並び」にも「はみ出し」にもさせない完全なCSS ──
    st.markdown("""
    <style>
    /* 強制横並びコンテナ */
    div[data-testid="stVerticalBlock"]:has(> div.element-container > .date-row-container) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 6px !important;
        width: 100% !important;
        overflow: hidden !important; /* はみ出しを絶対に防止 */
    }
    /* フック用の空要素を隠す */
    div[data-testid="stVerticalBlock"]:has(> div.element-container > .date-row-container) > div.element-container:nth-child(1) {
        display: none !important;
    }
    /* 【超重要】全ての子要素が均等に縮むように設定 (min-width: 0 がはみ出し防止の鍵) */
    div[data-testid="stVerticalBlock"]:has(> div.element-container > .date-row-container) > div.element-container {
        flex: 1 1 0% !important;
        min-width: 0 !important; 
    }
    /* カレンダー枠をボタンより少し広くする(比率 1.4 : 1 : 1) */
    div[data-testid="stVerticalBlock"]:has(> div.element-container > .date-row-container) > div.element-container:nth-child(2) {
        flex: 1.4 1 0% !important;
    }
    
    /* 内部の細かい要素（文字入力欄など）の突っ張りをすべて強制解除 */
    div[data-testid="stVerticalBlock"]:has(> div.element-container > .date-row-container) * {
        min-width: 0 !important;
    }
    
    /* ボタンの調整 (文字サイズと余白を詰める) */
    div[data-testid="stVerticalBlock"]:has(> div.element-container > .date-row-container) button {
        width: 100% !important;
        padding: 0 !important;
        font-size: 13px !important;
        min-height: 38px !important;
        height: 38px !important;
        white-space: nowrap !important; /* 文字の折り返しを防ぐ */
    }
    
    /* カレンダーの調整 */
    div[data-testid="stDateInput"] input {
        padding: 4px 6px !important;
        font-size: 13px !important;
        min-height: 38px !important;
        height: 38px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if 'input_date' not in st.session_state:
        st.session_state['input_date'] = today_jst

    def set_date_offset(days):
        st.session_state['input_date'] = today_jst - datetime.timedelta(days=days)
    def sync_date():
        st.session_state['input_date'] = st.session_state['input_date_picker']

    st.caption("日付を選択")
    
    # st.columns を使わず、コンテナ内にそのまま置いてCSSで制御
    with st.container():
        st.markdown('<div class="date-row-container"></div>', unsafe_allow_html=True)
        st.date_input(" ", value=st.session_state['input_date'], key='input_date_picker', on_change=sync_date, label_visibility="collapsed")
        st.button("1日前", on_click=set_date_offset, args=(1,))
        st.button("2日前", on_click=set_date_offset, args=(2,))
        
    date = st.session_state['input_date']

    # --- 以下、既存の入力フォーム処理 ---
    balance_type = st.radio("区分", ["支出","収入","投資"], horizontal=True, label_visibility="collapsed")
    category, amount, memo, sub_category = None, 0, "", ""
    investment_name, investment_amount = "", 0.0000

    if balance_type == "支出":
        st.caption("支出の詳細を選んでください")
        category = st.radio('項目', c.EXPENSE_CATEGORIES, horizontal=True, label_visibility="collapsed")
        sub_options = c.EXPENSE_SUB_CATEGORIES.get(category)
        if sub_options:
            st.caption(f"{category}の詳細を選んでください")
            sub_category = st.radio(f"{category}詳細", sub_options, horizontal=True, label_visibility="collapsed")
    elif balance_type == "収入":
        st.caption("収入の詳細を選んでください")
        category = st.radio('項目', c.INCOME_CATEGORIES, horizontal=True, label_visibility="collapsed")

    with st.form(key='entry_form', clear_on_submit=True):
        if balance_type == "収入" and category == "給与":
            st.markdown("**【給与内訳入力】**")
            # ※給与内訳は項目が多いので、スマホで見やすいように「あえて縦並びになる」st.columnsのままにしています
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.caption("支給")
                s_honkyu = st.number_input('本給', min_value=0, step=1, value=0)
                s_choukin = st.number_input('超勤手当', min_value=0, step=1, value=0)
                s_remote = st.number_input('リモートワーク手当', min_value=0, step=1, value=0)
                s_tsukin = st.number_input('通勤手当', min_value=0, step=1, value=0)
            with col_b:
                st.caption("法定控除")
                d_kenpo = st.number_input('健康保険', min_value=0, step=1, value=0)
                d_kousei = st.number_input('厚年保険', min_value=0, step=1, value=0)
                d_koyou = st.number_input('雇用保険', min_value=0, step=1, value=0)
                d_shotoku = st.number_input('所得税', min_value=0, step=1, value=0)
            with col_c:
                st.caption("控除")
                d_mochikabu = st.number_input('持株積立', min_value=0, step=1, value=0)
                d_shataku = st.number_input('社宅利用料', min_value=0, step=1, value=0)
                d_seimei = st.number_input('生命保険', min_value=0, step=1, value=0)
                d_kumiai = st.number_input('組合費', min_value=0, step=1, value=0)
                d_shokudou = st.number_input('食堂喫食代', min_value=0, step=1, value=0)
            
            memo = st.text_input('メモ（任意）')
            submit_btn = st.form_submit_button('一括登録する')
            
        else:
            if balance_type in ["支出", "収入"]:
                amount = st.number_input('金額', min_value=0, step=1, value=None, placeholder="0")
            if balance_type == "投資":
                category = "投資"
                investment_name = st.text_input("銘柄名")
                investment_amount = st.number_input('数量', min_value=0.0, step=0.00000001, value=None, placeholder="0.0",format="%.8f")
                amount = st.number_input('支払い金額', min_value=0, step=1, value=None, placeholder="0")
            memo = st.text_input('メモ（任意）')
            submit_btn = st.form_submit_button('登録する')

    if submit_btn:
        if balance_type == "収入" and category == "給与":
            try:
                if s_honkyu > 0: gsheets.add_entry(worksheet, date, '収入', '給与', s_honkyu, f"本給 {memo}".strip())
                if s_choukin > 0: gsheets.add_entry(worksheet, date, '収入', '給与', s_choukin, f"超勤手当 {memo}".strip())
                if s_remote > 0: gsheets.add_entry(worksheet, date, '収入', '給与', s_remote, f"リモートワーク手当 {memo}".strip())
                if s_tsukin > 0: gsheets.add_entry(worksheet, date, '収入', '給与', s_tsukin, f"通勤手当 {memo}".strip())
                if d_kenpo > 0: gsheets.add_entry(worksheet, date, '支出', '生活費', d_kenpo, f"保険 健康保険 {memo}".strip())
                if d_kousei > 0: gsheets.add_entry(worksheet, date, '支出', '生活費', d_kousei, f"保険 厚年保険 {memo}".strip())
                if d_koyou > 0: gsheets.add_entry(worksheet, date, '支出', '生活費', d_koyou, f"保険 雇用保険 {memo}".strip())
                if d_shotoku > 0: gsheets.add_entry(worksheet, date, '支出', '生活費', d_shotoku, f"税金 所得税 {memo}".strip())
                if d_mochikabu > 0: gsheets.add_entry(worksheet, date, '支出', '投資費', d_mochikabu, f"株 持株積立 {memo}".strip())
                if d_shataku > 0: gsheets.add_entry(worksheet, date, '支出', '生活費', d_shataku, f"その他 社宅利用料 {memo}".strip())
                if d_seimei > 0: gsheets.add_entry(worksheet, date, '支出', '生活費', d_seimei, f"保険 生命保険 {memo}".strip())
                if d_kumiai > 0: gsheets.add_entry(worksheet, date, '支出', '生活費', d_kumiai, f"その他 組合費 {memo}".strip())
                if d_shokudou > 0: gsheets.add_entry(worksheet, date, '支出', '食費', d_shokudou, f"社食 食堂喫食代 {memo}".strip())
                
                st.success('給与・各種控除を一括登録しました。')
                st.balloons()
                time.sleep(3)
                st.rerun()
            except Exception as e:
                st.error(f'書き込みエラー: {e}')
        else:
            final_memo = f"{sub_category} {memo}" if sub_category and memo else sub_category or memo
            if balance_type == "投資":
                final_memo = f"{investment_name} 購入 {final_memo}" if final_memo else f"{investment_name} 購入"

            if balance_type in ["支出", "収入"]:
                if amount is None:
                    st.warning('金額が0円です。入力してください。')
                else:
                    try:
                        gsheets.add_entry(worksheet, date, balance_type, category, amount, final_memo)
                        msg = f'お疲れさま！ {category} : {amount}円を登録しました。' if balance_type == "収入" else f'{category} ({sub_category if sub_category else ""}) : {amount}円を登録しました。'
                        st.success(msg) if balance_type == "収入" else st.info(msg)
                        st.balloons()
                        time.sleep(3)
                        st.rerun()
                    except Exception as e:
                        st.error(f'書き込みエラー: {e}')
            elif balance_type == "投資":
                if not investment_name: st.warning('銘柄名を入力してください。')
                elif amount is None or amount == 0: st.warning('金額を入力してください。')
                else:
                    try:
                        gsheets.add_entry(worksheet, date, "支出", "投資費", amount, final_memo)
                        gsheets.add_investment_data(worksheet, date, investment_name, investment_amount, amount, final_memo)
                        st.success(f'{investment_name}を登録しました！')
                        st.balloons()
                        time.sleep(3)
                        st.rerun()
                    except Exception as e:
                        st.error(f'書き込みエラー:{e}')