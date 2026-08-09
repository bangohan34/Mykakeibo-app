import streamlit as st
import const as c
import gsheets

def render(worksheet, url_user_id):
    st.subheader("サブスク管理")
    sub_expense_categories = c.EXPENSE_CATEGORIES if url_user_id == "u1" else (c.EXPENSE_CATEGORIES_saya if url_user_id == "u2" else c.EXPENSE_CATEGORIES)
    
    df_sub = gsheets.load_subscription_data(worksheet)
    if not df_sub.empty:
        monthly_total = df_sub['金額'].sum()
        yearly_total = monthly_total * 12
        st.markdown(f"""
        <div style="display: flex; gap: 10px; justify-content: space-between;">
            <div style="flex: 1; padding: 10px; text-align: center;">
                <div style="font-size: 14px; color: gray;">月額合計</div>
                <div style="font-size: 30px; font-weight: bold; color: #b22222;">{monthly_total:,} 円</div>
            </div>
            <div style="flex: 1; padding: 10px; text-align: center;">
                <div style="font-size: 14px; color: gray;">年額換算</div>
                <div style="font-size: 30px; font-weight: bold; color: #b22222;">{yearly_total:,} 円</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        display_sub = df_sub[['サービス名', '金額', 'メモ']].copy()
        display_sub['金額'] = display_sub['金額'].apply(lambda x: f"{x:,} 円")
        st.dataframe(
            display_sub.style.set_properties(**{'background-color': '#ede4ce', 'border-color': '#A1A3A6', 'border-style': 'solid'}),
            hide_index=True, use_container_width=True
        )
    else:
        st.info("サブスクはまだ登録されていません。")

    with st.expander("サブスクを追加する", expanded=False):
        with st.form(key="sub_add_form", clear_on_submit=True):
            sub_service_name = st.text_input("サービス名（例：Netflix, Spotify）")
            sub_amount = st.number_input("月額金額", min_value=0, step=1, value=None, placeholder="0")
            sub_category = st.selectbox("カテゴリー", sub_expense_categories)
            sub_pay_day = st.number_input("毎月の支払日", min_value=1, max_value=31, step=1, value=1)
            sub_memo = st.text_input("メモ（任意）")
            sub_submit = st.form_submit_button("登録する")
        if sub_submit:
            if not sub_service_name or sub_amount is None or sub_amount == 0:
                st.warning("サービス名と金額を正しく入力してください。")
            else:
                try:
                    gsheets.add_subscription(worksheet, sub_service_name, sub_amount, sub_category, sub_pay_day, sub_memo)
                    st.success(f"「{sub_service_name}」を登録しました！")
                    st.rerun()
                except Exception as e: st.error(f"登録エラー: {e}")

    with st.expander("サブスクを削除する", expanded=False):
        if not df_sub.empty:
            del_options = [""] + df_sub['サービス名'].tolist()
            del_target = st.selectbox("削除するサービスを選択", del_options, index=0)
            if del_target:
                target_row = df_sub[df_sub['サービス名'] == del_target]
                if st.checkbox("削除対象を確認する", key="sub_del_confirm"):
                    st.warning("⚠️ 以下のサブスクを本当に削除しますか？")
                    preview = target_row[['サービス名', '金額', 'メモ']].copy()
                    preview['金額'] = preview['金額'].apply(lambda x: f"{x:,} 円")
                    st.dataframe(preview.style.set_properties(**{'background-color': '#ede4ce', 'border-color': '#A1A3A6', 'border-style': 'solid'}), hide_index=True, use_container_width=True)
                    if st.button("はい、削除します", key="sub_delete_btn"):
                        try:
                            gsheets.delete_subscription(worksheet, int(target_row.iloc[0]['No']))
                            st.success(f"「{del_target}」を削除しました！")
                            st.rerun()
                        except Exception as e: st.error(f"削除エラー: {e}")
        else: st.info("削除するサブスクがありません。")