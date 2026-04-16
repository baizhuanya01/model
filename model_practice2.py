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