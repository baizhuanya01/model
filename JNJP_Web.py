import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("磷锂电池大规模应用的经济性分析！")

st.markdown("""
<style>
[data-testid="stMetricDelta"]:has(svg[class*="down"]) {
    color: orange !important;
}
[data-testid="stMetricDelta"] [class*="negative"] {
    color: orange !important;
}
</style>
""", unsafe_allow_html=True)

#参数表(所有参数格式为前几字首字母缩写加最后两字全拼,除了那个其他是other)
canshu = {
    "技术参数": {
        "额定功率 (MW)": {
            "type": "number",
            "var": "edgonglv",
            "default": 10.0,
            "step": 1.0,
            "help": "储能系统的额定输出功率"
        },
        "额定容量 (MWh)": {
            "type": "number",
            "var": "edrongliang",
            "default": 20.0,
            "step": 1.0,
            "help": "储能系统的总能量容量"
        },
        "系统效率 (%)": {
            "type": "slider",
            "var": "xtxiaolv",
            "min": 80,
            "max": 95,
            "default": 90,
            "help": "充放电循环的综合效率",
            "convert": lambda x: x / 100
        },
        "年循环次数": {
            "type": "number",
            "var": "nxhcishu",
            "default": 300,
            "step": 10,
            "min": 200,
            "max": 365,
            "help": "每年完成的充放电循环次数"
        },
        "充放电深度 (%)": {
            "type": "slider",
            "var": "cfdshendu",
            "min": 80,
            "max": 100,
            "default": 90,
            "help": "每次循环使用的电池容量百分比",
            "convert": lambda x: x / 100
        },
        "首年衰减率 (%)": {
            "type": "slider",
            "var": "snsjianlv",
            "min": 1,
            "max": 5,
            "default": 3,
            "help": "第一年的容量衰减",
            "convert": lambda x: x / 100
        },
        "线性衰减率 (%/年)": {
            "type": "slider",
            "var": "xxsjianlv",
            "min": 0.5,
            "max": 2.0,
            "default": 0.8,
            "step": 0.1,
            "help": "第二年起每年的容量衰减",
            "convert": lambda x: x / 100
        }
    },
    
    "成本参数": {
        "电池系统单价 (元/Wh)": {
            "type": "number",
            "var": "dcxtdanjia",
            "default": 0.9,
            "step": 0.1,
            "format": "%.2f",
            "help": "锂电池储能系统单位价格"
        },
        "PCS单价 (元/Wh)": {
            "type": "number",
            "var": "pcsdanjia",
            "default": 0.3,
            "step": 0.05,
            "format": "%.2f",
            "help": "储能变流器单价"
        },
        "BMS+EMS单价 (元/Wh)": {
            "type": "number",
            "var": "bmsemsdanjia",
            "default": 0.1,
            "step": 0.01,
            "format": "%.2f",
            "help": "电池管理系统+能量管理系统"
        },
        "升压变及电气单价 (元/W)": {
            "type": "number",
            "var": "sybjdqdanjia",
            "default": 0.2,
            "step": 0.05,
            "format": "%.2f",
            "help": "升压变及电气设备单价"
        },
        "土建工程费单价 (元/Wh)": {
            "type": "number",
            "var": "tjgcfdanjia",
            "default": 0.15,
            "step": 0.01,
            "format": "%.2f",
            "help": "土建工程单位成本"
        },
        "安装调试费比例 (%)": {
            "type": "slider",
            "var": "aztsfbili",
            "min": 1,
            "max": 10,
            "default": 5,
            "help": "安装调试费占设备费的比例",
            "convert": lambda x: x / 100
        },
        "建设用地费 (万元)": {
            "type": "number",
            "var": "jsydifei",
            "default": 50.0,
            "step": 10.0,
            "help": "土地使用费用"
        },
        "接入系统费 (万元)": {
            "type": "number",
            "var": "jrxtongfei",
            "default": 100.0,
            "step": 10.0,
            "help": "电网接入费用"
        },
        "前期开发管理费 (万元)": {
            "type": "number",
            "var": "qxkfglifei",
            "default": 50.0,
            "step": 10.0,
            "help": "项目前期开发管理费用"
        },
        "预备费率 (%)": {
            "type": "slider",
            "var": "ybfeilv",
            "min": 3,
            "max": 10,
            "default": 5,
            "help": "预备费比例",
            "convert": lambda x: x / 100
        }
    },
    
    "收益参数": {
        "放电电价 (元/kWh)": {
            "type": "number",
            "var": "fddianjia",
            "default": 1.0,
            "step": 0.1,
            "format": "%.2f",
            "help": "峰时售电价格"
        },
        "充电电价 (元/kWh)": {
            "type": "number",
            "var": "cddianjia",
            "default": 0.3,
            "step": 0.05,
            "format": "%.2f",
            "help": "谷时购电价格"
        },
        "补贴收入 (万元/年)": {
            "type": "number",
            "var": "btshouru",
            "default": 0.0,
            "step": 10.0,
            "help": "政府或电网的年度补贴"
        }
    },
    
    "财务参数": {
        "电池系统折旧年限 (年)": {
            "type": "number",
            "var": "dcxtzjnianxian",
            "default": 10,
            "step": 1,
            "min": 5,
            "max": 20,
            "help": "电池系统折旧年限"
        },
        "PCS折旧年限 (年)": {
            "type": "number",
            "var": "pcszjnianxian",
            "default": 15,
            "step": 1,
            "min": 10,
            "max": 20,
            "help": "PCS折旧年限"
        },
        "土建折旧年限 (年)": {
            "type": "number",
            "var": "tjzjnianxian",
            "default": 20,
            "step": 1,
            "min": 15,
            "max": 30,
            "help": "土建工程折旧年限"
        },
        "残值率 (%)": {
            "type": "slider",
            "var": "czhilv",
            "min": 0,
            "max": 10,
            "default": 5,
            "help": "资产残值率",
            "convert": lambda x: x / 100
        },
        "维修费率 (%)": {
            "type": "slider",
            "var": "wxfeilv",
            "min": 0.5,
            "max": 3.0,
            "default": 1.5,
            "step": 0.1,
            "help": "年维修费占静态投资的比例",
            "convert": lambda x: x / 100
        },
        "保险费率 (%)": {
            "type": "slider",
            "var": "bxfeilv",
            "min": 0.1,
            "max": 1.0,
            "default": 0.3,
            "step": 0.1,
            "help": "年保险费占静态投资的比例",
            "convert": lambda x: x / 100
        },
        "材料费单位成本 (元/kWh)": {
            "type": "number",
            "var": "clfdwchenben",
            "default": 0.01,
            "step": 0.001,
            "format": "%.3f",
            "help": "运维材料费单位成本"
        },
        "人员数量 (人)": {
            "type": "number",
            "var": "ryshuliang",
            "default": 5,
            "step": 1,
            "min": 1,
            "help": "运维人员数量"
        },
        "人均年工资 (万元/人)": {
            "type": "number",
            "var": "rjngongzi",
            "default": 10.0,
            "step": 1.0,
            "help": "每人年工资"
        },
        "福利费占工资比例 (%)": {
            "type": "slider",
            "var": "flfzgzbili",
            "min": 10,
            "max": 30,
            "default": 14,
            "help": "福利费比例",
            "convert": lambda x: x / 100
        },
        "其他费用年固定值 (万元/年)": {
            "type": "number",
            "var": "other",
            "default": 10.0,
            "step": 1.0,
            "help": "其他年度固定费用"
        },
        "电池更换年份 (年)": {
            "type": "number",
            "var": "dcghnianxian",
            "default": 0,
            "step": 1,
            "min": 0,
            "max": 20,
            "help": "电池更换年份（0表示不更换）"
        },
        "电池更换比例 (%)": {
            "type": "slider",
            "var": "dcghbili",
            "min": 0,
            "max": 100,
            "default": 0,
            "help": "电池更换容量占比",
            "convert": lambda x: x / 100
        },
        "电池更换单价 (元/Wh)": {
            "type": "number",
            "var": "dcghdanjia",
            "default": 0.8,
            "step": 0.1,
            "format": "%.2f",
            "help": "更换电池的单位价格"
        },
        "无形资产摊销年限 (年)": {
            "type": "number",
            "var": "wxzctxnianxian",
            "default": 10,
            "step": 1,
            "min": 5,
            "max": 20,
            "help": "无形资产（前期开发费）摊销年限"
        },
        "盈余公积金提取比例 (%)": {
            "type": "slider",
            "var": "yygjjtqbili",
            "min": 5,
            "max": 15,
            "default": 10,
            "help": "从净利润中提取盈余公积金的比例",
            "convert": lambda x: x / 100
        }
    },
    
    "税务与贷款": {
        "贷款比例 (%)": {
            "type": "slider",
            "var": "dkbili",
            "min": 0,
            "max": 80,
            "default": 70,
            "help": "贷款占总投资的比例",
            "convert": lambda x: x / 100
        },
        "贷款利率 (%)": {
            "type": "slider",
            "var": "dklilv",
            "min": 3.0,
            "max": 8.0,
            "default": 4.9,
            "step": 0.1,
            "help": "年贷款利率",
            "convert": lambda x: x / 100
        },
        "贷款年限 (年)": {
            "type": "number",
            "var": "dknianxian",
            "default": 10,
            "step": 1,
            "min": 5,
            "max": 20,
            "help": "贷款期限"
        },
        "城建税率 (%)": {
            "type": "slider",
            "var": "cjshuilv",
            "min": 5,
            "max": 7,
            "default": 7,
            "help": "城市维护建设税率",
            "convert": lambda x: x / 100
        },
        "教育附加率 (%)": {
            "type": "slider",
            "var": "jyfjialv",
            "min": 3,
            "max": 5,
            "default": 3,
            "help": "教育费附加率",
            "convert": lambda x: x / 100
        },
        "地方教育附加率 (%)": {
            "type": "slider",
            "var": "dfjyfjialv",
            "min": 1,
            "max": 2,
            "default": 2,
            "help": "地方教育附加率",
            "convert": lambda x: x / 100
        },
        "所得税率 (%)": {
            "type": "slider",
            "var": "sdshuilv",
            "min": 15,
            "max": 25,
            "default": 25,
            "help": "企业所得税率",
            "convert": lambda x: x / 100
        },
        "所得税减免年数 (年)": {
            "type": "number",
            "var": "sdsjmnianxian",
            "default": 0,
            "step": 1,
            "min": 0,
            "max": 5,
            "help": "所得税全免年数"
        },
        "所得税减半年数 (年)": {
            "type": "number",
            "var": "sdsjbnianxian",
            "default": 0,
            "step": 1,
            "min": 0,
            "max": 5,
            "help": "所得税减半年数"
        },
        "流动资金比例 (%)": {
            "type": "slider",
            "var": "ldzjbili",
            "min": 1,
            "max": 20,
            "default": 5,
            "help": "流动资金占营业收入的比例",
            "convert": lambda x: x / 100
        },
        "增值税率 (%)": {
            "type": "slider",
            "var": "zzshuilv",
            "min": 0,
            "max": 13,
            "default": 13,
            "help": "增值税税率",
            "convert": lambda x: x / 100
        },
        "进项税抵扣方式": {
            "type": "number",
            "var": "jxsdkfangshi",
            "default": 1,
            "step": 1,
            "min": 0,
            "max": 1,
            "help": "1=可抵扣，0=不抵扣"
        },
        "流动资产周转次数 (次/年)": {
            "type": "number",
            "var": "ldzczzcishu",
            "default": 4,
            "step": 1,
            "min": 1,
            "help": "流动资产年周转次数"
        },
        "应付账款周转次数 (次/年)": {
            "type": "number",
            "var": "yfzkzzcishu",
            "default": 4,
            "step": 1,
            "min": 1,
            "help": "应付账款年周转次数"
        }
    }
}

