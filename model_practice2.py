# 目标：输入装机规模和发电小时数，预测年收入
# 用 scikit-learn 的线性回归做占位模型
import numpy as np
import pandas as pd
# from sklearn.linear_model import LinearRegression
import streamlit as st
# import plotly.express as px
import plotly.graph_objects as go
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

st.title("模型练习 - 神经网络多特征预测")

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