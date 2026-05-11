import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")

st.title("磷酸铁锂储能电站多维动态技术经济评估与智能决策支持系统")

st.markdown("""
    <style>
    /* 引入等线字体 - 常规体 */
    @font-face {
        font-family: 'DengXian';
        src: url('./app/static/fonts/等线.ttf') format('truetype');
        font-weight: normal;
        font-style: normal;
    }

    /* 引入等线字体 - Light 体 */
    @font-face {
        font-family: 'DengXian';
        src: url('./app/static/fonts/等线 Light.ttf') format('truetype');
        font-weight: 300;
        font-style: normal;
    }

    /* 全局应用等线字体 */
    * {
        font-family: 'DengXian', '等线', sans-serif !important;
    }

    /* Delta 负值显示橙色 */
    [data-testid="stMetricDelta"]:has(svg[class*="down"]) {
        color: orange !important;
    }
    [data-testid="stMetricDelta"] [class*="negative"] {
        color: orange !important;
    }

    /* 缩小 metric 组件字体，减少视觉空间 */
    [data-testid="stMetric"] {
        padding: 2px 6px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        margin-bottom: 0 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.05rem !important;
        line-height: 1.2 !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.70rem !important;
        margin-top: 0 !important;
    }
    /* 缩小 subheader 并压缩上下间距 */
    [data-testid="stHeadingWithActionElements"] h3 {
        font-size: 0.95rem !important;
        margin: 4px 0 2px 0 !important;
        padding: 0 !important;
    }
    /* 压缩 divider 上下空白 */
    hr {
        margin: 4px 0 !important;
    }
    /* 压缩 columns 之间的间距 */
    [data-testid="stHorizontalBlock"] {
        gap: 8px !important;
    }
    /* 压缩 block 容器的内边距 */
    [data-testid="stVerticalBlock"] > div {
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }

    /* 侧边栏圆角 */
    [data-testid="stSidebar"] > div:first-child {
        border-radius: 0 16px 16px 0;
        overflow: auto;
    }
    section[data-testid="stSidebar"] {
        border-radius: 0 16px 16px 0 !important;
        overflow: auto !important;
    }
    section[data-testid="stSidebar"] > div {
        border-radius: 0 16px 16px 0 !important;
        overflow: auto !important;
        box-shadow: 2px 0 12px rgba(0,0,0,0.08);
    }
    /* expander 圆角 */
    [data-testid="stExpander"] {
        border-radius: 8px !important;
        overflow: hidden;
    }

    /* 防止 echarts iframe 拦截侧边栏滚轮 */
    [data-testid="stSidebar"] iframe {
        pointer-events: none;
    }
    </style>
    """, unsafe_allow_html=True)

#参数表(所有参数格式为前几字首字母缩写加最后两字全拼,除了那个其他是other)
canshu = {
    "技术参数": {
        # ── 带单位选择的特殊参数 ──────────────────────────────────
        # type 设为 "number_with_unit"，render_param 里有专门分支处理它
        # units        : 下拉框里显示的单位选项列表
        # unit_factors : 每个单位对应的换算系数，乘以用户输入值后统一换算到基准单位
        #                基准单位：功率 → MW，容量 → MWh
        # unit_default : 下拉框默认选中第几个（0 = 第一个）
        # label        : 不含单位的纯名称，单位由下拉框动态显示
        "额定功率": {
            "type": "number_with_unit",
            "label": "额定功率",
            "var": "edgonglv",
            "default": 100.0,
            "step": 1.0,
            "units": ["MW", "kW"],          # 可选单位
            "unit_factors": {               # 换算到 MW：1 MW=1，1 kW=0.001
                "MW": 1.0,
                "kW": 0.001
            },
            "unit_default": 0,              # 默认选 MW（索引 0）
            "help": "储能系统的额定输出功率"
        },
        "额定容量": {
            "type": "number_with_unit",
            "label": "额定容量",
            "var": "edrongliang",
            "default": 200.0,
            "step": 1.0,
            "units": ["MWh", "kWh"],        # 可选单位
            "unit_factors": {               # 换算到 MWh：1 MWh=1，1 kWh=0.001
                "MWh": 1.0,
                "kWh": 0.001
            },
            "unit_default": 0,              # 默认选 MWh（索引 0）
            "help": "储能系统的总能量容量"
        },
        "系统效率 (%)": {
            "type": "slider",
            "var": "xtxiaolv",
            "min": 70,
            "max": 99,
            "default": 94,
            "help": "充放电循环的综合效率",
            "convert": lambda x: x / 100
        },
        "年循环次数": {
            "type": "number",
            "var": "nxhcishu",
            "default": 620,
            "step": 30,
            "min": 200,
            "max": 800,
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
            "default": 0.65,
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
            "default": 0.1,
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
            "max": 20,
            "default": 7,
            "help": "预备费比例",
            "convert": lambda x: x / 100
        }
    },
    
    "收益参数": {
        "放电电价 (元/kWh)": {
            "type": "number",
            "var": "fddianjia",
            "default": 0.9039,
            "step": 0.1,
            "format": "%.2f",
            "help": "峰时售电价格"
        },
        "充电电价 (元/kWh)": {
            "type": "number",
            "var": "cddianjia",
            "default": 0.4413,
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
            "default": 10,
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
            "default": 4,
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
            "default": 5,
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
            "default": 15,
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
        }
    }
}

