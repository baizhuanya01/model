# 目标：输入装机规模和发电小时数，预测年收入
# 用 scikit-learn 的线性回归做占位模型
import numpy as np
import pandas as pd
import plotly.express as px
# from sklearn.linear_model import LinearRegression
import streamlit as st
import plotly.graph_objects as go
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

st.set_page_config(layout="wide")
st.title("数字沙盘")

current_view = st.radio(
    "视图",
    ["🤖 ML预测模型", "📊 经济性分析"],
    horizontal=True,
    label_visibility="collapsed"
)

if current_view == "🤖 ML预测模型":

    # === 使用说明 ===
    with st.expander("📋 使用须知（正式版）"):
        st.markdown("""
    **功能概述**

    数字沙盘提供数据可视化与机器学习预测两项核心功能，支持上传结构化数据文件，自动训练神经网络回归模型并输出预测结果。

    **支持的文件格式**
    - Excel（.xls、.xlsx）
    - CSV（UTF-8编码）

    **数据格式要求**
    - 第一行必须为列名
    - 数据须为纯数值型，不支持含文字、合并单元格或多级表头的文件
    - 建议样本量不少于50条，低于30条时模型评估结果不具参考价值

    **功能限制**
    - 当前模型为多层感知机回归（MLP），仅适用于数值型回归预测任务，不支持分类问题
    - 模型参数固定（两层隐藏层，64和32个神经元），不提供界面内调参功能
    - 测试集比例固定为20%，样本量过少时测试集可能仅有1-2条数据，R²分数不可靠
    - 预测结果仅供参考，不构成决策依据

    **注意事项**
    - 每次上传新文件后模型会重新训练，之前的训练结果不会保留
    - 服务器端不存储任何上传数据
    - 平台部署于Streamlit Community Cloud，国内访问可能存在延迟
    """)

    with st.expander("🙂 使用须知（随意版）"):
        st.markdown("""
    **能做的：**
    - 上传一张干净的表，选好特征列和目标列，自动帮你训练一个神经网络
    - 训练完可以手动输入参数看预测结果
    - 用预测vs真实的散点图直观看模型准不准

    **不能做的：**
    - 数据太少（低于50条）的时候R²分数基本没参考价值，别太当真
    - 表格里有合并单元格、多级表头、文字混数字的情况读不进来，需要先整理干净
    - 模型参数是固定的，不能在页面上调，想调要改代码
    - 预测结果是模型算的，不是真理，仅供参考

    **用之前注意：**
    - 文件格式只支持 xls、xlsx、csv
    - 第一行必须是列名，数据全部是数字
    - 每次上传新文件模型会重新训练，不保留历史结果
    - 网站在国外服务器，加载慢是正常的，不是崩了
    """)

    # === 数据准备 ===
    uploaded_file = st.file_uploader("上传数据", type=["xls", "xlsx", "csv"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xls") or uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)

        feature_cols = st.multiselect("选择特征列", options=df.columns.tolist())
        target_col = st.selectbox("选择目标列", options=df.columns.tolist())
        if feature_cols and target_col:  # 确保都选了才继续
            X = df[feature_cols].values
            y = df[target_col].values
            # 后面的训练代码都缩进在这里面

            # === 分割数据 ===
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # === 归一化 ===
            scaler_X = StandardScaler()
            scaler_y = StandardScaler()

            X_train_scaled = scaler_X.fit_transform(X_train)
            y_train_scaled = scaler_y.fit_transform(y_train.reshape(-1, 1)).flatten()

            # === 训练模型 ===
            model = MLPRegressor(hidden_layer_sizes=(64, 32), activation="relu", max_iter=1000, random_state=42)
            model.fit(X_train_scaled, y_train_scaled)

            st.write(f"训练损失：{model.loss_:.4f}，训练轮数：{model.n_iter_}")

            # === 评估 ===
            X_test_scaled = scaler_X.transform(X_test)
            y_test_scaled = scaler_y.transform(y_test.reshape(-1, 1)).flatten()
            score = model.score(X_test_scaled, y_test_scaled)
            st.write(f"测试集 R² 分数：{score:.4f}")

            # === 用户输入预测 ===
            st.divider()
            st.subheader("输入预测")

            inputs = []
            for col in feature_cols:
                val = st.number_input(f"{col}", value=float(df[col].mean()))
                inputs.append(val)


            input_scaled = scaler_X.transform([inputs])
            predicted_scaled = model.predict(input_scaled)
            predicted = scaler_y.inverse_transform(predicted_scaled.reshape(-1, 1))[0][0]
            st.metric("预测年收入", f"{predicted:.0f} 万元")

            # === 画图 用测试集画预测vs真实===
            y_pred_scaled = model.predict(X_test_scaled)
            y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
            y_true = y_test

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=y_true, y=y_pred, mode="markers", name="预测vs真实"))
            fig.add_trace(go.Scatter(
                x=[y_true.min(), y_true.max()],
                y=[y_true.min(), y_true.max()],
                mode="lines", name="理想线"
            ))
            fig.update_layout(title="预测值 vs 真实值", xaxis_title="真实收入(万元)", yaxis_title="预测收入(万元)")
            st.plotly_chart(fig)
    else:
        st.info("请先上传训练数据")

