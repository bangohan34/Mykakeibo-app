import streamlit as st
import datetime
import time
import const as c
import gsheets
import streamlit.components.v1 as components

def inject_auto_clear_script():
    """スマホやPCで数値入力欄をタップした際、0なら即座に消し、数値なら全選択する最強のJS"""
    components.html("""
    <script>
    function setupInputs() {
        const doc = window.parent.document;
        const inputs = doc.querySelectorAll('input[type="number"]');
        
        inputs.forEach(input => {
            if (!input.dataset.smartClear) {
                input.dataset.smartClear = 'true';
                
                // フォーカス（タップ）されたとき
                input.addEventListener('focus', function() {
                    if (this.value === '0') {
                        this.value = ''; // 0なら一瞬で空欄にする
                        this.dispatchEvent(new Event('input', { bubbles: true }));
                    } else {
                        this.select(); // 0以外なら全選択する
                    }
                });
                
                // フォーカスが外れて空欄だった場合、0に戻す
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

    // Streamlitの再描画（タブ切り替えなど）にも対応する監視機能
    const observer = new MutationObserver(() => {
        setupInputs();
    });
    observer.observe(window.parent.document.body, { childList: true, subtree: true });

    // 初回実行
    setTimeout(setupInputs, 200);
    </script>
    """, height=0, width=0)

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
    if vals['組合費'] >