# 通用参数渲染函数
# param_name : 参数的显示名称（字典的 key），用作控件 label
# config     : 该参数对应的配置字典，包含 type/var/default 等字段
def render_param(param_name, config, current_val):
    """根据配置渲染参数输入控件，只负责显示原始大数"""

    # ── 分支 1：普通数字输入框 ────────────────────────────────
    if config["type"] == "number":
        # 确定格式
        if "format" in config:
            format_str = config["format"]
        elif isinstance(current_val, int):
            format_str = "%d"
        else:
            format_str = "%f"
        
        value = st.number_input(
            label=param_name,
            value=current_val,
            step=config.get("step", 1.0),
            min_value=config.get("min"),
            max_value=config.get("max"),
            format=format_str,
            help=config["help"]
        )

    # ── 分支 2：滑块 ──────────────────────────────────────────
    elif config["type"] == "slider":
        _min = float(config["min"])
        _max = float(config["max"])
        safe_value = float(current_val)
        
        # 如果当前值因为旧数据变成了 0.94 这种小数，强制重置为默认大数（如 94）
        if safe_value < _min or safe_value > _max:
            safe_value = float(config["default"])
        
        value = st.slider(
            label=param_name,
            min_value=_min,
            max_value=_max,
            value=safe_value,
            step=float(config.get("step", 1.0)) if config.get("step") else None,
            help=config["help"]
        )

    # ── 分支 3：数字输入框 + 单位下拉选择 ────────────────────
    elif config["type"] == "number_with_unit":
        col_num, col_unit = st.columns([3, 1])
        with col_num:

            # 简单起见，这里先维持用 default 或者 current_val
            raw_value = st.number_input(
                label=config["label"],
                value=current_val, 
                step=config.get("step", 1.0),
                format="%g",
                help=config["help"]
            )
        with col_unit:
            selected_unit = st.selectbox(
                label="单位",
                options=config["units"],
                index=config.get("unit_default", 0),
                label_visibility="hidden",
                key=f"unit_{config['var']}"
            )

        value = raw_value * config["unit_factors"][selected_unit]

    else:
        value = current_val

    return value

#——————————————————预设方案————————————————————
# 土地费用 = 典型地价(万元/亩) × 5亩
# 充电电价取谷/深谷典型值，放电电价取尖/峰典型值
FA_diqv = {
    # ── 华东 ──────────────────────────────────────────────────
    "上海": {
        "fddianjia":  1.23,
        "cddianjia":  0.34,
        "jsydifei":   450.0,   # 90万/亩×5亩
        "rjngongzi":  12.6,
    },
    "浙江": {
        "fddianjia":  1.02,
        "cddianjia":  0.24,
        "jsydifei":   150.0,   # 30万/亩×5亩
        "rjngongzi":  11.0,
    },
    "江苏": {
        "fddianjia":  1.05,
        "cddianjia":  0.30,
        "jsydifei":   150.0,
        "rjngongzi":   9.0,
    },
    "安徽": {
        "fddianjia":  0.95,
        "cddianjia":  0.25,
        "jsydifei":    90.0,   # 18万/亩×5亩
        "rjngongzi":   7.5,
    },
    "福建": {
        "fddianjia":  0.95,
        "cddianjia":  0.30,
        "jsydifei":   125.0,   # 25万/亩×5亩
        "rjngongzi":   8.0,
    },
    "江西": {
        "fddianjia":  0.90,
        "cddianjia":  0.20,
        "jsydifei":    80.0,   # 16万/亩×5亩
        "rjngongzi":   9.0,
    },
    "山东": {
        "fddianjia":  0.95,
        "cddianjia":  0.20,
        "jsydifei":   125.0,
        "rjngongzi":   9.0,
    },

    # ── 华北 ──────────────────────────────────────────────────
    "北京": {
        "fddianjia":  1.10,
        "cddianjia":  0.45,
        "jsydifei":   475.0,   # 95万/亩×5亩
        "rjngongzi":  15.1,
    },
    "天津": {
        "fddianjia":  1.05,
        "cddianjia":  0.40,
        "jsydifei":   140.0,   # 28万/亩×5亩
        "rjngongzi":   9.0,
    },
    "河北": {
        "fddianjia":  0.85,
        "cddianjia":  0.25,
        "jsydifei":   110.0,   # 22万/亩×5亩
        "rjngongzi":   8.0,
    },
    "山西": {
        "fddianjia":  0.85,
        "cddianjia":  0.25,
        "jsydifei":    75.0,   # 15万/亩×5亩
        "rjngongzi":   9.0,
    },
    "内蒙古": {                # ⚠️ 表注"尚未执行固定分时电价"，峰谷价差仅0.25-0.35，数值为估算
        "fddianjia":  0.60,
        "cddianjia":  0.35,
        "jsydifei":    65.0,   # 13万/亩×5亩
        "rjngongzi":   9.0,
    },

    # ── 华南 ──────────────────────────────────────────────────
    "广东": {
        "fddianjia":  1.02,
        "cddianjia":  0.29,
        "jsydifei":   300.0,   # 60万/亩×5亩
        "rjngongzi":  12.5,
    },
    "海南": {
        "fddianjia":  1.01,
        "cddianjia":  0.38,
        "jsydifei":   100.0,   # 20万/亩×5亩
        "rjngongzi":  11.0,
    },
    "广西": {
        "fddianjia":  0.75,
        "cddianjia":  0.40,
        "jsydifei":    70.0,   # 14万/亩×5亩
        "rjngongzi":  11.2,
    },

    # ── 华中 ──────────────────────────────────────────────────
    "湖南": {
        "fddianjia":  0.95,
        "cddianjia":  0.35,
        "jsydifei":    90.0,
        "rjngongzi":  10.5,
    },
    "河南": {
        "fddianjia":  0.90,
        "cddianjia":  0.35,
        "jsydifei":   100.0,
        "rjngongzi":   7.5,
    },
    "湖北": {
        "fddianjia":  0.95,
        "cddianjia":  0.35,
        "jsydifei":   100.0,
        "rjngongzi":   9.6,
    },

    # ── 西南 ──────────────────────────────────────────────────
    "四川": {
        "fddianjia":  0.85,
        "cddianjia":  0.30,
        "jsydifei":    90.0,
        "rjngongzi":   7.0,
    },
    "重庆": {
        "fddianjia":  0.90,
        "cddianjia":  0.35,
        "jsydifei":    90.0,
        "rjngongzi":   9.0,
    },
    "贵州": {
        "fddianjia":  0.75,
        "cddianjia":  0.35,
        "jsydifei":    70.0,
        "rjngongzi":   7.5,
    },
    "云南": {
        "fddianjia":  0.75,
        "cddianjia":  0.35,
        "jsydifei":    75.0,
        "rjngongzi":   8.0,
    },
    # ── 西北 ──────────────────────────────────────────────────
    "陕西": {                  # ⚠️ 充放电电价表中无陕西，数值为估算
        "fddianjia":  0.80,
        "cddianjia":  0.28,
        "jsydifei":    85.0,   # 17万/亩×5亩
        "rjngongzi":   9.5,
    },
    "甘肃": {                  # ⚠️ 充放电电价表中无甘肃，数值为估算
        "fddianjia":  0.75,
        "cddianjia":  0.25,
        "jsydifei":    60.0,   # 12万/亩×5亩
        "rjngongzi":   7.0,
    },
    "新疆": {                  # ⚠️ 充放电电价表中无新疆，数值为估算
        "fddianjia":  0.65,
        "cddianjia":  0.20,
        "jsydifei":    50.0,   # 10万/亩×5亩
        "rjngongzi":   9.5,
    },
    "青海": {                  # ⚠️ 充放电电价表中无青海，数值为估算
        "fddianjia":  0.65,
        "cddianjia":  0.22,
        "jsydifei":    50.0,
        "rjngongzi":   9.0,
    },
    "宁夏": {                  # ⚠️ 充放电电价表中无宁夏，数值为估算
        "fddianjia":  0.65,
        "cddianjia":  0.22,
        "jsydifei":    45.0,   # 9万/亩×5亩
        "rjngongzi":   8.5,
    },

    # ── 东北 ──────────────────────────────────────────────────
    "辽宁": {                  # ⚠️ 充放电电价表中无辽宁，数值为估算
        "fddianjia":  0.80,
        "cddianjia":  0.28,
        "jsydifei":    75.0,
        "rjngongzi":  10.0,
    },
    "吉林": {                  # ⚠️ 充放电电价表中无吉林，数值为估算
        "fddianjia":  0.75,
        "cddianjia":  0.25,
        "jsydifei":    65.0,   # 13万/亩×5亩
        "rjngongzi":   8.5,
    },
    "黑龙江": {                # ⚠️ 充放电电价表中无黑龙江，数值为估算
        "fddianjia":  0.75,
        "cddianjia":  0.25,
        "jsydifei":    65.0,
        "rjngongzi":   8.5,
    },
}

