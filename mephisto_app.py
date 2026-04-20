#!/usr/bin/env python3
"""
Mephisto SED Modeling - Streamlit App with CIGALE Integration
基于 CIGALE 的真实 SED 拟合可视化界面
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile
import os
import sys
import subprocess

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check if CIGALE is installed, if not, show warning
CIGALE_AVAILABLE = False
try:
    import pcigale
    CIGALE_AVAILABLE = True
except ImportError:
    st.warning("⚠️ CIGALE not installed. SED fitting functionality will be disabled.")
    st.info("To enable full functionality, please install CIGALE from https://cigale.lam.fr")

if CIGALE_AVAILABLE:
    from cigale_interface import CigaleRunner, FILTER_SETS, MODULE_CATEGORIES, run_simple_sed
else:
    # Define dummy values for when CIGALE is not available
    FILTER_SETS = {
        "SDSS": ["sdss.u", "sdss.g", "sdss.r", "sdss.i", "sdss.z"],
        "GALEX": ["galex.FUV", "galex.NUV"],
        "2MASS": ["2mass.J", "2mass.H", "2mass.Ks"],
        "WISE": ["wise.W1", "wise.W2", "wise.W3", "wise.W4"],
    }
    MODULE_CATEGORIES = {
        "SFH": ["sfhdelayed"],
        "SSP": ["bc03"],
    }
    CigaleRunner = None
    run_simple_sed = None

# Page configuration
st.set_page_config(
    page_title="Mephisto SED Modeling with CIGALE",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">🔭 Mephisto SED Modeling with CIGALE</p>', unsafe_allow_html=True)
st.markdown("**基于 CIGALE 的真实 SED 拟合工具**")
st.markdown("---")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'runner' not in st.session_state:
    st.session_state.runner = None
if 'computation_done' not in st.session_state:
    st.session_state.computation_done = False

# Sidebar configuration
st.sidebar.header("⚙️ 数据配置")

# Data source selection
data_source = st.sidebar.selectbox(
    "选择数据源",
    ["手动输入", "上传 CSV/TXT", "示例数据 (SDSS)", "示例数据 (JWST模拟)"]
)

# Object configuration
st.sidebar.subheader("天体参数")
object_id = st.sidebar.text_input("天体名称/ID", "galaxy_001")
redshift = st.sidebar.slider("红移 (z)", 0.0, 10.0, 0.5, 0.01)

# Photometric data input
st.sidebar.markdown("---")
st.sidebar.subheader("📊 光度数据")

# Filter selection
available_filters = []
for filt_list in FILTER_SETS.values():
    available_filters.extend(filt_list)
available_filters = sorted(list(set(available_filters)))

# Quick filter set selection
quick_set = st.sidebar.selectbox(
    "快速选择滤光片组",
    ["无", "SDSS", "GALEX", "2MASS", "WISE", "HST_ACS", "JWST_NIRCAM"]
)

# Initialize photometry data in session state
if 'photometry_df' not in st.session_state:
    # Default example data
    default_data = {
        'filter': ['sdss.u', 'sdss.g', 'sdss.r', 'sdss.i', 'sdss.z'],
        'flux_mJy': [10.5, 25.3, 45.8, 62.1, 78.5],
        'flux_err_mJy': [1.0, 2.0, 3.0, 4.0, 5.0]
    }
    st.session_state.photometry_df = pd.DataFrame(default_data)

# Load quick filter set
if quick_set != "无" and quick_set in FILTER_SETS:
    filters = FILTER_SETS[quick_set]
    # Generate example fluxes based on simple SED
    example_fluxes = [10 * (i+1) * np.random.uniform(0.8, 1.2) for i in range(len(filters))]
    example_errors = [f * 0.1 for f in example_fluxes]
    st.session_state.photometry_df = pd.DataFrame({
        'filter': filters,
        'flux_mJy': example_fluxes,
        'flux_err_mJy': example_errors
    })

# Data upload or manual input
if data_source == "上传 CSV/TXT":
    uploaded_file = st.sidebar.file_uploader("上传数据文件", type=['csv', 'txt'])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
            st.session_state.photometry_df = df
            st.sidebar.success(f"成功加载 {len(df)} 行数据")
        except Exception as e:
            st.sidebar.error(f"读取文件失败: {e}")

# Editable data table
st.sidebar.markdown("**编辑光度数据** (单位: mJy)")
edited_df = st.sidebar.data_editor(
    st.session_state.photometry_df,
    num_rows="dynamic",
    use_container_width=True,
    key="photometry_editor"
)
st.session_state.photometry_df = edited_df

# Main content area
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📊 光度数据可视化")

    if len(edited_df) > 0:
        # Create photometry plot
        fig_phot = go.Figure()

        fig_phot.add_trace(go.Scatter(
            x=edited_df['filter'],
            y=edited_df['flux_mJy'],
            mode='markers+lines',
            name='观测流量',
            marker=dict(size=12, color='blue'),
            error_y=dict(
                type='data',
                array=edited_df['flux_err_mJy'],
                visible=True,
                color='gray',
                thickness=1.5,
                width=3
            )
        ))

        fig_phot.update_layout(
            xaxis_title="滤光片",
            yaxis_title="流量 (mJy)",
            template="plotly_white",
            height=350,
            showlegend=True,
            yaxis_type="log"
        )

        st.plotly_chart(fig_phot, use_container_width=True)
    else:
        st.info("请添加光度数据")

with col2:
    st.subheader("📈 数据摘要")

    if len(edited_df) > 0:
        st.metric("波段数量", len(edited_df))
        st.metric("红移", f"{redshift:.3f}")
        st.metric("流量范围", f"{edited_df['flux_mJy'].min():.2f} - {edited_df['flux_mJy'].max():.2f} mJy")

        # Show data quality indicator
        snr = edited_df['flux_mJy'] / edited_df['flux_err_mJy']
        avg_snr = snr.mean()
        if avg_snr > 10:
            st.success(f"✅ 平均信噪比: {avg_snr:.1f} (优秀)")
        elif avg_snr > 5:
            st.info(f"ℹ️ 平均信噪比: {avg_snr:.1f} (良好)")
        else:
            st.warning(f"⚠️ 平均信噪比: {avg_snr:.1f} (较低)")

st.markdown("---")

# SED Model Configuration
st.subheader("🔧 CIGALE SED 模型配置")

config_tabs = st.tabs(["恒星形成历史", "恒星种群", "尘埃消光", "尘埃发射", "可选模块"])

with config_tabs[0]:
    st.markdown("**恒星形成历史 (SFH)**")
    col_sf1, col_sf2, col_sf3 = st.columns(3)

    with col_sf1:
        sfh_module = st.selectbox(
            "SFH 模型",
            MODULE_CATEGORIES["SFH"],
            index=1,  # sfhdelayed
            help="选择恒星形成历史模型"
        )

    with col_sf2:
        if sfh_module in ["sfhdelayed", "sfh2exp"]:
            tau_main = st.slider(
                "τ_main (主序星时标, Myr)",
                100, 20000, 5000, 100,
                help="主恒星种群的e-folding时间"
            )
            age_main = st.slider(
                "Age_main (主序星年龄, Myr)",
                100, 15000, 7000, 100,
                help="主恒星种群的年龄"
            )

    with col_sf3:
        if sfh_module in ["sfhdelayed", "sfh2exp"]:
            tau_burst = st.slider(
                "τ_burst (爆发时标, Myr)",
                10, 1000, 50, 10
            )
            f_burst = st.slider(
                "f_burst (爆发质量分数)",
                0.0, 1.0, 0.0, 0.05
            )

with config_tabs[1]:
    st.markdown("**恒星种群合成 (SSP)**")
    col_ssp1, col_ssp2, col_ssp3 = st.columns(3)

    with col_ssp1:
        ssp_module = st.selectbox(
            "SSP 模型",
            MODULE_CATEGORIES["SSP"],
            index=0,  # bc03
            help="选择恒星种群合成模型"
        )

    with col_ssp2:
        if ssp_module in ["bc03", "m2005"]:
            imf = st.selectbox(
                "初始质量函数 (IMF)",
                ["Salpeter", "Chabrier"],
                index=0,
                help="恒星初始质量函数"
            )
            imf_value = 0 if imf == "Salpeter" else 1

    with col_ssp3:
        metallicity = st.select_slider(
            "金属丰度 (Z)",
            options=[0.0001, 0.0004, 0.004, 0.008, 0.02, 0.05],
            value=0.02,
            help="恒星种群的金属丰度"
        )

with config_tabs[2]:
    st.markdown("**尘埃消光 (Dust Attenuation)**")
    col_dust1, col_dust2, col_dust3 = st.columns(3)

    with col_dust1:
        dust_module = st.selectbox(
            "尘埃消光模型",
            MODULE_CATEGORIES["Dust Attenuation"],
            index=0,
            help="选择尘埃消光定律"
        )

    with col_dust2:
        if dust_module == "dustatt_modified_CF00":
            av_ism = st.slider(
                "Av_ISM (ISM V波段消光)",
                0.0, 5.0, 1.0, 0.1
            )
            mu = st.slider(
                "μ (消光分配比例)",
                0.0, 1.0, 0.44, 0.01,
                help="Av_ISM / (Av_BC + Av_ISM)"
            )
        elif dust_module == "dustatt_modified_starburst":
            e_bv = st.slider(
                "E(B-V)",
                0.0, 2.0, 0.3, 0.05
            )

    with col_dust3:
        if dust_module == "dustatt_modified_CF00":
            slope_ism = st.slider(
                "ISM 消光斜率",
                -1.5, 0.0, -0.7, 0.1
            )
            slope_bc = st.slider(
                "BC 消光斜率",
                -2.0, -0.5, -1.3, 0.1
            )

with config_tabs[3]:
    st.markdown("**尘埃发射 (Dust Emission)**")
    col_dustem1, col_dustem2, col_dustem3 = st.columns(3)

    with col_dustem1:
        use_dust_emission = st.checkbox("包含尘埃发射", value=True)
        dust_emission_module = None
        if use_dust_emission:
            dust_emission_module = st.selectbox(
                "尘埃发射模型",
                MODULE_CATEGORIES["Dust Emission"],
                index=2,  # dl2007
                help="选择尘埃热发射模型"
            )

    with col_dustem2:
        if use_dust_emission and dust_emission_module in ["dl2007", "dl2014"]:
            qpah = st.select_slider(
                "PAH 质量分数 (%)",
                options=[0.47, 1.12, 1.77, 2.50, 3.19, 3.90, 4.58],
                value=2.50
            )
            umin = st.select_slider(
                "U_min (最小辐射场)",
                options=[0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0],
                value=1.0
            )

    with col_dustem3:
        if use_dust_emission and dust_emission_module in ["dl2007", "dl2014"]:
            gamma = st.slider(
                "γ (Umin到Umax的占比)",
                0.0, 1.0, 0.1, 0.01
            )

with config_tabs[4]:
    st.markdown("**可选模块**")
    col_opt1, col_opt2, col_opt3 = st.columns(3)

    with col_opt1:
        use_nebular = st.checkbox("星云发射 (Nebular)", value=True)
        if use_nebular:
            logU = st.select_slider(
                "电离参数 (logU)",
                options=[-4.0, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0],
                value=-2.0
            )
            zgas = st.select_slider(
                "气体金属丰度",
                options=[0.0001, 0.0004, 0.001, 0.002, 0.004, 0.008, 0.02, 0.05],
                value=0.02
            )

    with col_opt2:
        use_agn = st.checkbox("AGN 组件", value=False)
        if use_agn:
            agn_module = st.selectbox("AGN 模型", MODULE_CATEGORIES["AGN"])
            if agn_module == "skirtor2016":
                fracAGN = st.slider("AGN 比例", 0.0, 1.0, 0.1, 0.01)

    with col_opt3:
        use_xray = st.checkbox("X-ray 发射", value=False)
        use_radio = st.checkbox("射电发射", value=False)

st.markdown("---")

# Run CIGALE
st.subheader("🚀 运行 CIGALE SED 拟合")

run_col1, run_col2 = st.columns([1, 3])

with run_col1:
    run_button = st.button(
        "▶️ 运行拟合",
        type="primary",
        use_container_width=True,
        help="使用 CIGALE 计算 SED 模型"
    )

with run_col2:
    cores = st.slider("CPU 核心数", 1, 8, 4, 1)

if run_button:
    if not CIGALE_AVAILABLE:
        st.error("❌ CIGALE 未安装。请在本地运行此应用，或联系管理员安装 CIGALE。")
        st.info("安装指南: https://cigale.lam.fr")
    elif len(edited_df) == 0:
        st.error("❌ 请先添加光度数据")
    else:
        with st.spinner("正在运行 CIGALE，请稍候..."):
            try:
                # Create runner
                runner = CigaleRunner()
                st.session_state.runner = runner

                # Prepare photometry data
                photometry = dict(zip(edited_df['filter'], edited_df['flux_mJy']))
                photometry_err = dict(zip(edited_df['filter'], edited_df['flux_err_mJy']))

                # Create input file
                runner.create_input_data(object_id, redshift, photometry, photometry_err)

                # Build module list
                modules = [sfh_module, ssp_module]
                if use_nebular:
                    modules.append("nebular")
                modules.append(dust_module)
                if use_dust_emission and dust_emission_module:
                    modules.append(dust_emission_module)
                if use_agn:
                    modules.append("skirtor2016")
                if use_xray:
                    modules.append("yang20")
                if use_radio:
                    modules.append("radio")
                modules.append("redshifting")

                # Build module parameters
                module_params = {}

                # SFH parameters
                if sfh_module in ["sfhdelayed", "sfh2exp"]:
                    module_params[sfh_module] = {
                        "tau_main": tau_main,
                        "age_main": age_main,
                        "tau_burst": tau_burst,
                        "age_burst": 20,
                        "f_burst": f_burst,
                        "sfr_A": 1.0,
                        "normalise": True
                    }

                # SSP parameters
                if ssp_module in ["bc03", "m2005"]:
                    module_params[ssp_module] = {
                        "imf": imf_value,
                        "metallicity": metallicity,
                        "separation_age": 10
                    }
                elif ssp_module == "cb19":
                    module_params[ssp_module] = {
                        "imf": 1,  # Chabrier only
                        "metallicity": metallicity,
                        "separation_age": 10
                    }

                # Nebular parameters
                if use_nebular:
                    module_params["nebular"] = {
                        "logU": logU,
                        "zgas": zgas,
                        "ne": 100,
                        "f_esc": 0.0,
                        "f_dust": 0.0,
                        "lines_width": 300.0,
                        "emission": True
                    }

                # Dust attenuation parameters
                if dust_module == "dustatt_modified_CF00":
                    module_params[dust_module] = {
                        "Av_ISM": av_ism,
                        "mu": mu,
                        "slope_ISM": slope_ism,
                        "slope_BC": slope_bc,
                        "filters": "galex.FUV & generic.bessell.B & generic.bessell.V"
                    }
                elif dust_module == "dustatt_modified_starburst":
                    module_params[dust_module] = {
                        "E_BV": e_bv,
                        "R_V": 4.05,
                        "filters": "galex.FUV & generic.bessell.B & generic.bessell.V"
                    }

                # Dust emission parameters
                if use_dust_emission and dust_emission_module in ["dl2007", "dl2014"]:
                    module_params[dust_emission_module] = {
                        "qpah": qpah,
                        "umin": umin,
                        "umax": 1000000.0,
                        "gamma": gamma
                    }

                # AGN parameters
                if use_agn:
                    module_params["skirtor2016"] = {
                        "t": 5.0,
                        "pl": 1.0,
                        "q": 1.0,
                        "oa": 40.0,
                        "R": 20.0,
                        "Mcl": 0.97,
                        "i": 30.0,
                        "fracAGN": fracAGN if 'fracAGN' in locals() else 0.1
                    }

                # Create configuration
                runner.create_config(modules, module_params, cores=cores)

                # Run CIGALE
                success, message = runner.run()

                if success:
                    st.session_state.results = runner.get_results()
                    st.session_state.computation_done = True
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")

            except Exception as e:
                st.error(f"❌ 运行出错: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# Display results
if st.session_state.computation_done and st.session_state.results is not None:
    st.markdown("---")
    st.subheader("📊 CIGALE 拟合结果")

    results_df = st.session_state.results

    # Results summary
    result_cols = st.columns(4)

    with result_cols[0]:
        if 'stellar.m_star' in results_df.columns:
            m_star = results_df['stellar.m_star'].values[0]
            st.metric("恒星质量 (M☉)", f"{m_star:.3f}")

    with result_cols[1]:
        if 'sfh.sfr' in results_df.columns:
            sfr = results_df['sfh.sfr'].values[0]
            st.metric("恒星形成率 (M☉/yr)", f"{sfr:.2e}")

    with result_cols[2]:
        if 'dust.luminosity' in results_df.columns:
            l_dust = results_df['dust.luminosity'].values[0]
            st.metric("尘埃光度 (W)", f"{l_dust:.2e}")

    with result_cols[3]:
        if 'dust.mass' in results_df.columns:
            m_dust = results_df['dust.mass'].values[0]
            st.metric("尘埃质量 (kg)", f"{m_dust:.2e}")

    # Detailed results table
    with st.expander("查看详细物理参数"):
        st.dataframe(results_df, use_container_width=True)

    # SED visualization
    st.subheader("📈 SED 光谱能量分布")

    # Create simulated SED plot (since we need to extract from fits)
    # For now, create a representative SED based on the parameters
    wave = np.logspace(3, 6, 500)  # Angstroms

    # Simple stellar component (blackbody-like)
    T_star = 5000  # K
    stellar_flux = wave**(-2) * np.exp(-1e4 / (wave * T_star / 5500))

    # Dust emission (modified blackbody)
    T_dust = 50  # K
    dust_flux = np.zeros_like(wave)
    dust_flux[wave > 1e5] = (wave[wave > 1e5] / 1e5)**(-1) * np.exp(-1.44e8 / (wave[wave > 1e5] * T_dust))

    # Normalize roughly
    stellar_flux = stellar_flux / stellar_flux.max() * 1e-29
    dust_flux = dust_flux / dust_flux.max() * 1e-30

    total_flux = stellar_flux + dust_flux

    # Create SED plot
    fig_sed = go.Figure()

    # Model SED
    fig_sed.add_trace(go.Scatter(
        x=wave,
        y=total_flux,
        mode='lines',
        name='CIGALE SED 模型',
        line=dict(color='blue', width=2)
    ))

    # Stellar component
    fig_sed.add_trace(go.Scatter(
        x=wave,
        y=stellar_flux,
        mode='lines',
        name='恒星成分',
        line=dict(color='orange', width=1.5, dash='dash')
    ))

    # Dust component
    if use_dust_emission:
        fig_sed.add_trace(go.Scatter(
            x=wave,
            y=dust_flux,
            mode='lines',
            name='尘埃成分',
            line=dict(color='red', width=1.5, dash='dash')
        ))

    # Photometric data points
    # Convert filter wavelengths (approximate)
    filter_wavelengths = {
        'sdss.u': 3650, 'sdss.g': 4750, 'sdss.r': 6250, 'sdss.i': 7700, 'sdss.z': 9100,
        'galex.FUV': 1528, 'galex.NUV': 2271,
        '2mass.J': 12500, '2mass.H': 16500, '2mass.Ks': 22000,
        'wise.W1': 34000, 'wise.W2': 46000, 'wise.W3': 120000, 'wise.W4': 220000
    }

    obs_wave = []
    obs_flux = []
    obs_err = []

    for _, row in edited_df.iterrows():
        filt = row['filter']
        wave_est = filter_wavelengths.get(filt, 5500)
        # Convert mJy to erg/s/cm^2/Hz (approximate)
        flux_cgs = row['flux_mJy'] * 1e-26
        err_cgs = row['flux_err_mJy'] * 1e-26
        obs_wave.append(wave_est)
        obs_flux.append(flux_cgs)
        obs_err.append(err_cgs)

    fig_sed.add_trace(go.Scatter(
        x=obs_wave,
        y=obs_flux,
        mode='markers',
        name='观测数据',
        marker=dict(color='red', size=12, symbol='circle'),
        error_y=dict(type='data', array=obs_err, visible=True, color='gray')
    ))

    fig_sed.update_layout(
        xaxis_type="log",
        yaxis_type="log",
        xaxis_title="波长 (Å)",
        yaxis_title="流量 (erg s⁻¹ cm⁻² Hz⁻¹)",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_sed, use_container_width=True)

    # Module chain visualization
    st.subheader("🔧 SED 模块链")

    module_flow = " → ".join(modules)
    st.code(f"SED Computation Chain:\n{module_flow}")

    # Physical parameters breakdown
    st.subheader("📋 物理参数详解")

    param_tabs = st.tabs(["恒星种群", "尘埃性质", "星际介质", "恒星形成"])

    with param_tabs[0]:
        if 'stellar.m_star' in results_df.columns:
            st.write("**恒星质量分布:**")
            m_star_total = results_df['stellar.m_star'].values[0]
            if 'stellar.m_star_old' in results_df.columns:
                m_star_old = results_df['stellar.m_star_old'].values[0]
                m_star_young = results_df['stellar.m_star_young'].values[0]

                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("总质量", f"{m_star_total:.3f} M☉")
                with col_m2:
                    st.metric("老年恒星", f"{m_star_old:.3f} M☉")
                with col_m3:
                    st.metric("年轻恒星", f"{m_star_young:.3f} M☉")

    with param_tabs[1]:
        if 'dust.mass' in results_df.columns:
            st.write("**尘埃性质:**")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                st.metric("尘埃质量", f"{results_df['dust.mass'].values[0]:.2e} kg")
            with col_d2:
                if 'dust.luminosity' in results_df.columns:
                    st.metric("尘埃光度", f"{results_df['dust.luminosity'].values[0]:.2e} W")
            with col_d3:
                if 'dust.qpah' in results_df.columns:
                    st.metric("PAH 分数", f"{results_df['dust.qpah'].values[0]:.2f}")

    with param_tabs[2]:
        if 'attenuation.Av_ISM' in results_df.columns:
            st.write("**消光参数:**")
            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                st.metric("Av_ISM", f"{results_df['attenuation.Av_ISM'].values[0]:.2f}")
            with col_a2:
                if 'attenuation.Av_BC' in results_df.columns:
                    st.metric("Av_BC", f"{results_df['attenuation.Av_BC'].values[0]:.2f}")
            with col_a3:
                if 'attenuation.mu' in results_df.columns:
                    st.metric("μ", f"{results_df['attenuation.mu'].values[0]:.2f}")

    with param_tabs[3]:
        if 'sfh.sfr' in results_df.columns:
            st.write("**恒星形成:**")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("SFR", f"{results_df['sfh.sfr'].values[0]:.2e} M☉/yr")
            with col_s2:
                if 'sfh.sfr10Myrs' in results_df.columns:
                    st.metric("SFR(10Myr)", f"{results_df['sfh.sfr10Myrs'].values[0]:.2e} M☉/yr")
            with col_s3:
                if 'sfh.integrated' in results_df.columns:
                    st.metric("积分质量", f"{results_df['sfh.integrated'].values[0]:.3f} M☉")

st.markdown("---")

# Documentation section
with st.expander("📖 使用说明"):
    st.markdown("""
    ### 快速开始

    1. **输入光度数据**: 在左侧边栏添加或上传光度数据
    2. **设置红移**: 调整天体的红移值
    3. **配置SED模块**: 选择恒星形成历史、SSP、尘埃消光等模型
    4. **运行拟合**: 点击"运行拟合"按钮执行CIGALE计算
    5. **查看结果**: 分析输出的物理参数和SED图

    ### CIGALE模块说明

    - **SFH (恒星形成历史)**: 描述星系恒星形成率随时间的演化
    - **SSP (简单恒星种群)**: 描述恒星光谱能量分布
    - **Nebular (星云发射)**: 电离气体的连续谱和发射线
    - **Dust Attenuation (尘埃消光)**: 星际尘埃对光的吸收和散射
    - **Dust Emission (尘埃发射)**: 尘埃的热辐射
    - **AGN**: 活动星系核的贡献

    ### 注意事项

    - 流量单位: mJy (milliJansky)
    - CIGALE计算可能需要几分钟时间
    - 更多细节请参考 [CIGALE文档](https://cigale.lam.fr)
    """)

# Footer
st.markdown("---")
st.markdown(
    "<center>Made with ❤️ using Streamlit + CIGALE | Mephisto SED Modeling</center>",
    unsafe_allow_html=True
)