# 通用参数渲染函数
def render_param(param_name, config):
    """根据配置渲染参数输入控件"""
    if config["type"] == "number":
        # 根据默认值类型自动确定format
        default_value = config["default"]
        if "format" in config:
            format_str = config["format"]
        elif isinstance(default_value, int):
            format_str = "%d"  # 整数格式
        else:
            format_str = "%f"  # 浮点数格式
        
        value = st.number_input(
            label=param_name,
            value=default_value,
            step=config.get("step", 1.0),
            min_value=config.get("min"),
            max_value=config.get("max"),
            format=format_str,
            help=config["help"]
        )
    elif config["type"] == "slider":
        value = st.slider(
            label=param_name,
            min_value=config["min"],
            max_value=config["max"],
            value=config["default"],
            step=config.get("step"),
            help=config["help"]
        )
    else:
        value = config["default"]
    
    # 应用转换函数
    if "convert" in config and config["convert"]:
        value = config["convert"](value)

    return value

with st.sidebar:
    params = {}
    icons = {
    "技术参数": "⚡",
    "成本参数": "💰",
    "收益参数": "📈",
    "财务参数": "🏦",
    "税务与贷款": "💼"
    }
    for group_name, group_params in canshu.items():
        icon = icons.get(group_name,"📋")
        with st.expander(label=f"{icon}{group_name}",expanded=True):
            param_names = list(group_params.keys())
            selected = st.multiselect("选择参数",options=param_names,default=None,help="选择你需要的参数，可多选。")
            for param_name, config in group_params.items():
                if param_name in selected:
                    value = render_param(param_name, config)
                else:
                    value = config["default"]
                    if "convert" in config:
                        value = config["convert"](value)
                params[config["var"]] = value