if "params" not in st.session_state:
    st.session_state.params = {
        config["var"]: config["default"]
        for group in canshu.values()
        for config in group.values()
    }

if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}

with st.sidebar:
    with st.form("sidebar_form"):
        selected_FA_diqv = st.selectbox("简易参数预设(详细自定义见下方)", options=list(FA_diqv.keys()),index=4)
        submitted2 = st.form_submit_button("加载预设")

    if submitted2:
        # 获取选中的城市数据
        yv_data = FA_diqv[selected_FA_diqv]
        # 更新当前的 session_state
        new_params = st.session_state.params.copy()
        for var_name, value in yv_data.items():
            new_params[var_name] = value
        
        st.session_state.params = new_params
        st.success(f"已加载当前方案")
        st.rerun()

    st.divider()

    with st.form("params_form"):
        new_raw_params = {}
        icons = {
        "技术参数": "⚡",
        "成本参数": "💰",
        "收益参数": "📈",
        "财务参数": "🏦",
        "税务与贷款": "💼"
        }
        for group_name, group_params in canshu.items():
            icon = icons.get(group_name,"📋")
            with st.expander(label=f"{icon}{group_name}"):
                for param_name, config in group_params.items():
                    var = config["var"]
                    val_in_store = st.session_state.params.get(var, config["default"])
                    
                    # 渲染控件，直接传值进去
                    # 不再使用 temp_config = config.copy()
                    new_val = render_param(param_name, config, val_in_store)
                    new_raw_params[var] = new_val

        submitted1 = st.form_submit_button("保存并应用参数修改")
        
    if submitted1:
        st.session_state.params = new_raw_params
        st.success("参数已更新")
        st.rerun()

    # ── 方案保存区 ────────────────────────────────────────────
    st.subheader("💾 保存方案")

    scenario_name = st.text_input("方案名称", placeholder="例如：基准方案、高电价情景…", key="scenario_name_input")
    if st.button("保存当前方案", use_container_width=True):
        if scenario_name.strip():
            st.session_state.saved_scenarios[scenario_name.strip()] = dict(params)
            st.success(f"已保存：{scenario_name.strip()}")
        else:
            st.warning("请先输入方案名称")

    if st.session_state.saved_scenarios:
        st.caption(f"已保存 {len(st.session_state.saved_scenarios)} 个方案")
        del_name = st.selectbox("删除方案", options=["—"] + list(st.session_state.saved_scenarios.keys()), key="del_scenario")
        if st.button("删除所选方案", use_container_width=True):
            if del_name != "—":
                del st.session_state.saved_scenarios[del_name]
                st.rerun()
                
params = st.session_state.params
raw_params = st.session_state.params
calc_params = {}

# 2. 统一处理转换逻辑，生成用于计算的字典
for group in canshu.values():
    for config in group.values():
        v = config["var"]
        # 获取当前值，如果没有则取默认值
        val = raw_params.get(v, config["default"])
        # session_state 始终存原始值，取出时统一做 convert
        if "convert" in config:
            calc_params[v] = config["convert"](val)
        else:
            calc_params[v] = val

# 3. 将转换后的干净数据展开为变量
locals().update(calc_params)

if edrongliang <= 0.5:
    diannuan = 6.5
elif 0.5 < edrongliang <= 1:
    diannuan = 14.5
elif 1 < edrongliang <= 2:
    diannuan = 35.0
elif 2 < edrongliang <= 4:
    diannuan = 49.0
elif 4 < edrongliang <= 10:
    diannuan = 47.5
elif 10 < edrongliang <= 100:
    diannuan = 135.0
elif 100 < edrongliang <= 200:
    diannuan = 475.0
else:
    diannuan = 475.0
#计算逻辑

# ── 1. 投资估算 ──────────────────────────────────────────────

# 单位换算及判断
rlhuansuan = edrongliang * 1e6   # 容量换算 MWh → Wh
glhuansuan = edgonglv   * 1e6   # 功率换算 MW  → W

