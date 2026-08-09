import altair as alt
import pandas as pd
import const as c

def create_combo_chart(data, x_col, x_format, tooltip_format, x_label_angle=0):
    bar_data = data.groupby([x_col, '区分'])['グラフ金額'].sum().reset_index()
    bars = alt.Chart(bar_data).mark_bar().encode(
        x=alt.X(x_col, axis=alt.Axis(format=x_format, title=None, labelAngle=x_label_angle)),
        y=alt.Y('グラフ金額', axis=alt.Axis(title='収支 & 残高 (円)', grid=True)),
        color=alt.Color('区分', scale=alt.Scale(domain=['収入', '支出'], range=["#379c72", "#A03333"]), legend=None),
        tooltip=[
            alt.Tooltip(x_col, format=tooltip_format, title='期間'),
            '区分',
            alt.Tooltip('グラフ金額', format=',', title='金額')
        ]
    )
    line_data = data.groupby(x_col)['現金推移'].last().reset_index()
    line = alt.Chart(line_data).mark_line(color="#498dd1", point=True).encode(
        x=alt.X(x_col, axis=alt.Axis(format=x_format, title=None)),
        y='現金推移',
        tooltip=[
            alt.Tooltip(x_col, format=tooltip_format, title='期間'),
            alt.Tooltip('現金推移', format=',', title='残高')
        ]
    )
    chart = alt.layer(bars, line).resolve_scale(y='shared').properties(height=300)
    return chart.configure_axis(
        labelColor='#703B3B',
        titleColor='#703B3B',
        gridColor='#e0e0e0'
    )

def create_expense_pie_chart(data):
    expense_df = data[data['区分'] == '支出'].copy()
    if expense_df.empty:
        return None
    pie_data = expense_df.groupby('カテゴリー', as_index=False)['金額'].sum()
    pie_data = pie_data.sort_values('金額', ascending=False)
    if 'その他' in pie_data['カテゴリー'].values:
        others_row = pie_data[pie_data['カテゴリー'] == 'その他']
        normal_rows = pie_data[pie_data['カテゴリー'] != 'その他']
        pie_data = pd.concat([normal_rows, others_row])
    pie_data['order_index'] = range(len(pie_data))
    sort_order = pie_data['カテゴリー'].tolist()
    domain = []
    range_ = []
    for cat in sort_order:
        domain.append(cat)
        range_.append(c.PIE_CHART_CATEGORIES_COLORS.get(cat, '#CFCFCF'))
    total_expense = pie_data['金額'].sum()
    pie_data['割合'] = pie_data['金額'] / total_expense
    base = alt.Chart(pie_data).encode(
        theta=alt.Theta("金額", stack=True),
        color=alt.Color(
            "カテゴリー", 
            legend=alt.Legend(title="カテゴリー"), 
            sort=sort_order,
            scale=alt.Scale(domain=domain, range=range_) 
        ),
        order=alt.Order("order_index", sort="ascending"),
        tooltip=[
            "カテゴリー", 
            alt.Tooltip("金額", format=","),
            alt.Tooltip("割合", format=".1%", title="構成比")
        ]
    )
    pie = base.mark_arc(
        innerRadius=50,
        outerRadius=90,
        stroke="#d3d3d3"
        ).properties(
            height=200
        )
    return pie.configure_view(
        strokeOpacity=0
    ).configure_legend(
        labelColor='#703B3B',
        titleColor='#703B3B',
        symbolStrokeWidth=0
    )

def create_expense_bar_chart(data, x_col, x_format, tooltip_format, x_label_angle=0):
    bar_data = data[data['区分'] == '支出'].groupby(x_col)['金額'].sum().reset_index()
    bars = alt.Chart(bar_data).mark_bar(color="#A03333").encode(
        x=alt.X(x_col, axis=alt.Axis(format=x_format, title=None, labelAngle=x_label_angle)),
        y=alt.Y('金額', axis=alt.Axis(title='支出 (円)', grid=True)),
        tooltip=[
            alt.Tooltip(x_col, format=tooltip_format, title='期間'),
            alt.Tooltip('金額', format=',', title='支出'),
        ]
    ).properties(height=300)
    return bars.configure_axis(
        labelColor='#703B3B',
        titleColor='#703B3B',
        gridColor='#e0e0e0'
    )