locals().update(params)

#计算逻辑

# ── 1. 投资估算 ──────────────────────────────────────────────

# 单位换算
rlhuansuan = edrongliang * 1e6   # 容量换算 MWh → Wh
glhuansuan = edgonglv   * 1e6   # 功率换算 MW  → W

# 1.1 设备费用（万元）
dcxtchenben  = rlhuansuan * dcxtdanjia   / 1e4   # 电池系统
pcschenben   = rlhuansuan * pcsdanjia    / 1e4   # PCS
bmsemschenben= rlhuansuan * bmsemsdanjia / 1e4   # BMS+EMS
sybjdqchenben= glhuansuan * sybjdqdanjia / 1e4   # 升压变及电气
aztsfchenben = (dcxtchenben + pcschenben + bmsemschenben + sybjdqchenben) * aztsfbili  # 安装调试费
sbheji       = dcxtchenben + pcschenben + bmsemschenben + sybjdqchenben + aztsfchenben  # 设备及安装小计

# 1.2 建筑工程费（万元）
tjgcfchenben = rlhuansuan * tjgcfdanjia / 1e4

# 1.3 其他费用（万元）
qtxiaoji = jsydifei + jrxtongfei + qxkfglifei          # 建设用地+接入+前期开发
ybfei    = (sbheji + tjgcfchenben + qtxiaoji) * ybfeilv  # 预备费
qtheji   = qtxiaoji + ybfei