# 1.1 设备费用（万元）
dcxtchenben  = rlhuansuan * dcxtdanjia   / 1e4   # 电池系统
pcschenben   = rlhuansuan * pcsdanjia    / 1e4   # PCS
bmsemschenben= rlhuansuan * bmsemsdanjia / 1e4   # BMS+EMS
sybjdqchenben= glhuansuan * sybjdqdanjia / 1e4   # 升压变及电气
aztsfchenben = (dcxtchenben + pcschenben + bmsemschenben + sybjdqchenben) * aztsfbili + diannuan  # 安装调试费
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
dwtouzi = jttouzi * 1e4 / (edrongliang * 1e3) if edrongliang > 0 else 0

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
dcxtnzheju = dcxtchenben  * (1 - czhilv) / dcxtzjnianxian if dcxtzjnianxian > 0 else 0
pcsnzheju  = pcschenben   * (1 - czhilv) / pcszjnianxian if pcszjnianxian > 0 else 0
tjnzheju   = tjgcfchenben * (1 - czhilv) / tjzjnianxian if tjzjnianxian > 0 else 0

zjfei = []
for year in years:
    zj = 0
    if year <= dcxtzjnianxian: zj += dcxtnzheju
    if year <= pcszjnianxian:  zj += pcsnzheju
    if year <= tjzjnianxian:   zj += tjnzheju
    zjfei.append(zj)

# 3.2 无形资产摊销（万元/年）
txfei = [wxzcyuanzhi / wxzctxnianxian if (wxzctxnianxian > 0 and year <= wxzctxnianxian) else 0 for year in years]

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

# 已修正零除年还款额计算
if dknianxian <= 0:
    nhkuane = 0
elif dklilv <= 0:
    # 如果利率为0，直接本金除以年限
    nhkuane = dkjine / dknianxian
else:
    # 标准等额本息公式
    nhkuane = dkjine * (dklilv * (1 + dklilv) ** dknianxian) / ((1 + dklilv) ** dknianxian - 1)

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
    if abs(hi - lo) < 1e-6:   # 区间足够小，收敛
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

#总评分S
# 1. 静态投资标准化
capex_min = 15000.0  # 1.5亿元
capex_max = 150000.0 # 15亿元
capex_star = (capex_max - jttouzi) / (capex_max - capex_min)
capex_star = max(0, min(1, capex_star)) # 限制在 0-1

# 2. LCOE 标准化
lcoe_min = 0.1
lcoe_max = 0.7
lcoe_star = (lcoe_max - lcoe) / (lcoe_max - lcoe_min)
lcoe_star = max(0, min(1, lcoe_star)) # 限制 in 0-1

# 3. 计算综合评分 S
S_score = ((60 * capex_star + 43 * lcoe_star) / 103) * 100

# ══════════════════════════════════════════════════════════════
# 得分计算函数区（纯计算，不渲染）
# 装饰器 clamp_score 确保所有得分在 0-100 之间
# ══════════════════════════════════════════════════════════════

