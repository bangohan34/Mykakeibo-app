import streamlit as st
import datetime
import time
import const as c
import gsheets
import streamlit.components.v1 as components

def inject_auto_clear_script():
    """スマホやPCで数値入力欄をタップした際、0なら即座に消し、数値なら全選択するJS"""
    components.html('''
    <script>
    function setupInputs() {
        const doc = window.parent.document;
        const inputs = doc.querySelectorAll('input[type="number"]');
        
        inputs.forEach(input => {
            if (!input.dataset.smartClear) {
                input.dataset.smartClear = 'true';
                
                input.addEventListener('focus', function() {
                    if (this.value === '0') {
                        this.value = ''; 
                        this.dispatchEvent(new Event('input', { bubbles: true }));
                    } else {
                        this.select(); 
                    }
                });
                
                input.addEventListener('blur', function() {
                    if (this.value === '') {
                        this.value = '0';
                        this.dispatchEvent(new Event('input', { bubbles: true }));
                        this.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                });
            }
        });
    }

    const observer = new MutationObserver(() => {
        setupInputs();
    });
    observer.observe(window.parent.document.body, { childList: true, subtree: true });

    setTimeout(setupInputs, 200);
    </script>
    ''', height=0, width=0)

def render_salary_form():
    """給与内訳の入力フォームを描画し、入力された辞書を返す"""
    st.markdown("**【給与内訳入力】**")
    inject_auto_clear_script()

    col_a, col_b, col_c = st.columns(3)
    vals = {}
    defs = c.SALARY_DEFAULTS
    
    with col_a:
        st.caption("支給")
        vals['本給'] = st.number_input('本給', min_value=0, step=1, value=defs['本給'])
        vals['超勤手当'] = st.number_input('超勤手当', min_value=0, step=1, value=defs['超勤手当'])
        vals['リモートワーク手当'] = st.number_input('リモートワーク手当', min_value=0, step=1, value=defs['リモートワーク手当'])
        vals['通勤手当'] = st.number_input('通勤手当', min_value=0, step=1, value=defs['通勤手当'])
        vals['その他（収入）'] = st.number_input('その他（収入）', min_value=0, step=1, value=defs['その他（収入）'])
    with col_b:
        st.caption("法定控除")
        vals['健康保険'] = st.number_input('健康保険', min_value=0, step=1, value=defs['健康保険'])
        vals['厚年保険'] = st.number_input('厚年保険', min_value=0, step=1, value=defs['厚年保険'])
        vals['雇用保険'] = st.number_input('雇用保険', min_value=0, step=1, value=defs['雇用保険'])
        vals['所得税'] = st.number_input('所得税', min_value=0, step=1, value=defs['所得税'])
    with col_c:
        st.caption("控除")
        vals['持株積立'] = st.number_input('持株積立', min_value=0, step=1, value=defs['持株積立'])
        vals['社宅利用料'] = st.number_input('社宅利用料', min_value=0, step=1, value=defs['社宅利用料'])
        vals['生命保険'] = st.number_input('生命保険', min_value=0, step=1, value=defs['生命保険'])
        vals['組合費'] = st.number_input('組合費', min_value=0, step=1, value=defs['組合費'])
        vals['食堂喫食代'] = st.number_input('食堂喫食代', min_value=0, step=1, value=defs['食堂喫食代'])
        vals['その他（支出）'] = st.number_input('その他（支出）', min_value=0, step=1, value=defs['その他（支出）'])
        
    return vals

def render_bonus_form():
    """賞与内訳の入力フォームを描画し、入力された辞書を返す"""
    st.markdown("**【賞与内訳入力】**")
    inject_auto_clear_script()

    col_a, col_b = st.columns(2)
    vals = {}
    defs = c.BONUS_DEFAULTS
    
    with col_a:
        st.caption("支給")
        vals['賞与額'] = st.number_input('賞与額', min_value=0, step=1, value=defs['賞与額'])
        vals['その他（収入）'] = st.number_input('その他（収入）', min_value=0, step=1, value=defs['その他（収入）'])
    with col_b:
        st.caption("法定控除")
        vals['健康保険'] = st.number_input('健康保険', min_value=0, step=1, value=defs['健康保険'])
        vals['厚年保険'] = st.number_input('厚年保険', min_value=0, step=1, value=defs['厚年保険'])
        vals['雇用保険'] = st.number_input('雇用保険', min_value=0, step=1, value=defs['雇用保険'])
        vals['所得税'] = st.number_input('所得税', min_value=0, step=1, value=defs['所得税'])
        vals['その他（支出）'] = st.number_input('その他（支出）', min_value=0, step=1, value=defs['その他（支出）'])
        
    return vals