# 1.4 可抵扣增值税（若进项税抵扣方式=1）
kdkzzs = sbheji * zzshuilv if jxsdkfangshi == 1 else 0

# 1.5 静态投资 / 动态投资（万元）
jttouzi  = sbheji + tjgcfchenben + qtheji
jsqlxi   = jttouzi * dkbili * dklilv * 0.5   # 建设期利息（建设期1年，均匀放款）
dttouzi  = jttouzi + jsqlxi

# 1.6 固定资产 / 无形资产原值（万元，不含税）
wxzcyuanzhi  = qxkfglifei                                          # 无形资产 = 前期开发管理费
gdzcyuanzhi  = jttouzi - kdkzzs - jsydifei - wxzcyuanzhi           # 固定资产原值（不含税）

# 1.7 单位kWh静态投资（元/kWh）
dwtouzi = jttouzi * 1e4 / (edrongliang * 1e3)

# ── 2. 20年运营数据 ──────────────────────────────────────────

years = list(range(1, 21))   # [1, 2, ..., 20]

# 2.1 年放电量 / 充电量（MWh）
fddianliang = []   # 放电量
cddianliang = []   # 充电量
for year in years:
    if year == 1:
        # 第1年：额定容量 × 循环次数 × 充放电深度 × (1 - 首年衰减率)
        fd = edrongliang * nxhcishu * cfdshendu * (1 - snsjianlv)
    else:
        # 第2年起：上一年放电量 × (1 - 线性衰减率)
        fd = fddianliang[year - 2] * (1 - xxsjianlv)
    fddianliang.append(fd)
    cddianliang.append(fd / xtxiaolv)   # 充电量 = 放电量 / 系统效率

