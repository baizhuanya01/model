import streamlit as st
import pandas as pd
import plotly.express as px

st.title("数字沙盘 - 练习")

# 第一步：上传文件
uploaded_file = st.file_uploader("上传财务模型 Excel", type=["xls", "xlsx"])


if uploaded_file:
    # 第二步：读取 Excel，指定读哪张表
    # sheet_name 对应 Excel 里的 tab 名，先用发电量那张
    df = pd.read_excel(uploaded_file, sheet_name="发电量及上网电价", header=1)
    df2 = pd.read_excel(uploaded_file, sheet_name="项目投资现金流量表", header=1)
    st.dataframe(df2.head(10))
    st.write(df2["项目"].tolist())

    df = df[df["年数"].apply(lambda x: str(x).isdigit())]

    # 取索引16那一行，从第3列开始（跳过序号、项目名、合计列）
    row = df2.iloc[16, 3:]

    # 列名就是年份（1-25），值就是累计现金流
    years = row.index.tolist()
    values = row.values.tolist()

    # 画图
    fig_cf = px.line(
        x=years,
        y=values,
        title="累计现金流量（税后）",
        labels={"x": "年数", "y": "万元"}
    )
    fig_cf.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="回收期")


    with st.sidebar:
        chart_type = st.selectbox("图表类型", ["折线图", "柱状图", "面积图"])
        valid_cols = [c for c in df.columns if "Unnamed" not in str(c) and c != "年数"]
        selected_cols = st.multiselect(
            "选择要展示的列",
            options=valid_cols,
            default=[valid_cols[0]]
        )

    if chart_type == "折线图":
        fig = px.line(df,x="年数",y=selected_cols,title="25年逐年发电量")
    elif chart_type == "柱状图":
        fig = px.bar(df,x="年数",y=selected_cols,title="25年逐年发电量")
    elif chart_type == "面积图":
        fig = px.area(df,x="年数",y=selected_cols,title="25年逐年发电量")

    st.plotly_chart(fig)
    st.plotly_chart(fig_cf)

options=["年发电量（KWH）", "售电收入（元）", "年减排二氧化碳（T）"]