def process_salary_entry(worksheet, date, vals, memo):
    """給与内訳のスプレッドシートへの書き込み処理"""
    if vals['本給'] > 0: gsheets.add_entry(worksheet, date, '収入', '給与', vals['本給'], f"本給 {memo}".strip())
    if vals['超勤手当'] > 0: gsheets.add_entry(worksheet, date, '収入', '給与', vals['超勤手当'], f"超勤手当 {memo}".strip())
    if vals['リモートワーク手当'] > 0: gsheets.add_entry(worksheet, date, '収入', '給与', vals['リモートワーク手当'], f"リモートワーク手当 {memo}".strip())
    if vals['通勤手当'] > 0: gsheets.add_entry(worksheet, date, '収入', '給与', vals['通勤手当'], f"通勤手当 {memo}".strip())
    if vals['その他（収入）'] > 0: gsheets.add_entry(worksheet, date, '収入', '給与', vals['その他（収入）'], f"その他（収入） {memo}".strip())
    
    if vals['健康保険'] > 0: gsheets.add_entry(worksheet, date, '支出', '税金', vals['健康保険'], f"保険 健康保険 {memo}".strip())
    if vals['厚年保険'] > 0: gsheets.add_entry(worksheet, date, '支出', '税金', vals['厚年保険'], f"保険 厚年保険 {memo}".strip())
    if vals['雇用保険'] > 0: gsheets.add_entry(worksheet, date, '支出', '税金', vals['雇用保険'], f"保険 雇用保険 {memo}".strip())
    if vals['所得税'] > 0: gsheets.add_entry(worksheet, date, '支出', '税金', vals['所得税'], f"税金 所得税 {memo}".strip())
    
    if vals['持株積立'] > 0: gsheets.add_entry(worksheet, date, '支出', '投資費', vals['持株積立'], f"株 持株積立 {memo}".strip())
    if vals['社宅利用料'] > 0: gsheets.add_entry(worksheet, date, '支出', '生活費', vals['社宅利用料'], f"その他 社宅利用料 {memo}".strip())
    if vals['生命保険'] > 0: gsheets.add_entry(worksheet, date, '支出', '生活費', vals['生命保険'], f"保険 生命保険 {memo}".strip())
    if vals['組合費'] > 0: gsheets.add_entry(worksheet, date, '支出', '生活費', vals['組合費'], f"その他 組合費 {memo}".strip())
    if vals['食堂喫食代'] > 0: gsheets.add_entry(worksheet, date, '支出', '食費', vals['食堂喫食代'], f"社食 食堂喫食代 {memo}".strip())
    if vals['その他（支出）'] > 0: gsheets.add_entry(worksheet, date, '支出', 'その他', vals['その他（支出）'], f"その他（支出） {memo}".strip())

def process_bonus_entry(worksheet, date, vals, memo):
    """賞与内訳のスプレッドシートへの書き込み処理"""
    if vals['賞与額'] > 0: gsheets.add_entry(worksheet, date, '収入', '賞与', vals['賞与額'], f"賞与 {memo}".strip())
    if vals['その他（収入）'] > 0: gsheets.add_entry(worksheet, date, '収入', '賞与', vals['その他（収入）'], f"その他（収入） {memo}".strip())
    
    if vals['健康保険'] > 0: gsheets.add_entry(worksheet, date, '支出', '税金', vals['健康保険'], f"保険 健康保険 {memo}".strip())
    if vals['厚年保険'] > 0: gsheets.add_entry(worksheet, date, '支出', '税金', vals['厚年保険'], f"保険 厚年保険 {memo}".strip())
    if vals['雇用保険'] > 0: gsheets.add_entry(worksheet, date, '支出', '税金', vals['雇用保険'], f"保険 雇用保険 {memo}".strip())
    if vals['所得税'] > 0: gsheets.add_entry(worksheet, date, '支出', '税金', vals['所得税'], f"税金 所得税 {memo}".strip())
    if vals['その他（支出）'] > 0: gsheets.add_entry(worksheet, date, '支出', 'その他', vals['その他（支出）'], f"その他（支出） {memo}".strip())