# 2.2 营业收入（万元）
yyshouru = [fd * 1000 * fddianjia / 1e4 for fd in fddianliang]

# 2.3 充电购电成本（万元）
cdgdchenben = [cd * 1000 * cddianjia / 1e4 for cd in cddianliang]

# ── 3. 折旧 & 摊销 ───────────────────────────────────────────

# 3.1 各资产年折旧（直线法，考虑残值率）
dcxtnzheju = dcxtchenben  * (1 - czhilv) / dcxtzjnianxian   # 电池系统年折旧
pcsnzheju  = pcschenben   * (1 - czhilv) / pcszjnianxian    # PCS年折旧
tjnzheju   = tjgcfchenben * (1 - czhilv) / tjzjnianxian     # 土建年折旧

zjfei = []
for year in years:
    zj = 0
    if year <= dcxtzjnianxian: zj += dcxtnzheju
    if year <= pcszjnianxian:  zj += pcsnzheju
    if year <= tjzjnianxian:   zj += tjnzheju
    zjfei.append(zj)

# 3.2 无形资产摊销（万元/年）
txfei = [wxzcyuanzhi / wxzctxnianxian if year <= wxzctxnianxian else 0 for year in years]

# ── 4. 运维费用 ──────────────────────────────────────────────

wxfei  = [jttouzi * wxfeilv]  * 20   # 维修费
bxfei  = [jttouzi * bxfeilv]  * 20   # 保险费
rgfei  = [ryshuliang * rjngongzi * (1 + flfzgzbili)] * 20  # 人工+福利
clfei  = [fd * 1000 * clfdwchenben / 1e4 for fd in fddianliang]  # 材料费
qtafei = [other] * 20   # 其他固定费用

# 电池更换（一次性，发生在指定年份）
dcghfei = []
for year in years:
    if year == dcghnianxian and dcghnianxian > 0:
        dcghfei.append(rlhuansuan * dcghbili * dcghdanjia / 1e4)
    else:
        dcghfei.append(0)

# ── 5. 贷款还本付息（等额本息 PMT）────────────────────────────

dkjine   = dttouzi * dkbili          # 贷款金额
zyzijin  = dttouzi * (1 - dkbili)    # 自有资金

# 年还款额（PMT公式）
if dknianxian > 0 and dklilv > 0:
    nhkuane = dkjine * (dklilv * (1 + dklilv) ** dknianxian) / ((1 + dklilv) ** dknianxian - 1)
else:
    nhkuane = 0

lxzhichu = []   # 利息支出
huanben  = []   # 还本
hkheji   = []   # 还本付息合计
ncyue    = []   # 年初借款余额
nmyue    = []   # 年末借款余额

yue = dkjine
for year in years:
    ncyue.append(yue)
    if year <= dknianxian and yue > 0:
        lixi = yue * dklilv
        ben  = nhkuane - lixi
        yue  = max(0, yue - ben)
    else:
        lixi, ben = 0, 0
    lxzhichu.append(lixi)
    huanben.append(ben)
    hkheji.append(lixi + ben)
    nmyue.append(yue)

# ── 6. 增值税 & 税金及附加 ────────────────────────────────────

