import streamlit as st
import time
import const as c
import gsheets

def render(worksheet, today_jst):
    st.subheader("収支入力")
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
        date = st.date_input('日付', today_jst) # ここでJSTを適用
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