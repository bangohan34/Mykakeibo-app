import altair as alt

def create_balance_chart(data, x_col, x_format, tooltip_format, x_label_angle=0):
    line_data = data.groupby(x_col)['現金推移'].last().reset_index()
    line = alt.Chart(line_data).mark_line(color="#498dd1", point=True).encode(
        x=alt.X(f"{x_col}:T", axis=alt.Axis(format=x_format, title=None, labelAngle=x_label_angle)),
        y=alt.Y('現金推移:Q', scale=alt.Scale(zero=False), axis=alt.Axis(title='現金残高 (円)', grid=True)),
        tooltip=[
            alt.Tooltip(f"{x_col}:T", format=tooltip_format, title='期間'),
            alt.Tooltip('現金推移:Q', format=',', title='残高')
        ]
    ).properties(height=250)
    return line.configure_axis(labelColor='#703B3B', titleColor='#703B3B', gridColor='#e0e0e0')

def create_expense_chart(data, x_col, x_format, tooltip_format, x_label_angle=0):
    exp_data = data[data['区分'] == '支出']
    bar_data = exp_data.groupby(x_col)['金額'].sum().reset_index()
    bars = alt.Chart(bar_data).mark_bar(color="#A03333").encode(
        x=alt.X(f"{x_col}:T", axis=alt.Axis(format=x_format, title=None, labelAngle=x_label_angle)),
        y=alt.Y('金額:Q', axis=alt.Axis(title='支出 (円)', grid=True)),
        tooltip=[
            alt.Tooltip(f"{x_col}:T", format=tooltip_format, title='期間'),
            alt.Tooltip('金額:Q', format=',', title='支出')
        ]
    ).properties(height=250)
    return bars.configure_axis(labelColor='#703B3B', titleColor='#703B3B', gridColor='#e0e0e0')

def create_utilities_chart(data):
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('年月:O', title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('金額:Q', axis=alt.Axis(title='金額 (円)', grid=True)),
        color=alt.Color('種類:N', scale=alt.Scale(domain=['ガス', '電気', '水道'], range=['#f08976', '#f2d879', '#63a3d8'])),
        tooltip=[
            alt.Tooltip('年月:O', title='月'),
            alt.Tooltip('種類:N', title='種類'),
            alt.Tooltip('金額:Q', format=',', title='金額')
        ]
    ).properties(height=250)
    return chart.configure_view(stroke='transparent').configure_axis(labelColor='#703B3B', titleColor='#703B3B', gridColor='#e0e0e0')

def create_salary_chart(data):
    # ★ 積み上げ順を制御するために、裏側でソート用の番号を振る
    df = data.copy()
    df['並び順'] = df['項目'].map({'本給': 1, '超勤手当': 2, 'その他': 3}).fillna(4)

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('年月:O', title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('金額:Q', axis=alt.Axis(title='金額 (円)', grid=True)),
        color=alt.Color('項目:N', scale=alt.Scale(
            domain=['本給', '超勤手当', 'その他'],
            range=["#61da83", "#d46767", '#8c857d']
        ), sort=['本給', '超勤手当', 'その他']),
        # ★ ここで「1(本給)」が一番下に来るように指定
        order=alt.Order('並び順:Q', sort='ascending'),
        tooltip=[
            alt.Tooltip('年月:O', title='月'),
            alt.Tooltip('項目:N', title='内訳'),
            alt.Tooltip('金額:Q', format=',', title='金額')
        ]
    ).properties(height=250)
    return chart.configure_view(stroke='transparent').configure_axis(labelColor='#703B3B', titleColor='#703B3B', gridColor='#e0e0e0')

def create_investment_history_chart(data):
    line = alt.Chart(data).mark_line(color="#ff8c00", point=True).encode(
        x=alt.X('日付:T', axis=alt.Axis(format='%m/%d', title=None, labelAngle=-45)),
        y=alt.Y('評価額:Q', scale=alt.Scale(zero=False), axis=alt.Axis(title='評価額 (円)', grid=True)),
        tooltip=[
            alt.Tooltip('日付:T', format='%Y/%m/%d', title='日付'),
            alt.Tooltip('評価額:Q', format=',.0f', title='総評価額')
        ]
    ).properties(height=250)
    return line.configure_axis(labelColor='#703B3B', titleColor='#703B3B', gridColor='#e0e0e0')