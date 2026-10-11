import streamlit as st
import time
import gsheets
import pandas as pd

def render(df, worksheet):
    # ★ 「押したら展開される」アコーディオン化
    with st.expander("📝 入力履歴の確認・修正・削除", expanded=False):
        if df.empty:
            st.info("まだデータがありません")
            return

        # 表示用のデータ整形
        df_display = df[['No','日付','区分','金額','カテゴリー','メモ']].copy()
        df_display['日付_str'] = df_display['日付'].dt.strftime('%y/%m/%d')
        # メモが長すぎると表が崩れるので省略表示
        df_display['メモ_disp'] = df_display['メモ'].astype(str).apply(lambda x: (x[:4] + '..') if len(x) > 3 else x)
        
        disp_df = df_display[['No', '日付_str', '区分', '金額', 'カテゴリー', 'メモ_disp']].rename(columns={'日付_str': '日付', 'メモ_disp': 'メモ', 'カテゴリー': '項目'})
        
        # リストを逆順（最新が上）にして上位50件を取得
        disp_df_top = disp_df.iloc[::-1].head(50)
        
        st.caption("👇 表の中の行をタップすると、その場で編集や削除ができます")
        
        # ★ Streamlitの最新機能：表をタップで選択できるようにする (on_select)
        event = st.dataframe(
            disp_df_top.style.map(gsheets.color_coding, subset=['区分']).format({"金額": "{:,} 円"}),
            use_container_width=True, 
            height=200, 
            hide_index=True,
            on_select="rerun",           # 選択されたら即座に再読み込み
            selection_mode="single-row"  # 1行だけ選択可能
        )
        
        selected_rows = event.selection.rows
        
        # もし表の行がタップ（選択）されたら、編集フォームを表示する
        if selected_rows:
            st.divider()
            
            # 選択された行の「No」を取得して、元のdfから詳細データを引っ張ってくる
            selected_idx = selected_rows[0]
            selected_no = disp_df_top.iloc[selected_idx]['No']
            target_data = df[df['No'] == selected_no].iloc[0]
            
            st.markdown(f"**No.{selected_no} のデータを修正**")
            
            # 編集・削除フォーム
            with st.form(key=f"edit_form_{selected_no}"):
                edit_date = st.date_input("日付", value=target_data['日付'])
                
                col1, col2 = st.columns(2)
                with col1:
                    # 区分を復元
                    type_idx = ["支出", "収入", "投資"].index(target_data['区分']) if target_data['区分'] in ["支出", "収入", "投資"] else 0
                    edit_type = st.selectbox("区分", ["支出", "収入", "投資"], index=type_idx)
                with col2:
                    edit_cat = st.text_input("項目（カテゴリー）", value=target_data['カテゴリー'])
                
                edit_amount = st.number_input("金額", min_value=0, step=1, value=int(target_data['金額']))
                edit_memo = st.text_input("メモ", value=str(target_data['メモ']))
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit_edit = st.form_submit_button("保存する", type="primary", use_container_width=True)
                with col_btn2:
                    submit_delete = st.form_submit_button("削除する", use_container_width=True)
                    
                if submit_edit:
                    try:
                        gsheets.update_entry(worksheet, selected_no, edit_date, edit_type, edit_cat, edit_amount, edit_memo)
                        st.success("✅ データを上書き保存しました！")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新エラー: {e}")
                        
                if submit_delete:
                    try:
                        # 削除時はエクセルの行数（+1）を渡す
                        gsheets.delete_entry(worksheet, int(selected_no) + 1)
                        st.warning("🗑️ データを削除しました！")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除エラー: {e}")