def clamp_score(func):
    """装饰器：确保得分函数返回值截断在 0-100 之间"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return max(0.0, min(100.0, float(result)))
    return wrapper

@clamp_score
def calc_s_score(jttouzi, lcoe):
    """
    成本性得分
    输入：静态投资(万元)，LCOE(元/kWh)
    标准化范围：投资 1.5亿~15亿，LCOE 0.1~0.7
    权重：60:43
    """
    capex_min, capex_max = 15000.0, 150000.0
    lcoe_min,  lcoe_max  = 0.1, 0.7
    cs = max(0.0, min(1.0, (capex_max - jttouzi) / (capex_max - capex_min)))
    ls = max(0.0, min(1.0, (lcoe_max  - lcoe)    / (lcoe_max  - lcoe_min)))
    return ((60 * cs + 43 * ls) / 103) * 100

@clamp_score
def calc_irr_score(irr):
    """
    盈利性得分（IRR）
    输入：IRR 小数形式（如 0.12 表示 12%），None 返回 0
    规则：6.5%→60分，20%→100分，线性插值；低于0返回0
    """
    if irr is None or irr < 0:
        return 0.0
    score = 60 + (irr - 0.065) / (0.20 - 0.065) * 40
    return score

@clamp_score
def calc_hsq_score(jthshouqi):
    """
    回收性得分（静态回收期）
    输入：回收期年数，None（20年内未回收）返回 0
    规则：10年→60分，4年→100分，线性插值；超过10年返回0
    """
    if jthshouqi is None:
        return 0.0
    score = 60 + (10 - jthshouqi) / (10 - 4) * 40
    return score


# ══════════════════════════════════════════════════════════════
# 敏感性分析函数区
# 固定其他参数，遍历目标参数范围，计算三个得分的变化
# ══════════════════════════════════════════════════════════════

@st.cache_data
def calc_sensitivity(base_params_tuple, vary_var, x_values, is_price_gap=False):
    """
    敏感性分析：固定其他参数，改变目标参数，返回三个得分列表
    
    参数：
        base_params_tuple : 参数字典转成的 tuple，如 tuple(sorted(params.items()))
                            用 tuple 是因为 st.cache_data 要求参数可哈希
        vary_var          : 要变化的参数 var 名，如 "sdshuilv"
        x_values          : 横轴数值 tuple
        is_price_gap      : True 时表示变化峰谷价差
    
    返回：
        (s_list, irr_list, hsq_list) 三个得分列表
    """
    # 还原字典
    base_params = dict(base_params_tuple)
    s_list, irr_list, hsq_list = [], [], []

    for x in x_values:
        p = base_params.copy()

        if is_price_gap:
            p["fddianjia"] = base_params["cddianjia"] + x
        else:
            p[vary_var] = x

        m = calc_metrics(p)

        s   = calc_s_score(m["静态投资(万元)"], m["LCOE(元/kWh)"])
        irr_val = m["IRR(%)"] / 100 if m["IRR(%)"] is not None else None
        irr = calc_irr_score(irr_val)
        hsq = calc_hsq_score(m["静态回收期(年)"])

        s_list.append(round(s, 2))
        irr_list.append(round(irr, 2))
        hsq_list.append(round(hsq, 2))

    return s_list, irr_list, hsq_list


def make_sensitivity_fig(x_values, x_label, s_list, irr_list, hsq_list):
    """
    生成单张敏感性分析折线图
    
    参数：
        x_values  : 横轴数值列表
        x_label   : 横轴标签，如 "峰谷电价差 (元/kWh)"
        s_list    : 成本性得分列表
        irr_list  : 盈利性得分列表
        hsq_list  : 回收性得分列表
    
    返回：plotly Figure 对象
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_values, y=s_list, name="成本性 S",
        mode="lines+markers",
        line=dict(color="#2ecc71", width=2), marker=dict(size=4)
    ))
    fig.add_trace(go.Scatter(
        x=x_values, y=irr_list, name="盈利性 IRR",
        mode="lines+markers",
        line=dict(color="#3498db", width=2), marker=dict(size=4)
    ))
    fig.add_trace(go.Scatter(
        x=x_values, y=hsq_list, name="回收性",
        mode="lines+markers",
        line=dict(color="#e67e22", width=2), marker=dict(size=4)
    ))

    # 60分合格线
    fig.add_hline(
        y=60, line_dash="dash", line_color="red", line_width=1,
        annotation_text="合格线 60分", annotation_position="bottom right"
    )

    fig.update_layout(
        xaxis_title=x_label,
        yaxis_title="得分",
        yaxis=dict(range=[0, 105]),
        legend=dict(orientation="h", y=1.12, x=0),
        margin=dict(t=30, b=40, l=40, r=10),
        height=260,
        plot_bgcolor="rgba(248,249,250,0.8)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


# ══════════════════════════════════════════════════════════════
# 水波图函数区
# 每个函数负责：① 计算水位 ② 生成 echarts option ③ 渲染图表
# 调用方式：在 tab 里直接 render_xxx_liquid()
# ══════════════════════════════════════════════════════════════

def make_liquid_option(level, colors, label_text, key, title=""):
    """
    通用水波图 option 生成 + 渲染函数
    
    参数：
        level      : 水位，0.0 ~ 1.0（超出范围会被截断）
        colors     : 波浪颜色列表，如 ["#2ecc71", "#58d68d", "#82e0aa"]
        label_text : 球内中央显示的文字，如 "12.3%" 或 "7年"
        key        : st_echarts 的唯一 key，同一页面不能重复
        title      : 图表上方标题，为空则不显示
    """
    from streamlit_echarts import st_echarts

    # 截断到合法范围，防止负水位或超过100%
    level = max(0.0, min(1.0, level))

    # 三层波浪，水位依次降低 0.05，制造层次感
    # max(0, ...) 防止低水位时出现负值导致报错
    wave_data = [
        level,
        max(0, level - 0.05),
        max(0, level - 0.10),
    ]

    option = {
        "title": {
            "text": title,
            "left": "center",
            "top": "7%",
            "textStyle": {
                "fontSize": 15,
                "color": "#000000",
                "fontWeight": "bold"
            }
        } if title else {},
        "series": [{
            "type": "liquidFill",
            "data": wave_data,
            "radius": "72%",
            "center": ["50%", "58%"],  # 球心往下偏，给标题留空间
            "color": colors,           # 波浪颜色，与 wave_data 一一对应
            "backgroundStyle": {
                "borderWidth": 2,
                "borderColor": colors[0],   # 外圈边框颜色与主波浪一致
                "color": "#f4f6f7"          # 球内背景色（未被水覆盖的部分）
            },
            "outline": {
                "show": True,
                "borderDistance": 5,        # 外轮廓与球的间距
                "itemStyle": {
                    "borderWidth": 4,
                    "borderColor": colors[0],
                    "shadowBlur": 10,
                    "shadowColor": "rgba(0,0,0,0.2)"
                }
            },
            "label": {
                "show": True,
                "color": "#283747",         # 水面以上文字颜色（深色）
                "insideColor": "#fff",      # 水面以下文字颜色（白色）
                "fontSize": 14,             # 小球小，字体也要小
                "fontWeight": "bold",
                "align": "center",
                "baseline": "middle",
                "position": ["50%", "50%"],
                "formatter": label_text     # 显示的文字内容
            }
        }]
    }

    st_echarts(option, height="140px", key=key)


def render_s_liquid(s_score, key="s_liquid"):
    """
    成本性评分水波图（S分）
    
    评分规则：直接使用 S_score（0~100），已在外部计算好
    颜色：绿色系（分越高越绿）
    
    参数：
        s_score : 成本性综合评分，0~100
        key     : echarts 唯一 key
    """
    level = s_score / 100
    label = f"{s_score:.1f} 分"
    colors = ["#2ecc71", "#58d68d", "#82e0aa"]
    make_liquid_option(level, colors, label, key, title="成本性评分")


def render_irr_liquid(irr, key="irr_liquid"):
    """
    IRR 盈利性水波图
    
    评分规则（线性插值）：
        IRR < 6.5%  → 不合格，水位 = 0，显示"不合格"
        IRR = 6.5%  → 60分，水位 = 0.60
        IRR = 20%   → 100分，水位 = 1.00
        中间线性插值：score = 60 + (irr - 0.065) / (0.20 - 0.065) × 40
    
    颜色：蓝色系
    
    参数：
        irr : IRR 小数形式，如 0.12 表示 12%（None 表示无法计算）
        key : echarts 唯一 key
    """
    if irr is None or irr < 0:
        make_liquid_option(0.0, ["#e74c3c", "#ec7063", "#f1948a"], "不合格", key, title="盈利性评分")
        return
    score = 60 + (irr - 0.065) / (0.20 - 0.065) * 40
    score = min(100, score)
    level = score / 100
    label = f"{irr*100:.1f}%"
    colors = ["#3498db", "#5dade2", "#85c1e9"]
    make_liquid_option(level, colors, label, key, title="盈利性评分")


def render_hsq_liquid(jthshouqi, key="hsq_liquid"):
    """
    动态回收期水波图
    
    评分规则（线性插值，注意：回收期越短越好，水位反向）：
        回收期 > 10年 → 不合格，水位 = 0，显示"不合格"
        回收期 = 10年 → 60分，水位 = 0.60
        回收期 = 4年  → 100分，水位 = 1.00
        中间线性插值：score = 60 + (10 - hsq) / (10 - 4) × 40
    
    颜色：橙色系
    
    参数：
        jthshouqi : 静态回收期（年），None 表示 20 年内未回收
        key       : echarts 唯一 key
    """
    if jthshouqi is None or jthshouqi < 0:
        make_liquid_option(0.0, ["#e74c3c", "#ec7063", "#f1948a"], "不合格", key, title="回收性评分")
        return
    score = 60 + (10 - jthshouqi) / (10 - 4) * 40
    score = min(100, score)
    level = score / 100
    label = f"{jthshouqi} 年"
    colors = ["#e67e22", "#f0a500", "#f7c948"]
    make_liquid_option(level, colors, label, key, title="回收性评分")


def calc_metrics(p):
    """根据参数字典 p 计算并返回核心财务指标字典"""
    # ── 入口统一转换：原始值 → 计算用值 ──────────────────────
    _p = {}
    for group in canshu.values():
        for config in group.values():
            k = config["var"]
            v = p.get(k, config["default"])
            _p[k] = config["convert"](v) if "convert" in config else v
    p = _p
    _edrongliang  = p["edrongliang"]
    _edgonglv     = p["edgonglv"]
    _xtxiaolv     = p["xtxiaolv"]
    _nxhcishu     = p["nxhcishu"]
    _cfdshendu    = p["cfdshendu"]
    _snsjianlv    = p["snsjianlv"]
    _xxsjianlv    = p["xxsjianlv"]
    _dcxtdanjia   = p["dcxtdanjia"]
    _pcsdanjia    = p["pcsdanjia"]
    _bmsemsdanjia = p["bmsemsdanjia"]
    _sybjdqdanjia = p["sybjdqdanjia"]
    _tjgcfdanjia  = p["tjgcfdanjia"]
    _aztsfbili    = p["aztsfbili"]
    _jsydifei     = p["jsydifei"]
    _jrxtongfei   = p["jrxtongfei"]
    _qxkfglifei   = p["qxkfglifei"]
    _ybfeilv      = p["ybfeilv"]
    _fddianjia    = p["fddianjia"]
    _cddianjia    = p["cddianjia"]
    _btshouru     = p["btshouru"]
    _dcxtzjnianxian = p["dcxtzjnianxian"]
    _pcszjnianxian  = p["pcszjnianxian"]
    _tjzjnianxian   = p["tjzjnianxian"]
    _czhilv       = p["czhilv"]
    _wxfeilv      = p["wxfeilv"]
    _bxfeilv      = p["bxfeilv"]
    _clfdwchenben = p["clfdwchenben"]
    _ryshuliang   = p["ryshuliang"]
    _rjngongzi    = p["rjngongzi"]
    _flfzgzbili   = p["flfzgzbili"]
    _other        = p["other"]
    _dcghnianxian = p["dcghnianxian"]
    _dcghbili     = p["dcghbili"]
    _dcghdanjia   = p["dcghdanjia"]
    _wxzctxnianxian = p["wxzctxnianxian"]
    _yygjjtqbili  = p["yygjjtqbili"]
    _dkbili       = p["dkbili"]
    _dklilv       = p["dklilv"]
    _dknianxian   = p["dknianxian"]
    _cjshuilv     = p["cjshuilv"]
    _jyfjialv     = p["jyfjialv"]
    _dfjyfjialv   = p["dfjyfjialv"]
    _sdshuilv     = p["sdshuilv"]
    _sdsjmnianxian = p["sdsjmnianxian"]
    _sdsjbnianxian = p["sdsjbnianxian"]
    _ldzjbili     = p["ldzjbili"]
    _zzshuilv     = p["zzshuilv"]
    _jxsdkfangshi = p["jxsdkfangshi"]

    if _edrongliang <= 0.5: _diannuan = 6.5
    elif _edrongliang <= 1: _diannuan = 14.5
    elif _edrongliang <= 2: _diannuan = 35.0
    elif _edrongliang <= 4: _diannuan = 49.0
    elif _edrongliang <= 10: _diannuan = 47.5
    elif _edrongliang <= 100: _diannuan = 135.0
    else: _diannuan = 475.0

    _rlhuansuan = _edrongliang * 1e6
    _glhuansuan = _edgonglv * 1e6
    _dcxtchenben   = _rlhuansuan * _dcxtdanjia   / 1e4
    _pcschenben    = _rlhuansuan * _pcsdanjia    / 1e4
    _bmsemschenben = _rlhuansuan * _bmsemsdanjia / 1e4
    _sybjdqchenben = _glhuansuan * _sybjdqdanjia / 1e4
    _aztsfchenben  = (_dcxtchenben + _pcschenben + _bmsemschenben + _sybjdqchenben) * _aztsfbili + _diannuan
    _sbheji        = _dcxtchenben + _pcschenben + _bmsemschenben + _sybjdqchenben + _aztsfchenben
    _tjgcfchenben  = _rlhuansuan * _tjgcfdanjia / 1e4
    _qtxiaoji      = _jsydifei + _jrxtongfei + _qxkfglifei
    _ybfei         = (_sbheji + _tjgcfchenben + _qtxiaoji) * _ybfeilv
    _qtheji        = _qtxiaoji + _ybfei
    _kdkzzs        = _sbheji * _zzshuilv if _jxsdkfangshi == 1 else 0
    _jttouzi       = _sbheji + _tjgcfchenben + _qtheji
    _jsqlxi        = _jttouzi * _dkbili * _dklilv * 0.5
    _dttouzi       = _jttouzi + _jsqlxi
    _wxzcyuanzhi   = _qxkfglifei
    _gdzcyuanzhi   = _jttouzi - _kdkzzs - _jsydifei - _wxzcyuanzhi
    _dkjine        = _dttouzi * _dkbili
    _zyzijin       = _dttouzi * (1 - _dkbili)

    if _dknianxian > 0 and _dklilv > 0:
        _nhkuane = _dkjine * (_dklilv * (1 + _dklilv) ** _dknianxian) / ((1 + _dklilv) ** _dknianxian - 1)
    else:
        _nhkuane = 0

    _years = list(range(1, 21))
    _fddianliang, _cddianliang = [], []
    for yr in _years:
        if yr == 1:
            fd = _edrongliang * _nxhcishu * _cfdshendu * (1 - _snsjianlv)
        else:
            fd = _fddianliang[yr - 2] * (1 - _xxsjianlv)
        _fddianliang.append(fd)
        _cddianliang.append(fd / _xtxiaolv)

    _yyshouru   = [fd * 1000 * _fddianjia / 1e4 for fd in _fddianliang]
    _cdgdchenben = [cd * 1000 * _cddianjia / 1e4 for cd in _cddianliang]

    _dcxtnzheju = _dcxtchenben  * (1 - _czhilv) / _dcxtzjnianxian
    _pcsnzheju  = _pcschenben   * (1 - _czhilv) / _pcszjnianxian
    _tjnzheju   = _tjgcfchenben * (1 - _czhilv) / _tjzjnianxian
    _zjfei = []
    for yr in _years:
        zj = 0
        if yr <= _dcxtzjnianxian: zj += _dcxtnzheju
        if yr <= _pcszjnianxian:  zj += _pcsnzheju
        if yr <= _tjzjnianxian:   zj += _tjnzheju
        _zjfei.append(zj)

    _txfei = [_wxzcyuanzhi / _wxzctxnianxian if yr <= _wxzctxnianxian else 0 for yr in _years]
    _wxfei  = [_jttouzi * _wxfeilv] * 20
    _bxfei  = [_jttouzi * _bxfeilv] * 20
    _rgfei  = [_ryshuliang * _rjngongzi * (1 + _flfzgzbili)] * 20
    _clfei  = [fd * 1000 * _clfdwchenben / 1e4 for fd in _fddianliang]
    _qtafei = [_other] * 20
    _dcghfei = [_rlhuansuan * _dcghbili * _dcghdanjia / 1e4 if yr == _dcghnianxian and _dcghnianxian > 0 else 0 for yr in _years]

    _lxzhichu, _huanben = [], []
    yue = _dkjine
    for yr in _years:
        if yr <= _dknianxian and yue > 0:
            lixi = yue * _dklilv
            ben  = _nhkuane - lixi
            yue  = max(0, yue - ben)
        else:
            lixi, ben = 0, 0
        _lxzhichu.append(lixi)
        _huanben.append(ben)

    _xxzzshui = [yy * _zzshuilv for yy in _yyshouru]
    _jxzzshui = [cd * _zzshuilv for cd in _cdgdchenben]
    _yjzzshui = [max(0, x - j) for x, j in zip(_xxzzshui, _jxzzshui)]
    _sjfujia  = [zzs * (_cjshuilv + _jyfjialv + _dfjyfjialv) for zzs in _yjzzshui]

    _zchenben = []
    for i in range(20):
        zc = (_cdgdchenben[i] + _dcghfei[i] + _zjfei[i] + _txfei[i] +
              _wxfei[i] + _rgfei[i] + _bxfei[i] + _clfei[i] + _qtafei[i] + _lxzhichu[i])
        _zchenben.append(zc)

    _lrzonge = [_yyshouru[i] + _btshouru - _zchenben[i] - _sjfujia[i] for i in range(20)]
    _mbkuisun, leiji_ks = [], 0
    for lz in _lrzonge:
        if leiji_ks > 0 and lz > 0:
            mibu = min(leiji_ks, lz); leiji_ks -= mibu
        elif lz < 0:
            mibu = 0; leiji_ks += abs(lz)
        else:
            mibu = 0
        _mbkuisun.append(mibu)

    _ynsuode = [_lrzonge[i] - _mbkuisun[i] for i in range(20)]
    _sdshui = []
    for i, yr in enumerate(_years):
        if _ynsuode[i] <= 0: _sdshui.append(0)
        elif yr <= _sdsjmnianxian: _sdshui.append(0)
        elif yr <= _sdsjmnianxian + _sdsjbnianxian: _sdshui.append(_ynsuode[i] * _sdshuilv * 0.5)
        else: _sdshui.append(_ynsuode[i] * _sdshuilv)

    _jlirun = [_lrzonge[i] - _sdshui[i] for i in range(20)]
    _yygjjin = [max(0, jl * _yygjjtqbili) for jl in _jlirun]

    _ldzijin = _yyshouru[0] * _ldzjbili
    _xjliu = []
    for i, yr in enumerate(_years):
        cf = _jlirun[i] + _zjfei[i] + _txfei[i] - _huanben[i]
        if yr == 20: cf += _ldzijin
        _xjliu.append(cf)

    _ljxjliu = [-(_zyzijin + _ldzijin)]
    for cf in _xjliu:
        _ljxjliu.append(_ljxjliu[-1] + cf)

    _zxlv = 0.08
    _npv = _ljxjliu[0]
    for i, cf in enumerate(_xjliu):
        _npv += cf / (1 + _zxlv) ** (i + 1)

    def _calc_npv_r(rate):
        v = _ljxjliu[0]
        for i, cf in enumerate(_xjliu):
            v += cf / (1 + rate) ** (i + 1)
        return v

    _irr = None
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        npv_mid = _calc_npv_r(mid)
        if abs(hi - lo) < 1e-6:   # 区间足够小，收敛
            _irr = mid; break
        elif npv_mid > 0: lo = mid
        else: hi = mid

    _jthshouqi = None
    for i, v in enumerate(_ljxjliu[1:], 1):
        if v >= 0: _jthshouqi = i; break

    _lcoe_fenzi = sum(_zchenben[i] / (1 + _zxlv) ** (i + 1) for i in range(20))
    _lcoe_fenmu = sum(_fddianliang[i] * 1000 / (1 + _zxlv) ** (i + 1) for i in range(20))
    _lcoe = _lcoe_fenzi * 1e4 / _lcoe_fenmu if _lcoe_fenmu > 0 else 0

    _njlirun   = sum(_lrzonge) / 20
    _njjlirun  = sum(_jlirun)  / 20
    _ztzsyilv  = _njlirun  / _dttouzi if _dttouzi > 0 else 0
    _zbjjlrunlv = _njjlirun / _zyzijin if _zyzijin > 0 else 0

    return {
        "动态投资(万元)": _dttouzi,
        "静态投资(万元)": _jttouzi,
        "自有资金(万元)": _zyzijin,
        "NPV(万元)": _npv,
        "IRR(%)": _irr * 100 if _irr else None,
        "静态回收期(年)": _jthshouqi,
        "LCOE(元/kWh)": _lcoe,
        "ROI(%)": _ztzsyilv * 100,
        "ROE(%)": _zbjjlrunlv * 100,
    }

tab1,tab2,tab3,tab4,tab5 = st.tabs(["主展板","参数配置","web3","web4","web5"])

if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}

