import streamlit as st
import time
import const as c
import gsheets

def render_asset_check(worksheet, yen_assets, today_jst):
    st.subheader("資産確認・調整")
    with st.expander("資産確認を開く", expanded=False):
        st.caption("現在の残高・未払い額を入力してください")
        account_total = sum(st.number_input(account, min_value=0, step=1, value=0, key=f"ac_{account}") for account in c.ASSET_CHECK_ACCOUNTS)

        st.caption("クレカ未払い分（残高から引かれます）")
        credit_total = sum(st.number_input(credit, min_value=0, step=1, value=0, key=f"cr_{credit}") for credit in c.ASSET_CHECK_CREDITS)

        real_assets = account_total - credit_total
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("実際の資産", f"{real_assets:,} 円")
        col2.metric("アプリ上の資産", f"{int(yen_assets):,} 円")
        diff = real_assets - int(yen_assets)
        col3.metric("差額", f"{diff:,} 円", delta=f"{diff:,}")

        if diff != 0:
            st.warning(f"{'不足' if diff < 0 else '超過'} {abs(diff):,} 円のズレがあります")
            if st.button("この差額を家計簿に記入する"):
                b_type = '収入' if diff > 0 else '支出'
                # 調整時の日付もJSTを使用
                gsheets.add_entry(worksheet, today_jst, b_type, 'その他', abs(diff), '資産調整')
                st.success(f"差額 {abs(diff):,} 円を「その他」で記入しました！")
                time.sleep(1)
                st.rerun()
        else:
            st.success("✅ アプリ上の資産と実際の資産が一致しています！")

def render_memo(worksheet):
    st.subheader("なんでもメモ")
    if 'my_memo_content' not in st.session_state:
        st.session_state['my_memo_content'] = gsheets.get_anything_memo(worksheet)
    if "memo_area" not in st.session_state:
        st.session_state["memo_area"] = st.session_state['my_memo_content']

    saved_text = st.session_state['my_memo_content']
    dynamic_height = max(150, (saved_text.count('\n') + 1) * 25)
    current_text = st.text_area("メモ", key="memo_area", height=dynamic_height, label_visibility="collapsed")
    is_unsaved = (current_text != saved_text)

    if is_unsaved:
        st.markdown(":warning: **<span style='color:#ff4b4b'>変更が保存されていません。</span>**", unsafe_allow_html=True)
        btn_type, btn_label = "primary", "変更を保存する"
    else:
        btn_type, btn_label = "secondary", "保存済み"

    if st.button(btn_label, type=btn_type):
        if is_unsaved:
            new_text = st.session_state["memo_area"]
            gsheets.update_anything_memo(worksheet, new_text)
            st.session_state['my_memo_content'] = new_text
            st.success("保存しました！")
            time.sleep(0.5)
            st.rerun()
        else:
            st.info("変更点はありません。")