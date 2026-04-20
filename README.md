# Mephisto SED Modeling - Streamlit App with CIGALE

基于 [CIGALE](https://cigale.lam.fr) 的 SED (Spectral Energy Distribution) 拟合可视化界面。

## 功能特点

- 📊 **交互式光度数据输入** - 支持手动输入、CSV上传和示例数据
- 🔧 **完整的 CIGALE 模块配置** - SFH, SSP, Dust Attenuation, Dust Emission, AGN等
- 📈 **实时 SED 光谱图** - 可视化模型 SED 和观测数据
- 🤖 **Agent 决策历史展示** - 记录拟合过程中的关键决策
- ⚡ **本地 CIGALE 集成** - 直接调用 pcigale 进行真实计算

## 在线访问

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_APP_URL_HERE)

## 本地运行

### 前提条件

1. 安装 CIGALE (pcigale):
```bash
# 下载 CIGALE 源码
cd ~/Documents
git clone https://gitlab.lam.fr/cigale/cigale.git cigale-v2025.0
cd cigale-v2025.0

# 安装依赖
pip install numpy==1.26.4 scipy matplotlib astropy configobj

# 安装 CIGALE
python setup.py build
pip install -e .
```

2. 确保 NumPy 版本兼容 (1.26.x 推荐):
```bash
pip install "numpy>=1.24.0,<2.0"
```

### 安装和运行

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/mephisto-streamlit.git
cd mephisto-streamlit

# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run mephisto_app.py
```

应用将在 http://localhost:8501 启动。

## 使用指南

### 快速开始

1. **输入光度数据**: 在左侧边栏添加滤光片和流量数据
2. **设置天体参数**: 输入红移和天体ID
3. **配置SED模型**: 选择恒星形成历史、SSP、尘埃模型等
4. **运行拟合**: 点击"运行拟合"按钮
5. **分析结果**: 查看物理参数、SED图和详细输出

### 支持的滤光片

- SDSS (u, g, r, i, z)
- GALEX (FUV, NUV)
- 2MASS (J, H, Ks)
- WISE (W1, W2, W3, W4)
- HST/ACS
- JWST/NIRCAM
- 以及更多...

### CIGALE 模块

| 类别 | 可用模块 |
|------|----------|
| SFH | sfh2exp, sfhdelayed, sfhdelayedbq, sfhfromfile, sfhperiodic |
| SSP | bc03, cb19, bpassv2, m2005 |
| Nebular | nebular |
| Dust Attenuation | dustatt_modified_CF00, dustatt_modified_starburst |
| Dust Emission | casey2012, dale2014, dl2007, dl2014, themis |
| AGN | fritz2006, skirtor2016 |

## 项目结构

```
mephisto-streamlit/
├── mephisto_app.py        # 主应用文件
├── cigale_interface.py    # CIGALE 接口封装
├── requirements.txt       # Python 依赖
├── README.md             # 项目说明
└── deploy.sh             # 部署脚本
```

## 部署到 Streamlit Cloud

1. 将代码推送到 GitHub:
```bash
./deploy.sh YOUR_GITHUB_USERNAME
```

2. 访问 [Streamlit Cloud](https://streamlit.io/cloud) 并登录

3. 创建新应用，选择 `mephisto-streamlit` 仓库

4. 点击 Deploy

## 注意事项

- CIGALE 计算可能需要几分钟，取决于模型复杂度
- 确保服务器/本地环境已正确安装 CIGALE
- NumPy 2.0+ 可能与 CIGALE 2025.0 不兼容，建议使用 NumPy 1.26.x

## 相关链接

- CIGALE 官网: https://cigale.lam.fr
- CIGALE 文档: https://cigale.lam.fr/doc/
- Streamlit 文档: https://docs.streamlit.io

## 许可证

MIT License

---

Made with ❤️ using Streamlit + CIGALE