# 增值税（销项 - 进项）
xxzzshui = [yy * zzshuilv for yy in yyshouru]
jxzzshui = [cd * zzshuilv for cd in cdgdchenben]
yjzzshui = [max(0, x - j) for x, j in zip(xxzzshui, jxzzshui)]

# 税金及附加 = 增值税 × (城建税率 + 教育附加率 + 地方教育附加率)
sjfujia = [zzs * (cjshuilv + jyfjialv + dfjyfjialv) for zzs in yjzzshui]

# ── 7. 总成本费用 ─────────────────────────────────────────────

zchenben  = []   # 总成本
jychenben = []   # 经营成本（不含折旧摊销利息）
for i in range(20):
    zc = (cdgdchenben[i] + dcghfei[i] + zjfei[i] + txfei[i] +
          wxfei[i] + rgfei[i] + bxfei[i] +
          clfei[i] + qtafei[i] + lxzhichu[i])
    zchenben.append(zc)
    jc = (cdgdchenben[i] + dcghfei[i] + wxfei[i] +
          rgfei[i] + bxfei[i] + clfei[i] + qtafei[i])
    jychenben.append(jc)

# ── 8. 利润及分配 ─────────────────────────────────────────────

# 利润总额
lrzonge = [yyshouru[i] + btshouru - zchenben[i] - sjfujia[i] for i in range(20)]

# 弥补以前年度亏损
mbkuisun = []
leiji_ks = 0
for lz in lrzonge:
    if leiji_ks > 0 and lz > 0:
        mibu = min(leiji_ks, lz)
        leiji_ks -= mibu
    elif lz < 0:
        mibu = 0
        leiji_ks += abs(lz)
    else:
        mibu = 0
    mbkuisun.append(mibu)

# 应纳税所得额
ynsuode = [lrzonge[i] - mbkuisun[i] for i in range(20)]

# 所得税（考虑减免年数）
sdshui = []
for i, year in enumerate(years):
    if ynsuode[i] <= 0:
        sdshui.append(0)
    elif year <= sdsjmnianxian:
        sdshui.append(0)                                   # 全免
    elif year <= sdsjmnianxian + sdsjbnianxian:
        sdshui.append(ynsuode[i] * sdshuilv * 0.5)        # 减半
    else:
        sdshui.append(ynsuode[i] * sdshuilv)              # 正常

# 净利润
jlirun = [lrzonge[i] - sdshui[i] for i in range(20)]

# 盈余公积金 & 未分配利润
yygjjin  = [max(0, jl * yygjjtqbili) for jl in jlirun]
wflirun  = [jlirun[i] - yygjjin[i] for i in range(20)]

# ── 9. 现金流 ─────────────────────────────────────────────────

# 流动资金（营业收入 × 流动资金比例，第1年投入，第20年回收）
ldzijin = yyshouru[0] * ldzjbili

# 年度现金流（净利润 + 折旧 + 摊销 - 还本）
xjliu = []
for i, year in enumerate(years):
    cf = jlirun[i] + zjfei[i] + txfei[i] - huanben[i]
    if year == 20:
        cf += ldzijin   # 第20年回收流动资金
    xjliu.append(cf)

# 累计现金流（第0年投入自有资金 + 流动资金）
ljxjliu = [-(zyzijin + ldzijin)]
for cf in xjliu:
    ljxjliu.append(ljxjliu[-1] + cf)

# ── 10. 财务指标 ──────────────────────────────────────────────

zxlv = 0.08   # 折现率 8%

# NPV（净现值）
npv = ljxjliu[0]
for i, cf in enumerate(xjliu):
    npv += cf / (1 + zxlv) ** (i + 1)

# IRR（二分法）
def calc_npv(rate):
    v = ljxjliu[0]
    for i, cf in enumerate(xjliu):
        v += cf / (1 + rate) ** (i + 1)
    return v

irr = None
lo, hi = 0.0, 1.0
for _ in range(200):
    mid = (lo + hi) / 2
    if abs(calc_npv(mid)) < 0.01:
        irr = mid; break
    elif calc_npv(mid) > 0: lo = mid
    else: hi = mid

