#!/usr/bin/env python3
"""
Mephisto 可视化界面
使用 Streamlit 搭建
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 页面配置
st.set_page_config(
    page_title="Mephisto SED Modeling",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("🔭 Mephisto SED Modeling Agent")
st.markdown("---")

# 侧边栏
st.sidebar.header("⚙️ 配置")

# 模拟数据选择
data_source = st.sidebar.selectbox(
    "选择数据源",
    ["模拟数据", "上传 CSV", "示例数据 (COSMOS)", "示例数据 (Little Red Dot)"]
)

# 红移设置
redshift = st.sidebar.slider("红移 (z)", 0.0, 10.0, 0.5, 0.1)

# 主页面布局
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 光度数据")

    # 模拟光度数据表格
    bands = ['FUV', 'NUV', 'u', 'g', 'r', 'i', 'z', 'J', 'H', 'K']
    wavelengths = [1528, 2271, 3650, 4750, 6250, 7700, 9100, 12500, 16500, 22000]

    # 生成模拟流量数据
    np.random.seed(42)
    fluxes = [1.5e-29 * (1+redshift)**2 * np.random.uniform(0.8, 1.2) for _ in bands]
    errors = [f * 0.1 for f in fluxes]

    phot_data = pd.DataFrame({
        '波段': bands,
        '波长 (Å)': wavelengths,
        '流量 (erg/s/cm²/Hz)': [f"{f:.2e}" for f in fluxes],
        '误差': [f"{e:.2e}" for e in errors]
    })

    st.dataframe(phot_data, use_container_width=True)

with col2:
    st.subheader("📈 统计信息")
    st.metric("波段数量", len(bands))
    st.metric("红移", f"{redshift:.2f}")
    st.metric("波长范围", f"{min(wavelengths)}-{max(wavelengths)} Å")

st.markdown("---")

# SED 配置部分
st.subheader("🔧 SED 模型配置")

config_col1, config_col2, config_col3 = st.columns(3)

with config_col1:
    st.markdown("**恒星形成历史 (SFH)**")
    sfh_model = st.selectbox("SFH 模型", ["sfhdelayed", "sfh2exp", "sfhperiodic", "sfhdelayedbq"])
    tau_main = st.slider("τ_main (Myr)", 100, 13000, 5000, 100)
    age_main = st.slider("Age_main (Myr)", 100, 13000, 7000, 100)

with config_col2:
    st.markdown("**恒星种群 (SSP)**")
    ssp_model = st.selectbox("SSP 模型", ["bc03", "m2005"])
    imf = st.selectbox("IMF", ["Chabrier", "Salpeter"])
    metallicity = st.slider("金属丰度", 0.001, 0.05, 0.02, 0.001)

with config_col3:
    st.markdown("**尘埃消光 (Dust Attenuation)**")
    dust_model = st.selectbox("尘埃模型", ["dustatt_modified_starburst", "dustatt_modified_CF00"])
    e_bv = st.slider("E(B-V)", 0.0, 1.0, 0.3, 0.05)

    # 可选模块
    st.markdown("**可选模块**")
    use_agn = st.checkbox("AGN", value=False)
    use_nebular = st.checkbox("星云发射", value=True)
    use_dustem = st.checkbox("尘埃发射", value=False)

st.markdown("---")

# 运行拟合按钮
if st.button("🚀 运行 SED 拟合", type="primary", use_container_width=True):
    with st.spinner("正在进行 SED 拟合..."):
        import time
        time.sleep(2)  # 模拟计算时间

        # 生成模拟结果
        st.success("✅ 拟合完成!")

        # 结果显示区域
        result_col1, result_col2, result_col3 = st.columns(3)

        with result_col1:
            st.metric("Chi²", f"{np.random.uniform(50, 150):.2f}")
        with result_col2:
            st.metric("Reduced Chi²", f"{np.random.uniform(0.8, 1.5):.3f}")
        with result_col3:
            st.metric("拟合参数", f"{np.random.randint(20, 40)}")

        # SED 图
        st.subheader("📈 SED 光谱能量分布")

        # 生成模拟 SED
        wave_sed = np.logspace(3, 6, 500)  # 从 1000 Å 到 1e6 Å

        # 简单的黑洞体 + 尘埃消光模拟
        T = 5000  # 温度
        sed_flux = 2e-29 * (wave_sed / 5000)**(-2) * np.exp(-((wave_sed/1e5)**0.5))
        sed_flux *= np.exp(-e_bv * (wave_sed/5500)**(-0.7))  # 消光

        # 添加AGN成分
        if use_agn:
            agn_flux = 1e-29 * (wave_sed / 10000)**(-0.5)
            sed_flux += agn_flux

        fig = go.Figure()

        # 绘制 SED
        fig.add_trace(go.Scatter(
            x=wave_sed,
            y=sed_flux,
            mode='lines',
            name='SED 模型',
            line=dict(color='blue', width=2)
        ))

        # 绘制观测数据点
        fig.add_trace(go.Scatter(
            x=wavelengths,
            y=fluxes,
            mode='markers',
            name='观测数据',
            marker=dict(color='red', size=10, symbol='circle')
        ))

        # 误差棒
        fig.add_trace(go.Scatter(
            x=wavelengths,
            y=fluxes,
            error_y=dict(type='data', array=errors, visible=True),
            mode='markers',
            marker=dict(color='red', size=0),
            showlegend=False
        ))

        fig.update_layout(
            xaxis_type="log",
            yaxis_type="log",
            xaxis_title="波长 (Å)",
            yaxis_title="流量 (erg/s/cm²/Hz)",
            template="plotly_white",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # 残差图
        st.subheader("📊 拟合残差")

        residuals = np.random.normal(0, 0.1, len(bands))

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=bands,
            y=residuals,
            marker_color=['green' if abs(r) < 0.1 else 'orange' if abs(r) < 0.2 else 'red' for r in residuals]
        ))
        fig2.add_hline(y=0, line_dash="dash", line_color="black")
        fig2.update_layout(
            xaxis_title="波段",
            yaxis_title="残差 (标准化)",
            template="plotly_white",
            height=300
        )

        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Agent 决策历史
st.subheader("🤖 Agent 决策历史")

if st.checkbox("显示模拟决策历史"):
    history_data = pd.DataFrame({
        '迭代': [1, 2, 3, 4, 5],
        'Chi²': [120.5, 98.3, 85.2, 78.5, 76.3],
        'Reduced Chi²': [1.45, 1.18, 1.02, 0.94, 0.91],
        '模块数': [5, 6, 6, 7, 7],
        '操作': ['初始', '添加 AGN', '微调参数', '添加尘埃', '优化完成']
    })

    st.dataframe(history_data, use_container_width=True)

    # 优化曲线
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

    fig3.add_trace(
        go.Scatter(x=history_data['迭代'], y=history_data['Chi²'],
                  name="Chi²", mode='lines+markers'),
        secondary_y=False
    )

    fig3.add_trace(
        go.Scatter(x=history_data['迭代'], y=history_data['Reduced Chi²'],
                  name="Reduced Chi²", mode='lines+markers'),
        secondary_y=True
    )

    fig3.update_xaxes(title_text="迭代次数")
    fig3.update_yaxes(title_text="Chi²", secondary_y=False)
    fig3.update_yaxes(title_text="Reduced Chi²", secondary_y=True)

    st.plotly_chart(fig3, use_container_width=True)

# 页脚
st.markdown("---")
st.markdown("<center>Made with ❤️ using Streamlit | Mephisto SED Modeling</center>", unsafe_allow_html=True)
