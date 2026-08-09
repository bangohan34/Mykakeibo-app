import altair as alt

def create_balance_chart(data, x_col, x_format, tooltip_format, x_label_angle=0):
    line_data = data.groupby(x_col)['現金推移'].last().reset_index()
    line = alt.Chart(line_data).mark_line(color="#498dd1", point=True).encode(
        x=alt.X(x_col, axis=alt.Axis(format=x_format, title=None, labelAngle=x_label_angle)),
        # scale(zero=False)により縦軸のスケールが自動調整されます
        y=alt.Y('現金推移', scale=alt.Scale(zero=False), axis=alt.Axis(title='現金残高 (円)', grid=True)),
        tooltip=[
            alt.Tooltip(x_col, format=tooltip_format, title='期間'),
            alt.Tooltip('現金推移', format=',', title='残高')
        ]
    ).properties(height=250)
    return line.configure_axis(labelColor='#703B3B', titleColor='#703B3B', gridColor='#e0e0e0')

def create_expense_chart(data, x_col, x_format, tooltip_format, x_label_angle=0):
    exp_data = data[data['区分'] == '支出']
    bar_data = exp_data.groupby(x_col)['金額'].sum().reset_index()
    bars = alt.Chart(bar_data).mark_bar(color="#A03333").encode(
        x=alt.X(x_col, axis=alt.Axis(format=x_format, title=None, labelAngle=x_label_angle)),
        y=alt.Y('金額', axis=alt.Axis(title='支出 (円)', grid=True)),
        tooltip=[
            alt.Tooltip(x_col, format=tooltip_format, title='期間'),
            alt.Tooltip('金額', format=',', title='支出')
        ]
    ).properties(height=250)
    return bars.configure_axis(labelColor='#703B3B', titleColor='#703B3B', gridColor='#e0e0e0')

def create_utilities_chart(data):
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('種類:N', title=None, axis=alt.Axis(labels=False, ticks=False)),
        y=alt.Y('金額:Q', title='金額 (円)', grid=True),
        color=alt.Color('種類:N', scale=alt.Scale(domain=['ガス', '電気', '水道'], range=['#f08976', '#f2d879', '#63a3d8'])),
        column=alt.Column('年月:O', header=alt.Header(title=None, labelOrient='bottom', labelColor='#703B3B')),
        tooltip=[
            alt.Tooltip('年月:O', title='月'),
            alt.Tooltip('種類:N', title='種類'),
            alt.Tooltip('金額:Q', format=',', title='金額')
        ]
    ).properties(width=40, height=250)
    return chart.configure_view(stroke='transparent').configure_axis(labelColor='#703B3B', titleColor='#703B3B', gridColor='#e0e0e0')