def render(worksheet, today_jst):
    st.subheader("収支入力")

    # --- スマホ用に縦の余白を限界までギュッと詰めるCSS ---
    st.markdown("""
        <style>
        /* 各入力パーツの下の無駄な余白をカット */
        div[data-testid="stRadio"] { margin-bottom: -10px; }
        div[data-testid="stDateInput"] { margin-bottom: -10px; }
        /* フォーム全体を少し上に詰める */
        div[data-testid="stForm"] { margin-top: 5px; padding: 15px; }
        </style>
    """, unsafe_allow_html=True)

    # 1. 区分
    st.markdown("<div style='font-size: 12px; color: gray; margin-bottom: -10px;'>▼ 区分</div>", unsafe_allow_html=True)
    balance_type = st.radio("区分", ["支出","収入","投資"], horizontal=True, label_visibility="collapsed")
    category, amount, memo, sub_category = None, 0, "", ""
    investment_name, investment_amount = "", 0.0000
    entry_vals = {}

    st.write("") # 少し隙間

    # 2. カテゴリー選択
    if balance_type in ["支出", "収入"]:
        st.markdown("<div style='font-size: 12px; color: gray; margin-bottom: -10px;'>▼ 項目</div>", unsafe_allow_html=True)
        if balance_type == "支出":
            category = st.radio('項目', c.EXPENSE_CATEGORIES, horizontal=True, label_visibility="collapsed")
            sub_options = c.EXPENSE_SUB_CATEGORIES.get(category)
            if sub_options:
                st.markdown("<div style='font-size: 12px; color: gray; margin-top: 10px; margin-bottom: -10px;'>▼ 詳細</div>", unsafe_allow_html=True)
                sub_category = st.radio(f"{category}詳細", sub_options, horizontal=True, label_visibility="collapsed")
        elif balance_type == "収入":
            category = st.radio('項目', c.INCOME_CATEGORIES, horizontal=True, label_visibility="collapsed")
    
    st.write("") # 少し隙間

    # 3. 日付選択
    st.markdown("<div style='font-size: 12px; color: gray; margin-bottom: -10px;'>▼ 日付</div>", unsafe_allow_html=True)
    offset = st.radio("日付", ["今日", "1日前", "2日前", "3日前"], horizontal=True, label_visibility="collapsed")
    
    if offset == "今日":
        target_date = today_jst
    elif offset == "1日前":
        target_date = today_jst - datetime.timedelta(days=1)
    elif offset == "2日前":
        target_date = today_jst - datetime.timedelta(days=2)
    else:
        target_date = today_jst - datetime.timedelta(days=3)
        
    date = st.date_input(" ", value=target_date, label_visibility="collapsed")

    # 4. 入力フォーム
    with st.form(key='entry_form', clear_on_submit=True):
        if balance_type == "収入" and category == "給与":
            entry_vals = render_salary_form()
            memo = st.text_input('メモ（任意）')
            submit_btn = st.form_submit_button('一括登録する', use_container_width=True)
        elif balance_type == "収入" and category == "賞与":
            entry_vals = render_bonus_form()
            memo = st.text_input('メモ（任意）')
            submit_btn = st.form_submit_button('一括登録する', use_container_width=True)
        else:
            if balance_type in ["支出", "収入"]:
                amount = st.number_input('金額', min_value=0, step=1, value=None, placeholder="0")
            if balance_type == "投資":
                category = "投資"
                investment_name = st.text_input("銘柄名")
                investment_amount = st.number_input('数量', min_value=0.0, step=0.00000001, value=None, placeholder="0.0",format="%.8f")
                amount = st.number_input('支払い金額', min_value=0, step=1, value=None, placeholder="0")
            memo = st.text_input('メモ（任意）')
            submit_btn = st.form_submit_button('登録する', use_container_width=True)

    # 5. 送信処理
    if submit_btn:
        if balance_type == "収入" and category == "給与":
            try:
                process_salary_entry(worksheet, date, entry_vals, memo)
                st.success('給与・各種控除を一括登録しました。')
                st.balloons()
                time.sleep(3)
                st.rerun()
            except Exception as e:
                st.error(f'書き込みエラー: {e}')
        elif balance_type == "収入" and category == "賞与":
            try:
                process_bonus_entry(worksheet, date, entry_vals, memo)
                st.success('賞与・各種控除を一括登録しました。')
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