#————————可见区————————————————
with tab1:
    # ── 方案对比区 ────────────────────────────────────────────
    if st.session_state.saved_scenarios:
        st.subheader("📊 方案对比")
        compare_names = st.multiselect(
            "选择要对比的方案（可多选）",
            options=list(st.session_state.saved_scenarios.keys()),
            default=list(st.session_state.saved_scenarios.keys())[:2]
                    if len(st.session_state.saved_scenarios) >= 2 else
                    list(st.session_state.saved_scenarios.keys())
        )
        if compare_names:
            compare_data = {"当前方案": calc_metrics(params)}
            for name in compare_names:
                compare_data[name] = calc_metrics(st.session_state.saved_scenarios[name])

            df_compare = pd.DataFrame(compare_data).T
            st.dataframe(df_compare.style.format({
                "动态投资(万元)":  "{:.0f}",
                "静态投资(万元)":  "{:.0f}",
                "自有资金(万元)":  "{:.0f}",
                "NPV(万元)":       "{:.0f}",
                "IRR(%)":          lambda x: f"{x:.2f}" if x is not None else "N/A",
                "静态回收期(年)":  lambda x: f"{x:.0f}" if x is not None else ">20年",
                "LCOE(元/kWh)":    "{:.4f}",
                "ROI(%)":          "{:.2f}",
                "ROE(%)":          "{:.2f}",
            }), use_container_width=True)
        st.divider()

    # 第一排：投资规模
    st.subheader("投资规模")
    z1, m1, y1, e1 = st.columns(4, vertical_alignment="center")
    z1.metric("动态投资", f"{dttouzi:.0f} 万元")
    m1.metric("静态投资", f"{jttouzi:.0f} 万元")
    y1.metric("自有资金", f"{zyzijin:.0f} 万元")
    with e1:
        render_hsq_liquid(jthshouqi)

    # 第二排：核心收益指标
    st.subheader("核心收益及irr评分")
    z2, m2, y2, e2 = st.columns(4, vertical_alignment="center")
    z2.metric("NPV（净现值）", f"{npv:.0f} 万元",
              delta="项目可行 ✓" if npv > 0 else "-项目不可行 ✗")
    m2.metric("IRR（内部收益率）", f"{irr*100:.2f}%" if irr else "N/A",
              delta="高于基准 ✓" if irr and irr > 0.08 else "-低于基准 ✗")
    y2.metric("静态回收期", f"{jthshouqi} 年" if jthshouqi else ">20年",
              delta="回收较快 ✓" if jthshouqi and jthshouqi <= 10 else "-回收较慢 ✗")
    with e2:
        render_irr_liquid(irr)
              
    # 第三排：效率指标
    st.subheader("效率指标及综合评分")
    z3, m3, y3, e3 = st.columns(4, vertical_alignment="center")
    z3.metric("度电成本 LCOE", f"{lcoe:.4f} 元/kWh",
              delta="低于电价 ✓" if lcoe < fddianjia else "-高于电价 ✗")
    m3.metric("总投资收益率 ROI", f"{ztzsyilv*100:.2f}%",
              delta="达标 ✓" if ztzsyilv > 0.08 else "-未达标 ✗")
    y3.metric("资本金净利润率 ROE", f"{zbjjlrunlv*100:.2f}%",
              delta="达标 ✓" if zbjjlrunlv > 0.10 else "-未达标 ✗")
    with e3:
        render_s_liquid(S_score)
    st.divider()

    fig1 = go.Figure()
    fig1.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280)
    fig1.add_trace(go.Scatter(x=list(range(0, 21)), y=ljxjliu, name="累计现金流", fill="tozeroy"))
    fig2 = go.Figure()
    fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280)
    fig2.add_trace(go.Pie(
        labels=["充电成本", "电池更换", "折旧费", "摊销费",
                "维修费", "人工费", "保险费", "材料费", "其他", "利息"],
        values=[sum(cdgdchenben), sum(dcghfei), sum(zjfei), sum(txfei),
                sum(wxfei), sum(rgfei), sum(bxfei), sum(clfei), sum(qtafei), sum(lxzhichu)]
    ))

    L1, R1 = st.columns(2, gap="large")
    with L1:
        with st.container(border=True):
            st.caption("📈 累计现金流")
            st.plotly_chart(fig1, use_container_width=True, key="ljxjinliu")
    with R1:
        with st.container(border=True):
            st.caption("🥧 成本构成")
            st.plotly_chart(fig2, use_container_width=True, key="chenbengouchen")

