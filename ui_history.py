import streamlit as st
import time
import gsheets

def render(df, worksheet):
    st.subheader("入力履歴")
    if not df.empty:
        df_display = df[['No','日付','区分','金額','カテゴリー','メモ']].copy()
        df_display = df_display.rename(columns={'カテゴリー': '項目'})
        df_display['日付'] = df_display['日付'].dt.strftime('%y/%m/%d')
        df_display['メモ'] = df_display['メモ'].astype(str).apply(lambda x: (x[:3] + '..') if len(x) > 2 else x)
        st.dataframe(
            df_display.iloc[::-1].style.map(gsheets.color_coding, subset=['区分'])
            .format({"金額": "{:,} 円"}).set_properties(**{
                'background-color': '#ede4ce', 'border-color': '#A1A3A6', 'border-style': 'solid'
            }), use_container_width=True, height=240, hide_index=True
        )
    else:
        st.info("まだデータがありません")

    st.subheader("データの削除")
    if "delete_msg" not in st.session_state: st.session_state["delete_msg"] = None
    if "menu_reset_id" not in st.session_state: st.session_state["menu_reset_id"] = 0
    if "del_confirm_ckeck" not in st.session_state: st.session_state["del_confirm_ckeck"] = False
    
    if st.session_state["delete_msg"]:
        if "エラー" in st.session_state["delete_msg"]: st.error(st.session_state["delete_msg"])
        else:
            st.success(st.session_state["delete_msg"])
            st.session_state["delete_msg"] = None
            time.sleep(1)
            st.rerun()

    with st.expander("削除メニューを開く", expanded=False):
        if not df.empty:
            st.write("削除する **No** を入力してください")
            target_no = st.number_input("削除するNo", min_value=1, step=1, value=None, format="%d", label_visibility="collapsed", key="delete_input_no")
            if st.checkbox("削除対象を確認する", key="del_confirm_ckeck"):
                if target_no:
                    target_row = df[df['No'] == target_no]
                    if not target_row.empty:
                        st.warning("⚠️ 以下のデータを本当に削除しますか？")
                        preview_df = target_row[['No','日付','区分','金額','カテゴリー','メモ']].copy().rename(columns={'カテゴリー': '項目'})
                        preview_df['日付'] = preview_df['日付'].dt.strftime('%y/%m/%d')
                        st.dataframe(preview_df.style.map(gsheets.color_coding, subset=['区分']).format({"金額": "{:,} 円"}), use_container_width=True, hide_index=True)
                        st.button("はい、削除します", on_click=gsheets.delete_callback)
                    else: st.error("そのNoのデータは見つかりませんでした。")
                else: st.info("Noを入力してください。")
        else: st.info("データがありません。")