# 静态回收期
jthshouqi = None
for i, v in enumerate(ljxjliu[1:], 1):
    if v >= 0:
        jthshouqi = i; break

# 动态回收期
dt_xjliu = [ljxjliu[0]]
for i, cf in enumerate(xjliu):
    dt_xjliu.append(dt_xjliu[-1] + cf / (1 + zxlv) ** (i + 1))

dthshouqi = None
for i, v in enumerate(dt_xjliu[1:], 1):
    if v >= 0:
        dthshouqi = i; break

# LCOE（度电成本，元/kWh）
lcoe_fenzi = sum(zchenben[i] / (1 + zxlv) ** (i + 1) for i in range(20))
lcoe_fenmu = sum(fddianliang[i] * 1000 / (1 + zxlv) ** (i + 1) for i in range(20))
lcoe = lcoe_fenzi * 1e4 / lcoe_fenmu if lcoe_fenmu > 0 else 0   # 元/kWh

# 总投资收益率 / 资本金净利润率
njlirun  = sum(lrzonge) / 20
njjlirun = sum(jlirun)  / 20
ztzsyilv = njlirun  / dttouzi if dttouzi > 0 else 0
zbjjlrunlv = njjlirun / zyzijin if zyzijin > 0 else 0

tab1,tab2,tab3,tab4,tab5 = st.tabs(["主展板","web2","web3","web4","web5"])

with tab1:
    # 第一排：投资规模
    st.subheader("投资规模")
    z1, m1, y1 = st.columns(3)
    z1.metric("动态投资", f"{dttouzi:.0f} 万元")
    m1.metric("静态投资", f"{jttouzi:.0f} 万元")
    y1.metric("自有资金", f"{zyzijin:.0f} 万元")

    st.divider()

    # 第二排：核心收益指标
    st.subheader("核心收益")
    z2, m2, y2 = st.columns(3)
    z2.metric("NPV（净现值）", f"{npv:.0f} 万元",
              delta="项目可行 ✓" if npv > 0 else "-项目不可行 ✗")
    m2.metric("IRR（内部收益率）", f"{irr*100:.2f}%" if irr else "N/A",
              delta="高于基准 ✓" if irr and irr > 0.08 else "-低于基准 ✗")
    y2.metric("静态回收期", f"{jthshouqi} 年" if jthshouqi else ">20年",
              delta="回收较快 ✓" if jthshouqi and jthshouqi <= 10 else "-回收较慢 ✗")

    st.divider()

    # 第三排：效率指标
    st.subheader("效率指标")
    z3, m3, y3 = st.columns(3)
    z3.metric("度电成本 LCOE", f"{lcoe:.4f} 元/kWh",
              delta="低于电价 ✓" if lcoe < fddianjia else "-高于电价 ✗")
    m3.metric("总投资收益率 ROI", f"{ztzsyilv*100:.2f}%",
              delta="达标 ✓" if ztzsyilv > 0.08 else "-未达标 ✗")
    y3.metric("资本金净利润率 ROE", f"{zbjjlrunlv*100:.2f}%",
              delta="达标 ✓" if zbjjlrunlv > 0.10 else "-未达标 ✗")
        
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=list(range(0, 21)), y=ljxjliu, name="累计现金流", fill="tozeroy"))
    fig2 = go.Figure()
    fig2.add_trace(go.Pie(
        labels=["充电成本", "电池更换", "折旧费", "摊销费",
                "维修费", "人工费", "保险费", "材料费", "其他", "利息"],
        values=[sum(cdgdchenben), sum(dcghfei), sum(zjfei), sum(txfei),
                sum(wxfei), sum(rgfei), sum(bxfei), sum(clfei), sum(qtafei), sum(lxzhichu)]
    ))
    st.header("累计现金流图")
    st.plotly_chart(fig1, use_container_width=True, key="ljxjinliu")
    st.header("成本构成图")
    st.plotly_chart(fig2, use_container_width=True, key="chenbengouchen")