with tab2:
    # 在 tab 里
    gap_x    = list(np.linspace(0.1, 1.5, 20).round(3))
    tax_x    = list(np.linspace(15, 25, 20).round(1))
    exempt_x = list(range(0, 6))

    s1, irr1, hsq1 = calc_sensitivity(params, None,           gap_x,    is_price_gap=True)
    s2, irr2, hsq2 = calc_sensitivity(params, "sdshuilv",     tax_x)
    s3, irr3, hsq3 = calc_sensitivity(params, "sdsjmnianxian", exempt_x)

    fig_gap    = make_sensitivity_fig(gap_x,    "峰谷电价差 (元/kWh)", s1, irr1, hsq1)
    fig_tax    = make_sensitivity_fig(tax_x,    "所得税率 (%)",         s2, irr2, hsq2)
    fig_exempt = make_sensitivity_fig(exempt_x, "所得税减免年数 (年)",  s3, irr3, hsq3)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("峰谷价差敏感性")
        st.plotly_chart(fig_gap,    use_container_width=True, key="sens_gap")
    with c2:
        st.caption("所得税率敏感性")
        st.plotly_chart(fig_tax,    use_container_width=True, key="sens_tax")
    with c3:
        st.caption("减免年数敏感性")
        st.plotly_chart(fig_exempt, use_container_width=True, key="sens_exempt")