if current_view == "📊 经济性分析":
    st.title("磷酸铁锂储能系统经济性分析")

    # ============================================================
    # 侧边栏：动态参数
    # ============================================================
    with st.sidebar:
        st.header("⚙️ 参数调节")
        with st.expander("成本参数"):
            battery_price = st.slider("电池采购单价（元/kWh）", 500, 2000, 900, step=50,
                                    help="磷酸铁锂电芯当前市场价格区间约为500-1500元/kWh")
            capacity = st.slider("系统装机容量（MWh）", 1, 100, 10, step=1,
                                help="储能系统总能量容量")
            cycle_life = st.slider("循环寿命（次）", 2000, 6000, 4000, step=100,
                                    help="电池在容量衰减至80%前可完成的充放电次数")
                                    
        with st.expander("参数权重(土建安装占比自动计算)"):
            b1 = st.slider("电芯成本占比",30,70,55,
                            help="电池本体，磷酸铁锂电芯，是最大头")/100
            b2 = st.slider("PCS及配套占比",10,50,25,
                            help="储能变流器 + BMS电池管理系统 + EMS能量管理系统")/100
            b3 = 1 - b1 - b2
            if b3 < 0:
                st.warning("电芯和PCS占比之和超过100%，请重新调整")
                st.stop()

        with st.expander("收益参数"):
            price_diff = st.slider("峰谷电价差（元/kWh）", 0.3, 1.5, 0.7, step=0.05,
                                    help="峰时电价与谷时电价之差，直接决定套利收益")
            efficiency = st.slider("充放电效率（%）", 80, 98, 92, step=1,
                                    help="一次完整充放电循环的能量转换效率") / 100
            cycles_per_year = st.slider("年充放电次数", 200, 365, 300, step=10,
                                        help="每年实际完成的充放电循环次数")

        with st.expander("财务参数"):
            discount_rate = st.slider("折现率（%）", 3, 15, 8, step=1,
                                    help="用于计算净现值（NPV）的资金时间价值折现率") / 100
            opex_rate = st.slider("年运维费率（%）", 0.5, 3.0, 1.5, step=0.1,
                                help="每年运维成本占初始投资的比例") / 100

    # ============================================================
    # 核心计算
    # ============================================================
    # 初始投资（CAPEX）
    capex = battery_price * capacity * 1000  # 元

    # 年收益
    annual_revenue = capacity * 1000 * efficiency * price_diff * cycles_per_year  # 元

    # 年运维成本（OPEX）
    annual_opex = capex * opex_rate

    # 年净收益
    annual_net = annual_revenue - annual_opex

    # 项目寿命（循环寿命/年充放电次数）
    project_life = int(cycle_life / cycles_per_year)

    # 静态投资回收期
    payback = capex / annual_net if annual_net > 0 else float("inf")

    # NPV
    npv = sum([annual_net / (1 + discount_rate) ** t for t in range(1, project_life + 1)]) - capex

    # 碳减排（每度电折算0.581kg CO₂，国家电网排放因子）
    annual_emission_reduction = capacity * 1000 * efficiency * cycles_per_year * 0.581 / 1000  # 吨

    # ============================================================
    # 顶部大屏：核心指标
    # ============================================================
    st.subheader("📊 核心指标概览")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("初始投资（万元）", f"{capex/10000:.0f}")
    col2.metric("静态回收期（年）", f"{payback:.1f}" if payback != float("inf") else "不可回收")
    col3.metric("净现值 NPV（万元）", f"{npv/10000:.0f}", delta="正收益" if npv > 0 else "负收益")
    col4.metric("年碳减排（吨CO₂）", f"{annual_emission_reduction:.0f}")

    st.divider()

    # ============================================================
    # 图表区
    # ============================================================
    col_left, col_right = st.columns(2)

    # 1. 累计现金流图（含盈亏平衡点）
    with col_left:
        st.subheader("💰 累计现金流")
        years = list(range(0, project_life + 1))
        cumulative_cf = [-capex] + [-capex + annual_net * t for t in range(1, project_life + 1)]

        fig_cf = go.Figure()
        fig_cf.add_trace(go.Scatter(
            x=years, y=[v / 10000 for v in cumulative_cf],
            mode="lines+markers", name="累计现金流",
            fill="tozeroy",
            line=dict(color="#00b4d8")
        ))
        fig_cf.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="盈亏平衡")
        fig_cf.update_layout(
            xaxis_title="年份", yaxis_title="万元",
            plot_bgcolor="#1a1a2e", paper_bgcolor="#1a1a2e",
            font=dict(color="white")
        )
        st.plotly_chart(fig_cf, use_container_width=True)

    # 2. 成本构成饼图
    with col_right:
        st.subheader("🥧 全寿命周期成本构成")
        total_opex = annual_opex * project_life
        labels = ["电芯成本", "PCS及配套", "土建安装", "运维成本（全周期）"]
        values = [capex * b1, capex * b2, capex * b3, total_opex]

        fig_pie = go.Figure(go.Pie(
            labels=labels, values=values,
            hole=0.4,
            marker=dict(colors=["#00b4d8", "#0077b6", "#023e8a", "#48cae4"])
        ))
        fig_pie.update_layout(
            plot_bgcolor="#1a1a2e", paper_bgcolor="#1a1a2e",
            font=dict(color="white")
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # 3. 敏感性分析（Tornado图）
    st.subheader("🌪️ 敏感性分析")
    st.caption("各参数变动±10%对NPV的影响（万元）")

    params = ["电池单价", "峰谷电价差", "循环寿命", "充放电效率", "年充放电次数", "折现率"]
    sensitivity = []
    delta = 0.1

    base_params = {
        "battery_price": battery_price,
        "price_diff": price_diff,
        "cycle_life": cycle_life,
        "efficiency": efficiency,
        "cycles_per_year": cycles_per_year,
        "discount_rate": discount_rate
    }

    def calc_npv(bp, pd_, cl, eff, cpy, dr):
        cap = bp * capacity * 1000
        rev = capacity * 1000 * eff * pd_ * cpy
        opex = cap * opex_rate
        net = rev - opex
        life = int(cl / cpy)
        return sum([net / (1 + dr) ** t for t in range(1, life + 1)]) - cap

    for param in ["battery_price", "price_diff", "cycle_life", "efficiency", "cycles_per_year", "discount_rate"]:
        p = base_params.copy()
        p[param] *= (1 + delta)
        npv_up = calc_npv(p["battery_price"], p["price_diff"], p["cycle_life"],
                        p["efficiency"], p["cycles_per_year"], p["discount_rate"])
        p[param] = base_params[param] * (1 - delta)
        npv_down = calc_npv(p["battery_price"], p["price_diff"], p["cycle_life"],
                            p["efficiency"], p["cycles_per_year"], p["discount_rate"])
        sensitivity.append((npv_up - npv) / 10000)

    fig_tornado = go.Figure(go.Bar(
        x=sensitivity, y=params,
        orientation="h",
        marker=dict(color=["#00b4d8" if v > 0 else "#e63946" for v in sensitivity])
    ))
    fig_tornado.update_layout(
        xaxis_title="NPV变化（万元）",
        plot_bgcolor="#1a1a2e", paper_bgcolor="#1a1a2e",
        font=dict(color="white")
    )
    st.plotly_chart(fig_tornado, use_container_width=True)