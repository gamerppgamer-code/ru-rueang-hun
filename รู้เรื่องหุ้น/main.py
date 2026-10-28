import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import difflib
import calendar
import hashlib
import os
import re
import random
import secrets
import threading
import queue
import time
from datetime import datetime, timedelta

from stock_api import get_stock_data, get_risk_market_data


# ==================================================
# UI THEME (ตกแต่งหน้าตาเท่านั้น ไม่เกี่ยวกับการทำงานของโปรแกรม)
# ==================================================
THEME_FONT = "Tahoma"

THEME_COLORS = {
    "bg": "#0A1124",         # พื้นหลังหลัก
    "surface": "#0F1830",    # การ์ด / ตาราง
    "field": "#0A1226",      # ช่องกรอก
    "primary": "#4C7DFF",
    "primary_dark": "#3B66DD",
    "hover": "#6C93FF",
    "primary_soft": "#10215C",
    "text": "#E8EEFC",
    "muted": "#8D9BBC",
    "border": "#26365C",
    "selected": "#1C3485",
    "tab_idle": "#0F1830",
    "disabled": "#3A4A70",
    "cyan": "#38D6F0",
    "violet": "#8B7CFF",
    "positive": "#34D399",
    "negative": "#F87171",
    "warning": "#F5A524",
}


def apply_ui_theme(root, colors=None):
    c = dict(THEME_COLORS)
    if colors:
        # เผื่อใช้สีเดิมจาก self.ui_colors ที่ผู้ใช้กำหนดไว้
        c["bg"] = colors.get("background", c["bg"])
        c["surface"] = colors.get("surface", c["surface"])
        c["primary"] = colors.get("primary", c["primary"])
        c["primary_dark"] = colors.get("primary_active", c["primary_dark"])
        c["text"] = colors.get("text", c["text"])
        c["muted"] = colors.get("muted", c["muted"])
        c["border"] = colors.get("border", c["border"])
        c["selected"] = colors.get("selected", c["selected"])

    root.configure(bg=c["bg"])

    # ------------------------------------------------------------
    # วิดเจ็ต tk แบบคลาสสิก (ปฏิทิน, Canvas, ลิสต์ของ Combobox)
    # ต้องเรียกก่อนสร้างวิดเจ็ต จึงใส่ไว้ใน create_style ซึ่งทำงานก่อน
    # ------------------------------------------------------------
    root.option_add("*Canvas.background", c["bg"])
    root.option_add("*Frame.background", c["surface"])
    root.option_add("*Label.background", c["surface"])
    root.option_add("*Label.foreground", c["text"])
    root.option_add("*Frame.highlightBackground", c["border"])
    root.option_add("*TCombobox*Listbox.background", c["surface"])
    root.option_add("*TCombobox*Listbox.foreground", c["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", c["primary"])
    root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
    root.option_add("*TCombobox*Listbox.font", (THEME_FONT, 11))
    root.option_add("*Dialog.msg.font", (THEME_FONT, 10))

    s = ttk.Style(root)
    try:
        s.theme_use("clam")
    except Exception:
        pass

    # ------------------------------------------------------------
    # พื้นฐาน
    # ------------------------------------------------------------
    s.configure(".", font=(THEME_FONT, 10), background=c["bg"], foreground=c["text"])
    s.configure("TFrame", background=c["bg"])
    s.configure("TLabel", background=c["bg"], foreground=c["text"], font=(THEME_FONT, 10))
    s.configure("Title.TLabel", font=(THEME_FONT, 26, "bold"), foreground=c["primary"])
    s.configure("Subtitle.TLabel", font=(THEME_FONT, 12), foreground=c["muted"])
    s.configure("Normal.TLabel", font=(THEME_FONT, 11))

    # ------------------------------------------------------------
    # การ์ด (LabelFrame) : เส้นขอบบาง หัวข้อสีน้ำเงินตัวหนา
    # ------------------------------------------------------------
    s.configure(
        "TLabelframe",
        background=c["bg"],
        bordercolor=c["border"],
        lightcolor=c["border"],
        darkcolor=c["border"],
        borderwidth=1,
        relief="solid",
        padding=6,
    )
    s.configure(
        "TLabelframe.Label",
        background=c["bg"],
        foreground=c["primary"],
        font=(THEME_FONT, 11, "bold"),
    )

    # ------------------------------------------------------------
    # ปุ่ม : น้ำเงินเต็มสี มุมเรียบ มีสถานะ hover / กด / ปิดใช้งาน
    # ------------------------------------------------------------
    s.configure(
        "TButton",
        font=(THEME_FONT, 10, "bold"),
        padding=(14, 8),
        background=c["primary"],
        foreground="#FFFFFF",
        bordercolor=c["primary"],
        lightcolor=c["primary"],
        darkcolor=c["primary"],
        focusthickness=0,
        focuscolor=c["primary"],
        relief="flat",
    )
    s.map(
        "TButton",
        background=[
            ("disabled", c["disabled"]),
            ("pressed", c["primary_dark"]),
            ("active", "#3568D8"),
        ],
        foreground=[("disabled", "#FFFFFF"), ("!disabled", "#FFFFFF")],
        bordercolor=[("pressed", c["primary_dark"]), ("active", "#3568D8")],
        lightcolor=[("pressed", c["primary_dark"]), ("active", "#3568D8")],
        darkcolor=[("pressed", c["primary_dark"]), ("active", "#3568D8")],
    )
    s.configure("Primary.TButton", padding=(16, 9))

    # ------------------------------------------------------------
    # แท็บด้านบน
    # ------------------------------------------------------------
    s.configure("TNotebook", background=c["bg"], borderwidth=0, tabmargins=(4, 6, 4, 0))
    s.configure(
        "TNotebook.Tab",
        font=(THEME_FONT, 11, "bold"),
        padding=(22, 11),
        background=c["tab_idle"],
        foreground=c["muted"],
        borderwidth=0,
    )
    s.map(
        "TNotebook.Tab",
        background=[("selected", c["primary"]), ("active", c["selected"])],
        foreground=[("selected", "#FFFFFF"), ("active", c["primary"])],
        expand=[("selected", (0, 0, 0, 2))],
    )

    # ------------------------------------------------------------
    # ช่องกรอก : ขอบเปลี่ยนเป็นสีน้ำเงินตอนโฟกัส
    # ------------------------------------------------------------
    for name in ("TEntry", "TCombobox", "TSpinbox"):
        s.configure(
            name,
            padding=8,
            fieldbackground=c["surface"],
            background=c["surface"],
            foreground=c["text"],
            bordercolor=c["border"],
            lightcolor=c["border"],
            darkcolor=c["border"],
            insertcolor=c["text"],
            arrowcolor=c["primary"],
        )
        s.map(
            name,
            bordercolor=[("focus", c["primary"])],
            lightcolor=[("focus", c["primary"])],
            darkcolor=[("focus", c["primary"])],
        )
    s.map(
        "TCombobox",
        fieldbackground=[("readonly", c["surface"])],
        foreground=[("readonly", c["text"])],
        selectbackground=[("readonly", c["surface"])],
        selectforeground=[("readonly", c["text"])],
    )

    # ------------------------------------------------------------
    # ตาราง
    # ------------------------------------------------------------
    s.configure(
        "Treeview",
        font=(THEME_FONT, 10),
        rowheight=32,
        background=c["surface"],
        fieldbackground=c["surface"],
        foreground=c["text"],
        bordercolor=c["border"],
        lightcolor=c["border"],
        darkcolor=c["border"],
        borderwidth=1,
        relief="solid",
    )
    s.configure(
        "Treeview.Heading",
        font=(THEME_FONT, 10, "bold"),
        padding=(8, 9),
        background=c["primary_soft"],
        foreground=c["primary"],
        bordercolor=c["border"],
        lightcolor=c["primary_soft"],
        darkcolor=c["primary_soft"],
        relief="flat",
    )
    s.map(
        "Treeview.Heading",
        background=[("active", c["selected"])],
    )
    s.map(
        "Treeview",
        background=[("selected", c["selected"])],
        foreground=[("selected", c["primary_dark"])],
    )

    # ------------------------------------------------------------
    # แถบเลื่อน
    # ------------------------------------------------------------
    for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        s.configure(
            name,
            background="#C9D5EA",
            troughcolor=c["bg"],
            bordercolor=c["bg"],
            lightcolor="#C9D5EA",
            darkcolor="#C9D5EA",
            arrowcolor=c["muted"],
            borderwidth=0,
            arrowsize=14,
            relief="flat",
        )
        s.map(
            name,
            background=[("active", c["primary"]), ("pressed", c["primary_dark"])],
        )

    # ------------------------------------------------------------
    # แถบแสดงระดับความเสี่ยง
    # ------------------------------------------------------------
    s.configure(
        "Horizontal.TProgressbar",
        troughcolor=c["tab_idle"],
        background=c["primary"],
        bordercolor=c["border"],
        lightcolor=c["primary"],
        darkcolor=c["primary"],
        thickness=18,
    )

    # ------------------------------------------------------------
    # อื่น ๆ
    # ------------------------------------------------------------
    s.configure("TSeparator", background=c["border"])
    s.configure("TCheckbutton", background=c["bg"], font=(THEME_FONT, 10))
    s.configure("TRadiobutton", background=c["bg"], font=(THEME_FONT, 10))

    # ------------------------------------------------------------
    # ปรับโทนมืดเพิ่มเติม ให้เหมือนหน้าเข้าสู่ระบบ
    # ------------------------------------------------------------
    root.option_add("*Toplevel.background", c["bg"])
    root.option_add("*Text.background", c["field"])
    root.option_add("*Text.foreground", c["text"])

    s.configure("Title.TLabel", foreground=c["text"])
    s.configure("TLabelframe.Label", foreground=c["cyan"])

    for name in ("TEntry", "TCombobox", "TSpinbox"):
        s.configure(
            name,
            fieldbackground=c["field"],
            background=c["field"],
            selectbackground=c["primary"],
            selectforeground="#FFFFFF",
        )
        s.map(
            name,
            bordercolor=[("focus", c["cyan"])],
            lightcolor=[("focus", c["cyan"])],
            darkcolor=[("focus", c["cyan"])],
        )
    s.map(
        "TCombobox",
        fieldbackground=[("readonly", c["field"])],
        foreground=[("readonly", c["text"])],
        selectbackground=[("readonly", c["field"])],
        selectforeground=[("readonly", c["text"])],
    )

    s.map(
        "TButton",
        background=[
            ("disabled", c["disabled"]),
            ("pressed", c["primary_dark"]),
            ("active", c["hover"]),
        ],
        bordercolor=[("pressed", c["primary_dark"]), ("active", c["hover"])],
        lightcolor=[("pressed", c["primary_dark"]), ("active", c["hover"])],
        darkcolor=[("pressed", c["primary_dark"]), ("active", c["hover"])],
    )

    s.configure(
        "TNotebook.Tab",
        background=c["tab_idle"],
        foreground=c["muted"],
    )
    s.map(
        "TNotebook.Tab",
        background=[("selected", c["primary"]), ("active", c["selected"])],
        foreground=[("selected", "#FFFFFF"), ("active", c["text"])],
    )

    s.configure(
        "Treeview",
        background=c["surface"],
        fieldbackground=c["surface"],
        foreground=c["text"],
    )
    s.configure(
        "Treeview.Heading",
        background=c["primary_soft"],
        foreground=c["cyan"],
        lightcolor=c["primary_soft"],
        darkcolor=c["primary_soft"],
    )
    s.map(
        "Treeview",
        background=[("selected", c["selected"])],
        foreground=[("selected", "#FFFFFF")],
    )
    s.map("Treeview.Heading", background=[("active", c["selected"])])

    for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        s.configure(
            name,
            background=c["border"],
            troughcolor=c["bg"],
            bordercolor=c["bg"],
            lightcolor=c["border"],
            darkcolor=c["border"],
            arrowcolor=c["muted"],
        )
        s.map(
            name,
            background=[("active", c["primary"]), ("pressed", c["primary_dark"])],
        )

    s.configure(
        "Horizontal.TProgressbar",
        troughcolor=c["field"],
        background=c["cyan"],
        bordercolor=c["border"],
        lightcolor=c["cyan"],
        darkcolor=c["cyan"],
    )

    return c


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ==================================================
# PORTFOLIO RISK ENGINE
# ฟังก์ชันคำนวณล้วน ๆ (ไม่แตะ UI) ใช้กับหน้า "วิเคราะห์ความเสี่ยงพอร์ต"
# ==================================================
# กฎจัดกลุ่มอุตสาหกรรม -> (ธีมที่ขับเคลื่อนร่วมกัน, ความอ่อนไหวต่อตลาดเชิงเปรียบเทียบ)
# หมายเหตุ: ความอ่อนไหวเป็นค่าประมาณตามลักษณะอุตสาหกรรม (1.0 = เท่าตลาด)
# ไม่ใช่ค่า beta จริงของหุ้นแต่ละตัว ลำดับสำคัญ (เช่น biotech ต้องมาก่อน technology)
RISK_THEME_TECH = "เทคโนโลยี / AI / ชิป"
RISK_THEME_CONSUMER = "ผู้บริโภค / ยานยนต์ / ค้าปลีก"
RISK_THEME_FINANCE = "การเงิน"
RISK_THEME_HEALTH = "สุขภาพ / เภสัช"
RISK_THEME_ENERGY = "พลังงาน / วัตถุดิบ"
RISK_THEME_INDUSTRIAL = "อุตสาหกรรม / การบิน / ป้องกันประเทศ"
RISK_THEME_DEFENSIVE = "สินค้าจำเป็น / สาธารณูปโภค / สื่อสาร"
RISK_THEME_REALESTATE = "อสังหาริมทรัพย์"

RISK_INDUSTRY_RULES = [
    (("biotech",), RISK_THEME_HEALTH, 1.30),
    (("pharma", "health", "life science", "medical", "drug"), RISK_THEME_HEALTH, 0.75),
    (("semiconductor",), RISK_THEME_TECH, 1.50),
    (("software", "internet", "it service", "computer", "hardware", "electronic"), RISK_THEME_TECH, 1.30),
    (("technology",), RISK_THEME_TECH, 1.25),
    (("electrical",), RISK_THEME_TECH, 1.20),
    (("media", "entertainment", "interactive", "advertising"), RISK_THEME_TECH, 1.15),
    (("telecom", "utilit"), RISK_THEME_DEFENSIVE, 0.65),
    (("communication",), RISK_THEME_TECH, 1.10),
    (("food", "beverage", "household", "tobacco", "staple", "personal products", "supermarket"), RISK_THEME_DEFENSIVE, 0.60),
    (("auto",), RISK_THEME_CONSUMER, 1.30),
    (("retail", "consumer", "hotel", "restaurant", "leisure", "apparel", "textile", "cruise", "casino", "travel"), RISK_THEME_CONSUMER, 1.05),
    (("bank", "financ", "insurance", "capital market", "broker", "payment", "credit"), RISK_THEME_FINANCE, 1.05),
    (("oil", "gas", "energy", "coal", "metal", "mining", "chemical", "steel", "paper", "material"), RISK_THEME_ENERGY, 1.20),
    (("aerospace", "defense", "defence", "machinery", "industrial", "airline", "transport", "logistic", "construction", "building", "engineering", "trading"), RISK_THEME_INDUSTRIAL, 1.15),
    (("real estate", "reit"), RISK_THEME_REALESTATE, 0.95),
]

RISK_UNKNOWN_INDUSTRY = ("", "-", "ไม่ระบุ", "n/a", "na", "unknown", "none")


def _risk_clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def _risk_scale(value, low, high):
    """แปลงค่าเป็นคะแนน 0-100 แบบเส้นตรง (<=low = 0, >=high = 100)"""
    if high == low:
        return 0.0
    return _risk_clamp((value - low) / (high - low) * 100.0)


def classify_industry_risk(industry, symbol=""):
    """คืน (ธีม, ความอ่อนไหวต่อตลาด, ข้อมูลอุตสาหกรรมครบหรือไม่)"""
    text = str(industry or "").strip().lower()

    if text in RISK_UNKNOWN_INDUSTRY:
        return f"ไม่ระบุ ({symbol})", 1.0, False

    for keywords, theme, sensitivity in RISK_INDUSTRY_RULES:
        for keyword in keywords:
            if keyword in text:
                return theme, sensitivity, True

    return f"อื่น ๆ ({industry})", 1.0, True


def sensitivity_label(sensitivity):
    if sensitivity < 0.8:
        return "ต่ำ"
    if sensitivity < 1.1:
        return "กลาง"
    if sensitivity < 1.35:
        return "สูง"
    return "สูงมาก"


def volatility_label(volatility):
    """ระดับความผันผวนต่อปี (%) ของหุ้นรายตัว"""
    if volatility is None:
        return "-"
    if volatility < 25:
        return "ต่ำ"
    if volatility < 40:
        return "กลาง"
    if volatility < 60:
        return "สูง"
    return "สูงมาก"


def _weighted_average(stocks, key):
    """ค่าเฉลี่ยถ่วงน้ำหนักเฉพาะหุ้นที่มีข้อมูล คืน (ค่า, น้ำหนักรวมที่มีข้อมูล %)"""
    covered = [s for s in stocks if s.get(key) is not None]
    covered_weight = sum(s["weight"] for s in covered)

    if not covered or covered_weight <= 0:
        return None, 0.0

    value = sum(s["weight"] * s[key] for s in covered) / covered_weight
    return value, covered_weight


def build_portfolio_risk_report(portfolio, market_data=None):
    """
    วิเคราะห์โครงสร้างพอร์ตเชิงลึกจากข้อมูล symbol / amount / industry
    คืน dict ที่หน้า UI นำไปแสดงผล (ไม่มีการเรียกเครือข่ายหรือฐานข้อมูล)

    market_data: {symbol: {"beta", "beta_source", "volatility", "max_drawdown"}}
    ถ้ามี beta จริงจะใช้แทนค่าประมาณจากชื่ออุตสาหกรรม (หุ้นที่ไม่มีข้อมูลยังใช้ค่าประมาณ)
    """
    market_data = market_data or {}
    total = sum(item["amount"] for item in portfolio)
    count = len(portfolio)

    # ---------- รายหุ้น ----------
    stocks = []
    for item in portfolio:
        theme, sensitivity, known = classify_industry_risk(
            item["industry"], item["symbol"]
        )

        market = market_data.get(item["symbol"]) or {}
        real_beta = market.get("beta")

        if real_beta is not None:
            sensitivity = _risk_clamp(float(real_beta), 0.1, 3.0)
            sens_source = "beta"
        else:
            sens_source = "estimate"

        stocks.append({
            "symbol": item["symbol"],
            "company": item["company"],
            "industry": item["industry"],
            "amount": item["amount"],
            "weight": item["amount"] / total * 100.0,
            "theme": theme,
            "sensitivity": sensitivity,
            "sens_label": sensitivity_label(sensitivity),
            "sens_source": sens_source,
            "beta": real_beta,
            "beta_source": market.get("beta_source"),
            "volatility": market.get("volatility"),
            "vol_label": volatility_label(market.get("volatility")),
            "max_drawdown": market.get("max_drawdown"),
            "known": known,
        })

    stocks.sort(key=lambda s: s["amount"], reverse=True)

    weighted_sens_total = sum(s["weight"] * s["sensitivity"] for s in stocks)
    for s in stocks:
        s["risk_share"] = (
            s["weight"] * s["sensitivity"] / weighted_sens_total * 100.0
        )

    weights = [s["weight"] for s in stocks]
    top1 = weights[0]
    top3 = sum(weights[:3])
    top5 = sum(weights[:5])
    top_stock = stocks[0]

    hhi = sum(w * w for w in weights)
    effective_stocks = 10000.0 / hhi
    avg_sensitivity = weighted_sens_total / 100.0

    # ---------- ข้อมูลตลาดจริง (beta / volatility / drawdown) ----------
    beta_stocks = [s for s in stocks if s["sens_source"] == "beta"]
    beta_count = len(beta_stocks)
    beta_coverage = sum(s["weight"] for s in beta_stocks)
    weighted_volatility, vol_coverage = _weighted_average(stocks, "volatility")
    weighted_drawdown, dd_coverage = _weighted_average(stocks, "max_drawdown")
    market_stocks = [
        s for s in stocks
        if s["beta"] is not None
        or s["volatility"] is not None
        or s["max_drawdown"] is not None
    ]
    missing_market = [
        s["symbol"] for s in stocks
        if s["beta"] is None and s["volatility"] is None
    ]

    # ---------- รายอุตสาหกรรม / ธีม ----------
    industry_amounts = {}
    for s in stocks:
        industry_amounts[s["industry"]] = (
            industry_amounts.get(s["industry"], 0.0) + s["amount"]
        )
    industry_weights = {
        name: amount / total * 100.0
        for name, amount in industry_amounts.items()
    }
    top_industry = max(industry_weights, key=industry_weights.get)
    top_industry_weight = industry_weights[top_industry]
    industry_hhi = sum(w * w for w in industry_weights.values())
    effective_industries = 10000.0 / industry_hhi

    theme_amounts = {}
    theme_members = {}
    theme_industries = {}
    theme_sens = {}
    for s in stocks:
        t = s["theme"]
        theme_amounts[t] = theme_amounts.get(t, 0.0) + s["amount"]
        theme_members.setdefault(t, []).append(s["symbol"])
        theme_industries.setdefault(t, set()).add(s["industry"])
        theme_sens[t] = theme_sens.get(t, 0.0) + s["weight"] * s["sensitivity"]

    themes = []
    for t, amount in sorted(theme_amounts.items(), key=lambda kv: -kv[1]):
        weight = amount / total * 100.0
        themes.append({
            "theme": t,
            "members": theme_members[t],
            "industries": sorted(theme_industries[t]),
            "weight": weight,
            "amount": amount,
            "sensitivity": theme_sens[t] / weight if weight else 1.0,
        })
    top_theme = themes[0]

    # ---------- องค์ประกอบคะแนน (0-100 ยิ่งสูงยิ่งเสี่ยง) ----------
    stock_score = (
        0.6 * _risk_scale(top1, 10, 60)
        + 0.4 * _risk_scale(top3, 30, 90)
    )
    industry_score = _risk_scale(top_industry_weight, 20, 80)
    depth_score = _risk_scale(10.0 - effective_stocks, 0, 9)
    theme_score = _risk_scale(top_theme["weight"], 30, 90)
    beta_score = _risk_scale(avg_sensitivity, 0.6, 1.5)
    if weighted_volatility is not None:
        # ถ้ามีความผันผวนจริง ให้ผสมกับ beta (ความผันผวนเฉลี่ย 15% = 0, 60% = 100)
        vol_score = _risk_scale(weighted_volatility, 15, 60)
        sens_score = 0.6 * beta_score + 0.4 * vol_score
    else:
        sens_score = beta_score

    if beta_coverage >= 99.9:
        beta_text = "beta จริงทุกตัว"
    elif beta_count > 0:
        beta_text = (
            f"beta จริง {beta_count}/{count} ตัว ({beta_coverage:.0f}% ของพอร์ต) "
            "ที่เหลือประมาณจากอุตสาหกรรม"
        )
    else:
        beta_text = "ประมาณจากประเภทอุตสาหกรรม ยังไม่มี beta จริง"

    sens_note = f"ค่าเฉลี่ยถ่วงน้ำหนัก {avg_sensitivity:.2f} เท่าของตลาด ({beta_text})"
    if weighted_volatility is not None:
        sens_note += (
            f" | ความผันผวนเฉลี่ย {weighted_volatility:.1f}%/ปี"
            + (
                f" (ครอบคลุม {vol_coverage:.0f}% ของพอร์ต)"
                if vol_coverage < 99.9 else ""
            )
        )

    factors = [
        {
            "key": "stock", "name": "การกระจุกตัวรายหุ้น", "weight": 30,
            "score": stock_score,
            "note": (
                f"หุ้นใหญ่สุด {top_stock['symbol']} {top1:.1f}% | "
                f"3 อันดับแรกรวม {top3:.1f}% (ยิ่งพึ่งหุ้นไม่กี่ตัวยิ่งเสี่ยง)"
            ),
        },
        {
            "key": "industry", "name": "การกระจุกตัวรายอุตสาหกรรม", "weight": 25,
            "score": industry_score,
            "note": (
                f"อุตสาหกรรมหลัก {top_industry} {top_industry_weight:.1f}% | "
                f"มี {len(industry_weights)} อุตสาหกรรม "
                f"(เทียบเท่า {effective_industries:.1f} กลุ่มที่เท่ากัน)"
            ),
        },
        {
            "key": "depth", "name": "ความลึกของการกระจาย", "weight": 20,
            "score": depth_score,
            "note": (
                f"ถือจริง {count} ตัว แต่เทียบเท่าหุ้นที่น้ำหนักเท่ากันเพียง "
                f"{effective_stocks:.1f} ตัว (HHI {hhi:,.0f})"
            ),
        },
        {
            "key": "theme", "name": "ธีม / ปัจจัยขับเคลื่อนร่วมกัน", "weight": 15,
            "score": theme_score,
            "note": (
                f"ธีมหลัก \"{top_theme['theme']}\" {top_theme['weight']:.1f}% "
                f"({', '.join(top_theme['members'][:6])}) มักขึ้นลงตามปัจจัยเดียวกัน"
            ),
        },
        {
            "key": "sens", "name": "ความอ่อนไหวและความผันผวน", "weight": 10,
            "score": sens_score,
            "note": sens_note,
        },
    ]

    for f in factors:
        f["contribution"] = f["score"] * f["weight"] / 100.0

    score = sum(f["contribution"] for f in factors)

    # ---------- Stress test (สมมติฐานสมมุติ ไม่ใช่การพยากรณ์) ----------
    def scenario(name, assumption, loss_pct):
        loss_amount = total * loss_pct / 100.0
        if loss_pct >= 25:
            severity = "high"
        elif loss_pct >= 12:
            severity = "mid"
        else:
            severity = ""
        return {
            "name": name,
            "assumption": assumption,
            "loss_pct": loss_pct,
            "loss_amount": loss_amount,
            "remaining": total - loss_amount,
            "severity": severity,
        }

    scenarios = [
        scenario(
            "ตลาดหุ้นปรับตัวลงแรง",
            f"ตลาด -20% ถ่วงตามความอ่อนไหว (เฉลี่ย {avg_sensitivity:.2f} เท่า, "
            + (
                "beta จริง" if beta_coverage >= 99.9
                else f"beta จริง {beta_count}/{count} ตัว"
            )
            + ")",
            20.0 * avg_sensitivity,
        ),
        scenario(
            "หุ้นใหญ่สุดลงแรง",
            f"{top_stock['symbol']} -30% ส่วนอื่นคงที่",
            top1 * 0.30,
        ),
        scenario(
            "หุ้นใหญ่สุดเกิดเหตุร้ายแรง",
            f"{top_stock['symbol']} -50% (เช่น ผลประกอบการพลาดหนัก/ข่าวร้าย)",
            top1 * 0.50,
        ),
        scenario(
            "3 อันดับแรกลงพร้อมกัน",
            f"{', '.join(s['symbol'] for s in stocks[:3])} ลงตัวละ -20%",
            top3 * 0.20,
        ),
        scenario(
            "อุตสาหกรรมหลักถูกกดดัน",
            f"{top_industry} -25% ส่วนอื่นคงที่",
            top_industry_weight * 0.25,
        ),
        scenario(
            "ธีมหลักถูกกดดัน",
            f"{top_theme['theme']} -30% ส่วนอื่นคงที่",
            top_theme["weight"] * 0.30,
        ),
    ]

    if weighted_drawdown is not None:
        scenarios.append(scenario(
            "ซ้ำรอย Drawdown สูงสุดย้อนหลัง",
            f"ทุกหุ้นลงเท่าที่เคยลงสูงสุดใน 1 ปีพร้อมกัน "
            f"(เฉลี่ย {weighted_drawdown:.1f}% กรณีเลวร้าย)",
            weighted_drawdown * dd_coverage / 100.0,
        ))

    worst_scenario = max(scenarios, key=lambda sc: sc["loss_pct"])

    # ---------- แนวทางปรับสมดุล ----------
    stock_cap = 25.0
    industry_cap = 40.0
    equal_weight = 100.0 / count

    rebalance = []
    for s in stocks:
        excess_amount = max(0.0, s["amount"] - total * stock_cap / 100.0)
        rebalance.append({
            "symbol": s["symbol"],
            "weight": s["weight"],
            "equal_weight": equal_weight,
            "diff": s["weight"] - equal_weight,
            "excess_amount": excess_amount,
        })

    # เงินใหม่ที่ต้องเติมเพื่อให้หุ้นใหญ่สุดเหลือเท่าเพดาน (ไม่ต้องขายของเดิม)
    new_money_for_cap = max(
        0.0, top_stock["amount"] / (stock_cap / 100.0) - total
    )
    industries_over_cap = [
        (name, w, max(0.0, industry_amounts[name] - total * industry_cap / 100.0))
        for name, w in sorted(industry_weights.items(), key=lambda kv: -kv[1])
        if w > industry_cap
    ]

    unknown_stocks = [s for s in stocks if not s["known"]]
    unknown_weight = sum(s["weight"] for s in unknown_stocks)

    report = {
        "total": total,
        "count": count,
        "stocks": stocks,
        "top1": top1,
        "top3": top3,
        "top5": top5,
        "top_stock": top_stock,
        "hhi": hhi,
        "effective_stocks": effective_stocks,
        "avg_sensitivity": avg_sensitivity,
        "industry_weights": industry_weights,
        "industry_amounts": industry_amounts,
        "top_industry": top_industry,
        "top_industry_weight": top_industry_weight,
        "industry_hhi": industry_hhi,
        "effective_industries": effective_industries,
        "themes": themes,
        "top_theme": top_theme,
        "factors": factors,
        "score": score,
        "scenarios": scenarios,
        "worst_scenario": worst_scenario,
        "rebalance": rebalance,
        "stock_cap": stock_cap,
        "industry_cap": industry_cap,
        "equal_weight": equal_weight,
        "new_money_for_cap": new_money_for_cap,
        "industries_over_cap": industries_over_cap,
        "unknown_stocks": unknown_stocks,
        "unknown_weight": unknown_weight,
        "beta_count": beta_count,
        "beta_coverage": beta_coverage,
        "weighted_volatility": weighted_volatility,
        "vol_coverage": vol_coverage,
        "weighted_drawdown": weighted_drawdown,
        "dd_coverage": dd_coverage,
        "market_count": len(market_stocks),
        "missing_market": missing_market,
    }

    report["narrative"] = build_risk_narrative(report)
    report["extra_points"], report["extra_protect"], report["extra_advice"] = (
        build_risk_insights(report)
    )
    return report


def build_risk_insights(r):
    """ข้อความเพิ่มสำหรับกล่อง 'จุดที่ต้องระวัง / ช่วยลดความเสี่ยง / คำแนะนำ'"""
    points, protect, advice = [], [], []

    if r["count"] >= 3 and r["top3"] >= 80:
        points.append(
            f"3 อันดับแรกรวมกัน {r['top3']:.1f}% ของพอร์ต "
            "หุ้นที่เหลือแทบไม่ช่วยกระจายความเสี่ยง"
        )
    elif r["count"] >= 6 and r["top3"] < 55:
        protect.append(
            f"3 อันดับแรกรวมกันเพียง {r['top3']:.1f}% "
            "น้ำหนักไม่ได้พึ่งหุ้นไม่กี่ตัว"
        )

    if r["count"] >= 2 and r["effective_stocks"] < r["count"] * 0.6:
        points.append(
            f"ถือ {r['count']} ตัว แต่น้ำหนักไม่เท่ากัน ทำให้เทียบเท่าหุ้นที่"
            f"น้ำหนักเท่ากันเพียง {r['effective_stocks']:.1f} ตัว"
        )
    elif r["count"] >= 4 and r["effective_stocks"] >= r["count"] * 0.8:
        protect.append(
            f"น้ำหนักค่อนข้างสม่ำเสมอ (เทียบเท่า {r['effective_stocks']:.1f} จาก "
            f"{r['count']} ตัว)"
        )

    theme = r["top_theme"]
    if len(theme["members"]) >= 2 and theme["weight"] >= 60:
        points.append(
            f"หุ้นในธีม \"{theme['theme']}\" ({', '.join(theme['members'][:6])}) "
            f"รวมกัน {theme['weight']:.1f}% แม้ชื่ออุตสาหกรรมต่างกัน "
            "แต่มักขึ้นลงไปในทิศทางเดียวกัน (ความเสี่ยงซ่อนเร้น)"
        )
        advice.append(
            f"เพิ่มสินทรัพย์ที่ขับเคลื่อนด้วยปัจจัยต่างจากธีม \"{theme['theme']}\" "
            "เช่น กลุ่มสุขภาพ สินค้าจำเป็น สาธารณูปโภค หรือกองทุนดัชนีวงกว้าง"
        )
    elif theme["weight"] < 45 and r["count"] >= 4:
        protect.append(
            f"ไม่มีธีมใดเกิน {theme['weight']:.1f}% ปัจจัยขับเคลื่อนค่อนข้างหลากหลาย"
        )

    if r["avg_sensitivity"] >= 1.25:
        points.append(
            f"พอร์ตมีความอ่อนไหวต่อตลาดเฉลี่ย {r['avg_sensitivity']:.2f} เท่า "
            "หากตลาดผันผวนแรง พอร์ตมีแนวโน้มแกว่งแรงกว่าตลาด"
        )
    elif r["avg_sensitivity"] <= 0.9:
        protect.append(
            f"ความอ่อนไหวต่อตลาดเฉลี่ยเพียง {r['avg_sensitivity']:.2f} เท่า "
            "พอร์ตมีสัดส่วนกลุ่มป้องกันตัวอยู่พอสมควร"
        )

    # ---------- ข้อมูลตลาดจริง ----------
    vol = r.get("weighted_volatility")
    if vol is not None:
        if vol >= 45:
            points.append(
                f"ความผันผวนย้อนหลัง 1 ปีเฉลี่ยถ่วงน้ำหนัก {vol:.1f}%/ปี อยู่ในระดับสูง "
                "ราคาพอร์ตมีแนวโน้มแกว่งแรงในช่วงสั้น"
            )
        elif vol <= 25 and r["vol_coverage"] >= 60:
            protect.append(
                f"ความผันผวนย้อนหลังเฉลี่ยเพียง {vol:.1f}%/ปี ราคาแกว่งไม่แรงนัก"
            )

    dd = r.get("weighted_drawdown")
    if dd is not None and dd >= 35:
        points.append(
            f"ย้อนหลัง 1 ปี หุ้นในพอร์ตเคยลดลงจากจุดสูงสุดเฉลี่ย {dd:.1f}% "
            "แสดงว่าเคยเกิดช่วงขาดทุนลึกมาแล้ว"
        )

    high_risk = [
        s for s in r["stocks"]
        if s["weight"] >= 15
        and ((s["volatility"] or 0) >= 60 or (s["beta"] or 0) >= 1.8)
    ]
    if high_risk:
        names = ", ".join(s["symbol"] for s in high_risk)
        points.append(
            f"{names} มีน้ำหนักตั้งแต่ 15% ขึ้นไป และมีความผันผวนหรือ beta สูงมาก "
            "ส่งผลต่อการแกว่งของพอร์ตมากกว่าสัดส่วนที่ถือ"
        )
        advice.append(
            f"พิจารณาจำกัดน้ำหนักของ {names} หรือผสมหุ้นที่ผันผวนต่ำกว่าเพื่อลดการแกว่งของพอร์ต"
        )

    if r.get("missing_market"):
        names = ", ".join(r["missing_market"])
        points.append(
            f"ยังไม่มีข้อมูลตลาดจริงของ {names} จึงใช้ค่าประมาณจากอุตสาหกรรมแทน "
            "(กดปุ่ม \"รีเฟรชข้อมูลตลาด\" เพื่อลองดึงใหม่)"
        )

    worst = r["worst_scenario"]
    if worst["loss_pct"] >= 25:
        points.append(
            f"ภายใต้สถานการณ์ \"{worst['name']}\" พอร์ตอาจลดลงราว "
            f"{worst['loss_pct']:.1f}% (≈ {worst['loss_amount']:,.0f} บาท)"
        )
    elif worst["loss_pct"] < 12:
        protect.append(
            f"สถานการณ์จำลองที่แย่ที่สุดทำให้พอร์ตลดลงราว {worst['loss_pct']:.1f}% "
            "ซึ่งยังอยู่ในระดับจำกัด"
        )

    if r["top1"] > r["stock_cap"]:
        advice.append(
            f"หากต้องการให้ {r['top_stock']['symbol']} ไม่เกิน {r['stock_cap']:.0f}% "
            f"โดยไม่ขายของเดิม ต้องเติมเงินลงทุนใหม่ราว {r['new_money_for_cap']:,.0f} บาท "
            "ในหุ้น/อุตสาหกรรมอื่น (หรือทยอยขายส่วนเกินตามแผนของคุณ)"
        )

    for name, weight, excess in r["industries_over_cap"][:2]:
        advice.append(
            f"อุตสาหกรรม {name} {weight:.1f}% เกินเพดานอ้างอิง "
            f"{r['industry_cap']:.0f}% ราว {excess:,.0f} บาท"
        )

    if r["count"] < 6:
        advice.append(
            "พิจารณาให้มีหุ้นอย่างน้อย 6-8 ตัวจากหลายอุตสาหกรรม "
            "เพื่อให้จำนวนหุ้นที่แท้จริงเพิ่มขึ้น"
        )

    if r["unknown_stocks"]:
        names = ", ".join(s["symbol"] for s in r["unknown_stocks"])
        points.append(
            f"ไม่มีข้อมูลอุตสาหกรรมของ {names} ({r['unknown_weight']:.1f}% ของพอร์ต) "
            "ผลวิเคราะห์รายอุตสาหกรรม/ธีมอาจคลาดเคลื่อน"
        )

    return points, protect, advice


def build_risk_narrative(r):
    """บทวิเคราะห์เชิงลึกเป็นหัวข้อ (หัวข้อ, เนื้อหา)"""
    sections = []

    # 1) ที่มาของคะแนน
    ranked = sorted(r["factors"], key=lambda f: -f["contribution"])
    first, second = ranked[0], ranked[1]
    sections.append((
        "1) คะแนนความเสี่ยงมาจากอะไร",
        f"คะแนนรวม {r['score']:.0f}/100 ประกอบจาก 5 องค์ประกอบ "
        f"ตัวที่ดันคะแนนมากที่สุดคือ \"{first['name']}\" "
        f"(คะแนนย่อย {first['score']:.0f}/100 เพิ่มให้ {first['contribution']:.1f} คะแนน) "
        f"รองลงมาคือ \"{second['name']}\" "
        f"({second['contribution']:.1f} คะแนน) "
        "การลดความเสี่ยงให้ได้ผลเร็วควรเริ่มแก้ที่องค์ประกอบสองตัวนี้ก่อน",
    ))

    # 2) ความเสี่ยงซ่อนเร้นจากธีม
    theme = r["top_theme"]
    industry_count = len(r["industry_weights"])
    if len(theme["industries"]) >= 2:
        hidden = (
            f"พอร์ตมี {industry_count} อุตสาหกรรม แต่ธีม \"{theme['theme']}\" "
            f"รวม {len(theme['industries'])} อุตสาหกรรม "
            f"({', '.join(theme['industries'][:5])}) น้ำหนักรวม {theme['weight']:.1f}% "
            "หุ้นกลุ่มนี้มักได้รับผลจากปัจจัยเดียวกัน เช่น ดอกเบี้ย กระแสเงินลงทุน "
            "และอารมณ์ของตลาด การกระจายตามชื่ออุตสาหกรรมจึงอาจดูดีกว่าความเป็นจริง"
        )
    elif theme["weight"] >= 60:
        hidden = (
            f"ธีม \"{theme['theme']}\" มีน้ำหนัก {theme['weight']:.1f}% "
            "ปัจจัยของกลุ่มนี้จึงกำหนดผลตอบแทนของพอร์ตเป็นส่วนใหญ่"
        )
    else:
        hidden = (
            f"ธีมหลักคือ \"{theme['theme']}\" น้ำหนัก {theme['weight']:.1f}% "
            "ไม่สูงจนน่ากังวล และไม่พบการซ้อนทับของหลายอุตสาหกรรมในธีมเดียวกันมากนัก"
        )
    sections.append(("2) ความเสี่ยงซ่อนเร้นจากธีมเดียวกัน", hidden))

    # 3) ใครคือตัวขับความเสี่ยง
    by_risk = sorted(r["stocks"], key=lambda s: -s["risk_share"])
    lead = by_risk[0]
    drivers = (
        f"{lead['symbol']} มีน้ำหนัก {lead['weight']:.1f}% "
        f"แต่คิดเป็น {lead['risk_share']:.1f}% ของความเสี่ยงเชิงเปรียบเทียบ "
        f"(ความอ่อนไหว {lead['sens_label']}"
        + (
            f", beta {lead['beta']:.2f}" if lead["beta"] is not None
            else ", ประมาณจากอุตสาหกรรม"
        )
        + (
            f", ผันผวน {lead['volatility']:.0f}%/ปี"
            if lead["volatility"] is not None else ""
        )
        + ")"
    )
    heavier = [
        s for s in by_risk
        if s["risk_share"] > s["weight"] * 1.15 and s["symbol"] != lead["symbol"]
    ]
    if heavier:
        drivers += (
            " | หุ้นที่ส่งผลต่อความเสี่ยงมากกว่าน้ำหนักที่ถือ: "
            + ", ".join(s["symbol"] for s in heavier[:4])
        )
    sections.append(("3) ตัวขับความเสี่ยงของพอร์ต", drivers))

    # 4) Stress test
    worst = r["worst_scenario"]
    market = r["scenarios"][0]
    sections.append((
        "4) หากเกิดเหตุการณ์ไม่ดี",
        f"ถ้าตลาดลง 20% พอร์ตนี้อาจลดราว {market['loss_pct']:.1f}% "
        f"(≈ {market['loss_amount']:,.0f} บาท) สถานการณ์จำลองที่กระทบหนักที่สุดคือ "
        f"\"{worst['name']}\" ลดราว {worst['loss_pct']:.1f}% "
        f"(≈ {worst['loss_amount']:,.0f} บาท) เหลือมูลค่า {worst['remaining']:,.0f} บาท "
        "ตัวเลขเหล่านี้เป็นสมมติฐานเพื่อเปรียบเทียบ ไม่ใช่การพยากรณ์",
    ))

    if r.get("weighted_drawdown") is not None:
        sections.append((
            "4.1) เทียบกับสิ่งที่เคยเกิดขึ้นจริงใน 1 ปีที่ผ่านมา",
            f"หุ้นในพอร์ตเคยลดลงจากจุดสูงสุดเฉลี่ยถ่วงน้ำหนัก {r['weighted_drawdown']:.1f}% "
            f"(ครอบคลุม {r['dd_coverage']:.0f}% ของพอร์ต)"
            + (
                f" และมีความผันผวนเฉลี่ย {r['weighted_volatility']:.1f}%/ปี"
                if r.get("weighted_volatility") is not None else ""
            )
            + " ค่า drawdown เป็นของหุ้นแต่ละตัวแยกกัน หุ้นไม่ได้ลงถึงจุดต่ำสุดพร้อมกันเสมอไป "
            "จึงเป็นภาพกรณีเลวร้ายมากกว่าผลขาดทุนที่คาดว่าจะเกิดจริง",
        ))

    # 5) เป้าหมายปรับสมดุล
    if r["top1"] > r["stock_cap"]:
        rebalance_text = (
            f"เพดานอ้างอิงรายหุ้น {r['stock_cap']:.0f}% และรายอุตสาหกรรม "
            f"{r['industry_cap']:.0f}% ตอนนี้ {r['top_stock']['symbol']} อยู่ที่ "
            f"{r['top1']:.1f}% หากไม่ขาย ต้องเติมเงินใหม่ราว "
            f"{r['new_money_for_cap']:,.0f} บาทกระจายไปหุ้นอื่นจึงจะเหลือ "
            f"{r['stock_cap']:.0f}% "
        )
        if r["count"] < 4:
            rebalance_text += (
                "และเมื่อมีหุ้นไม่ถึง 4 ตัว จะไม่สามารถอยู่ใต้เพดานรายหุ้นได้ครบทุกตัว "
                "จึงควรเพิ่มจำนวนหุ้นด้วย"
            )
    else:
        rebalance_text = (
            f"ไม่มีหุ้นใดเกินเพดานอ้างอิง {r['stock_cap']:.0f}% "
            f"น้ำหนักเท่ากันของพอร์ตนี้คือ {r['equal_weight']:.1f}% ต่อตัว "
            "ควรทบทวนเมื่อมูลค่าหุ้นแต่ละตัวเปลี่ยนไปมาก"
        )
    sections.append(("5) เป้าหมายการปรับสมดุล", rebalance_text))

    # 6) คุณภาพข้อมูล
    if r["unknown_stocks"]:
        quality = (
            f"มี {len(r['unknown_stocks'])} ตัวที่ไม่มีข้อมูลอุตสาหกรรม "
            f"({r['unknown_weight']:.1f}% ของพอร์ต) จึงถูกนับเป็นกลุ่มแยกเดี่ยว "
            "ซึ่งอาจทำให้การกระจุกตัวตามอุตสาหกรรมต่ำเกินจริง"
        )
    else:
        quality = (
            "หุ้นทุกตัวมีข้อมูลอุตสาหกรรม การจัดกลุ่มธีมจึงอ้างอิงจากชื่ออุตสาหกรรมที่ระบบมี "
            "ซึ่งเป็นการจัดกลุ่มแบบกว้าง ไม่ได้ดูธุรกิจจริงของแต่ละบริษัท"
        )
    if r.get("market_count", 0) == 0:
        quality += (
            " | ยังไม่มีข้อมูลตลาดจริง (beta / ความผันผวน / drawdown) "
            "ความอ่อนไหวต่อตลาดทั้งหมดจึงเป็นค่าประมาณจากอุตสาหกรรม"
        )
    else:
        quality += (
            f" | ข้อมูลตลาดจริง: beta {r['beta_count']}/{r['count']} ตัว "
            f"({r['beta_coverage']:.0f}% ของพอร์ต), "
            f"ความผันผวน/drawdown ครอบคลุม {r['vol_coverage']:.0f}% ของพอร์ต "
            "(จากราคาปิดรายวันย้อนหลังประมาณ 1 ปี)"
        )
        if r.get("missing_market"):
            quality += (
                f" | ไม่มีข้อมูลของ {', '.join(r['missing_market'])} "
                "จึงใช้ค่าประมาณแทน"
            )
    sections.append(("6) คุณภาพข้อมูลที่ใช้วิเคราะห์", quality))

    # 7) ลำดับสิ่งที่ควรพิจารณา
    action_map = {
        "stock": (
            f"ลดน้ำหนักของ {r['top_stock']['symbol']} หรือทยอยเพิ่มหุ้นตัวอื่น "
            f"ให้หุ้นแต่ละตัวไม่เกินราว {r['stock_cap']:.0f}%"
        ),
        "industry": (
            f"เพิ่มสินทรัพย์นอกกลุ่ม {r['top_industry']} "
            f"ให้อุตสาหกรรมเดียวไม่เกินราว {r['industry_cap']:.0f}%"
        ),
        "depth": (
            f"เพิ่มจำนวนหุ้นหรือปรับน้ำหนักให้ใกล้เคียงกันขึ้น "
            f"(จำนวนหุ้นที่แท้จริงตอนนี้ {r['effective_stocks']:.1f} ควรไปที่ 6-8)"
        ),
        "theme": (
            f"เพิ่มสินทรัพย์ที่ปัจจัยขับเคลื่อนต่างจากธีม \"{theme['theme']}\""
        ),
        "sens": "ผสมหุ้นที่ผันผวนต่ำกว่าตลาดบางส่วนเพื่อลดการแกว่งของพอร์ต",
    }
    actions = [
        f"{i}. {action_map[f['key']]}"
        for i, f in enumerate(
            [f for f in ranked if f["score"] >= 35][:3], start=1
        )
    ]
    if not actions:
        actions = ["ไม่มีองค์ประกอบใดสูงเด่น ควรเพียงติดตามน้ำหนักเมื่อราคาเปลี่ยน"]
    sections.append(("7) ลำดับสิ่งที่ควรพิจารณา", "\n".join(actions)))

    # 8) ข้อจำกัด
    sections.append((
        "8) สิ่งที่การวิเคราะห์นี้ยังไม่ครอบคลุม",
        "ระบบประเมินจากโครงสร้างพอร์ต (น้ำหนักและอุตสาหกรรม) ร่วมกับ beta ความผันผวน "
        "และ drawdown ย้อนหลังราว 1 ปีของแต่ละหุ้น (เท่าที่ดึงข้อมูลได้) ซึ่งเป็นอดีตและไม่รับประกัน "
        "อนาคต ความผันผวนเฉลี่ยถ่วงน้ำหนักเป็นเพียงค่าเฉลี่ย ไม่ใช่ความผันผวนของพอร์ตจริง "
        "เพราะยังไม่รวมค่าสหสัมพันธ์ระหว่างหุ้น นอกจากนี้ยังไม่รวมความเสี่ยงค่าเงิน "
        "(หากลงทุนหุ้นต่างประเทศด้วยเงินบาท) สภาพคล่อง ภาษีและค่าธรรมเนียม "
        "รวมถึงปัจจัยพื้นฐานของแต่ละบริษัท ผลนี้เป็นข้อมูลประกอบการตัดสินใจ "
        "ไม่ใช่คำแนะนำให้ซื้อหรือขายหุ้น",
    ))

    return sections


class AnimatedBanner(tk.Canvas):
    """แบนเนอร์หัวหน้าแบบแดชบอร์ดนักลงทุน: ชื่อหน้า + กราฟเส้นเคลื่อนไหว (ภาพประกอบ)"""

    def __init__(self, parent, title, subtitle, seed=1, tag="DASHBOARD", height=150):
        super().__init__(
            parent,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=THEME_COLORS["bg"]
        )
        self.title_text = title
        self.subtitle_text = subtitle
        self.tag_text = tag
        self.rng = random.Random(seed)
        self.count = 46
        level = 0.4
        self.values = []
        for _ in range(self.count):
            level = self._next_level(level)
            self.values.append(level)
        self.tick = 0
        self.reveal = 0.0
        self.region = None
        self.job = None
        self.size = (0, 0)
        self.bind("<Configure>", self._on_resize)
        self.bind("<Destroy>", self._on_destroy)
        self.job = self.after(60, self._animate)

    def _next_level(self, level):
        level += self.rng.uniform(-0.10, 0.12)
        return min(0.95, max(0.06, level))

    def _on_destroy(self, event):
        if event.widget is self and self.job is not None:
            try:
                self.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None

    def _on_resize(self, event):
        if event.width < 300 or event.height < 80:
            return
        if (event.width, event.height) == self.size:
            return
        self.size = (event.width, event.height)
        self._draw_static(event.width, event.height)
        self._draw_chart()

    def _draw_static(self, w, h):
        c = AUTH_COLORS
        self.delete("static")
        auth_rounded_rect(
            self, 2, 2, w - 2, h - 2, 24,
            fill=c["panel"], outline=c["panel_soft"], width=1, tags="static"
        )
        # แสงเรืองมุมซ้ายบนให้ดูมีมิติ
        for i in range(6):
            r = 150 - i * 22
            auth_rounded_rect(
                self, 2, 2, 2 + r * 1.9, 2 + r * 0.9, 24,
                fill=auth_blend(c["panel"], c["primary"], 0.05 + i * 0.012),
                outline="", tags="static"
            )
        self.create_text(
            36, h * 0.36, text=self.title_text, anchor="w", fill="#FFFFFF",
            font=("Tahoma", 24, "bold"), tags="static"
        )
        self.create_text(
            36, h * 0.36 + 40, text=self.subtitle_text, anchor="w", fill="#A9BAEB",
            font=("Tahoma", 11), tags="static"
        )
        chip_w = 34 + 8 * len(self.tag_text)
        auth_rounded_rect(
            self, 36, h - 50, 36 + chip_w, h - 22, 12,
            fill="#0B1744", outline=c["panel_soft"], width=1, tags="static"
        )
        self.create_text(
            36 + 28, h - 36, text=self.tag_text, anchor="w", fill="#DCE6FF",
            font=("Tahoma", 8, "bold"), tags="static"
        )
        x0, x1 = w * 0.50, w - 40
        y0, y1 = 26, h - 30
        self.region = (x0, y0, x1, y1)
        grid = auth_blend(c["panel"], c["panel_soft"], 0.8)
        for i in range(4):
            gy = y0 + (y1 - y0) * i / 3
            self.create_line(x0, gy, x1, gy, fill=grid, dash=(2, 5), tags="static")
        self.create_text(
            x1, h - 14, text="ภาพประกอบตัวอย่าง", anchor="e", fill="#6F83C0",
            font=("Tahoma", 8), tags="static"
        )

    def _draw_chart(self):
        self.delete("chart")
        if self.region is None:
            return
        c = AUTH_COLORS
        x0, y0, x1, y1 = self.region
        h = self.size[1]

        if self.reveal < self.count:
            vals = self.values[:max(2, int(self.reveal))]
        else:
            vals = self.values

        pts = []
        for i, v in enumerate(vals):
            x = x0 + (x1 - x0) * i / (self.count - 1)
            y = y1 - v * (y1 - y0)
            pts.extend((x, y))
        if len(pts) < 4:
            return

        area = pts + [pts[-2], y1, pts[0], y1]
        self.create_polygon(
            area, fill=auth_blend(c["panel"], c["primary"], 0.22),
            outline="", tags="chart"
        )
        self.create_line(
            pts, fill=auth_blend(c["panel"], c["cyan"], 0.22), width=8,
            smooth=True, capstyle="round", joinstyle="round", tags="chart"
        )
        self.create_line(
            pts, fill=c["cyan"], width=2.5, smooth=True,
            capstyle="round", joinstyle="round", tags="chart"
        )
        ex, ey = pts[-2], pts[-1]
        phase = (self.tick % 36) / 36
        ring = 6 + phase * 14
        self.create_oval(
            ex - ring, ey - ring, ex + ring, ey + ring, fill="",
            outline=auth_blend(c["cyan"], c["panel"], phase), width=2, tags="chart"
        )
        self.create_oval(
            ex - 5, ey - 5, ex + 5, ey + 5, fill="#FFFFFF",
            outline=c["cyan"], width=2, tags="chart"
        )
        # จุดเต้นในแถบป้ายชื่อ
        dot = 3 + 2 * math.sin(self.tick / 6)
        self.create_oval(
            36 + 14 - dot, h - 36 - dot, 36 + 14 + dot, h - 36 + dot,
            fill=c["green"], outline="", tags="chart"
        )

    def _animate(self):
        self.job = None
        try:
            if not self.winfo_exists():
                return
            self.tick += 1
            if self.reveal < self.count:
                self.reveal = min(self.count, self.reveal + 0.9)
            elif self.tick % 8 == 0:
                self.values.append(self._next_level(self.values[-1]))
                self.values.pop(0)
            if self.winfo_ismapped():
                self._draw_chart()
            self.job = self.after(45, self._animate)
        except tk.TclError:
            self.job = None


class StockDashboard(tk.Canvas):
    """การ์ดราคา + แถบช่วงราคาวันนี้ + มาตรวัดตัวชี้วัดพื้นฐาน (เคลื่อนไหวตอนแสดงผล)"""

    def __init__(self, parent, stock, score):
        super().__init__(
            parent,
            height=250,
            highlightthickness=0,
            bd=0,
            bg=THEME_COLORS["bg"]
        )
        self.stock = stock
        self.score = score
        self.progress = 0.0
        self.job = None
        self.bind("<Configure>", lambda event: self.redraw())
        self.bind("<Destroy>", self._on_destroy)
        self.job = self.after(80, self._step)

    def _on_destroy(self, event):
        if event.widget is self and self.job is not None:
            try:
                self.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None

    def _step(self):
        self.job = None
        try:
            if not self.winfo_exists():
                return
            if self.progress < 1.0:
                self.progress = min(1.0, self.progress + 0.05)
                self.redraw()
                self.job = self.after(30, self._step)
        except tk.TclError:
            self.job = None

    def redraw(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 300:
            return
        c = AUTH_COLORS
        s = self.stock
        self.delete("all")
        ease = 1 - (1 - self.progress) ** 3

        price = _to_float(s.get("price"))
        change = _to_float(s.get("change"))
        pct = _to_float(s.get("change_percent"))
        high = _to_float(s.get("high"))
        low = _to_float(s.get("low"))

        # ---------- การ์ดราคา ----------
        card_w = int(min(w * 0.48, 560))
        auth_rounded_rect(
            self, 2, 2, card_w, h - 2, 22,
            fill=c["card"], outline=c["card_border"], width=1
        )
        self.create_text(
            26, 30, text=str(s.get("symbol", "")), anchor="w",
            fill=c["cyan"], font=("Tahoma", 12, "bold")
        )
        name = str(s.get("company_name") or "-")
        if len(name) > 38:
            name = name[:37] + "…"
        self.create_text(
            26, 52, text=name, anchor="w", fill=c["muted"], font=("Tahoma", 9)
        )
        if price is not None:
            self.create_text(
                26, 100, text=f"{price * ease:,.2f}", anchor="w",
                fill=c["text"], font=("Tahoma", 32, "bold")
            )
        else:
            self.create_text(
                26, 100, text="-", anchor="w", fill=c["muted"],
                font=("Tahoma", 32, "bold")
            )

        if change is not None:
            up = change >= 0
            color = c["green"] if up else c["red"]
            pct_text = f" ({abs(pct):.2f}%)" if pct is not None else ""
            chip_text = f"{'▲' if up else '▼'} {abs(change):,.2f}{pct_text}"
            chip_w = 30 + 9 * len(chip_text)
            auth_rounded_rect(
                self, 26, 128, 26 + chip_w, 156, 13,
                fill=auth_blend(c["card"], color, 0.18),
                outline=auth_blend(c["card"], color, 0.45)
            )
            self.create_text(
                26 + chip_w / 2, 142, text=chip_text, fill=color,
                font=("Tahoma", 10, "bold")
            )

        bx0, bx1, by = 26, card_w - 26, h - 52
        self.create_text(
            bx0, by - 26, text="ช่วงราคาวันนี้", anchor="w",
            fill=c["muted"], font=("Tahoma", 9, "bold")
        )
        if (
            price is not None and high is not None
            and low is not None and high > low
        ):
            frac = max(0.0, min(1.0, (price - low) / (high - low)))
            self.create_line(
                bx0, by, bx1, by, fill=c["field_border"], width=8, capstyle="round"
            )
            px = bx0 + (bx1 - bx0) * frac * ease
            if px > bx0 + 1:
                self.create_line(
                    bx0, by, px, by, fill=c["cyan"], width=8, capstyle="round"
                )
            self.create_oval(
                px - 9, by - 9, px + 9, by + 9,
                fill="#FFFFFF", outline=c["cyan"], width=3
            )
            self.create_text(
                bx0, by + 20, text=f"ต่ำ {low:,.2f}", anchor="w",
                fill=c["muted"], font=("Tahoma", 9)
            )
            self.create_text(
                bx1, by + 20, text=f"สูง {high:,.2f}", anchor="e",
                fill=c["muted"], font=("Tahoma", 9)
            )
        else:
            self.create_text(
                bx0, by, text="ไม่มีข้อมูลช่วงราคา", anchor="w",
                fill=c["muted"], font=("Tahoma", 10)
            )

        # ---------- มาตรวัดตัวชี้วัด ----------
        rx0, rx1 = card_w + 14, w - 2
        auth_rounded_rect(
            self, rx0, 2, rx1, h - 2, 22,
            fill=c["card"], outline=c["card_border"], width=1
        )
        self.create_text(
            rx0 + 24, 30, text="ตัวชี้วัดพื้นฐาน", anchor="w",
            fill=c["muted"], font=("Tahoma", 10, "bold")
        )

        gauges = [
            ("ROE", s.get("roe"), 40, "%"),
            ("ROA", s.get("roa"), 20, "%"),
            ("Net Margin", s.get("net_margin"), 40, "%"),
            ("คะแนนรวม", self.score, 100, ""),
        ]
        slot = (rx1 - rx0 - 20) / 4
        radius = max(22, min(46, slot / 2 - 14))
        cy = h / 2 + 14
        for index, (label, value, maximum, unit) in enumerate(gauges):
            cx = rx0 + 10 + slot * (index + 0.5)
            self.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                outline=c["field_border"], width=9
            )
            number = _to_float(value)
            if number is None:
                text = "-"
            else:
                frac = max(0.0, min(1.0, number / maximum))
                if number <= 0:
                    color = c["red"]
                elif frac >= 0.5:
                    color = c["green"]
                elif frac >= 0.25:
                    color = c["orange"]
                else:
                    color = c["red"]
                extent = -min(359.9, 360 * frac * ease)
                if abs(extent) > 0.5:
                    self.create_arc(
                        cx - radius, cy - radius, cx + radius, cy + radius,
                        start=90, extent=extent, style="arc",
                        outline=color, width=9
                    )
                if unit == "%":
                    text = f"{number * ease:.1f}%"
                else:
                    text = f"{number * ease:.0f}"
            self.create_text(
                cx, cy, text=text, fill=c["text"],
                font=("Tahoma", 11 if radius >= 36 else 9, "bold")
            )
            self.create_text(
                cx, cy + radius + 24, text=label, fill=c["muted"],
                font=("Tahoma", 9)
            )


class RiskGauge(tk.Canvas):
    """มาตรวัดความเสี่ยงครึ่งวงกลม + สรุปภาษาง่าย ๆ + ปัจจัยหลัก 3 ข้อ"""

    ZONES = [
        (0, 35, "green"),
        (35, 55, "cyan"),
        (55, 75, "orange"),
        (75, 100, "red"),
    ]

    def __init__(self, parent):
        super().__init__(
            parent,
            height=300,
            highlightthickness=0,
            bd=0,
            bg=THEME_COLORS["bg"]
        )
        self.score = 0.0
        self.target = 0.0
        self.level = "ยังไม่มีข้อมูล"
        self.color = THEME_COLORS["muted"]
        self.headline = "เพิ่มหุ้นเข้าพอร์ตเพื่อเริ่มวิเคราะห์ความเสี่ยง"
        self.factors = []
        self.job = None
        self.bind("<Configure>", lambda event: self.redraw())
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        if event.widget is self and self.job is not None:
            try:
                self.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None

    def set_empty(self):
        self.target = 0.0
        self.level = "ยังไม่มีข้อมูล"
        self.color = THEME_COLORS["muted"]
        self.headline = "เพิ่มหุ้นเข้าพอร์ตเพื่อเริ่มวิเคราะห์ความเสี่ยง"
        self.factors = []
        self._kick()

    def set_result(self, score, level, color, headline, factors):
        self.target = max(0.0, min(100.0, float(score)))
        self.level = level
        self.color = color
        self.headline = headline
        self.factors = list(factors)
        self._kick()

    def _kick(self):
        self.redraw()
        if self.job is None:
            self.job = self.after(20, self._step)

    def _step(self):
        self.job = None
        try:
            if not self.winfo_exists():
                return
            diff = self.target - self.score
            if abs(diff) < 0.4:
                self.score = self.target
            else:
                self.score += diff * 0.2
            self.redraw()
            if self.score != self.target:
                self.job = self.after(20, self._step)
        except tk.TclError:
            self.job = None

    def redraw(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 400 or h < 200:
            return
        c = AUTH_COLORS
        self.delete("all")

        auth_rounded_rect(
            self, 2, 2, w - 2, h - 2, 24,
            fill=c["card"], outline=c["card_border"], width=1
        )

        # ---------- มาตรวัดครึ่งวงกลม ----------
        gauge_w = min(int(w * 0.42), 400)
        cx = 30 + gauge_w / 2
        radius = max(60, min(gauge_w / 2 - 16, h - 130))
        cy = h - 70
        box = (cx - radius, cy - radius, cx + radius, cy + radius)

        for start, end, key in self.ZONES:
            self.create_arc(
                *box,
                start=180 - 1.8 * start,
                extent=-1.8 * (end - start) + 0.6,
                style="arc",
                outline=auth_blend(c["card"], c[key], 0.28),
                width=20
            )

        for start, end, key in self.ZONES:
            if self.score > start:
                stop = min(self.score, end)
                self.create_arc(
                    *box,
                    start=180 - 1.8 * start,
                    extent=-1.8 * (stop - start),
                    style="arc",
                    outline=c[key],
                    width=20
                )

        angle = math.radians(180 - 1.8 * self.score)
        kx = cx + radius * math.cos(angle)
        ky = cy - radius * math.sin(angle)
        self.create_oval(
            kx - 11, ky - 11, kx + 11, ky + 11,
            fill="#FFFFFF", outline=self.color, width=4
        )

        self.create_text(
            cx, cy - 26, text=f"{self.score:.0f}",
            fill=c["text"], font=("Tahoma", 40, "bold")
        )
        self.create_text(
            cx, cy + 8, text="จาก 100 คะแนนความเสี่ยง",
            fill=c["muted"], font=("Tahoma", 10)
        )
        self.create_text(
            cx - radius, cy + 26, text="ต่ำ",
            fill=c["green"], font=("Tahoma", 10, "bold")
        )
        self.create_text(
            cx + radius, cy + 26, text="สูง",
            fill=c["red"], font=("Tahoma", 10, "bold")
        )

        # ---------- ข้อความสรุปฝั่งขวา ----------
        x0 = 30 + gauge_w + 40
        avail = w - x0 - 36
        if avail < 220:
            return

        self.create_text(
            x0, 34, text="ระดับความเสี่ยงของพอร์ต", anchor="w",
            fill=c["muted"], font=("Tahoma", 10, "bold")
        )
        self.create_text(
            x0, 70, text=self.level, anchor="w",
            fill=self.color, font=("Tahoma", 28, "bold")
        )
        self.create_text(
            x0, 102, text=self.headline, anchor="nw",
            fill="#DCE6FF", font=("Tahoma", 11), width=avail
        )

        if not self.factors:
            return

        self.create_text(
            x0, 190, text="ปัจจัยที่ดันความเสี่ยงมากที่สุด", anchor="w",
            fill=c["muted"], font=("Tahoma", 9, "bold")
        )

        label_w = min(240, int(avail * 0.45))
        bar_x0 = x0 + label_w
        bar_x1 = x0 + avail - 50
        for index, (name, score) in enumerate(self.factors[:3]):
            y = 214 + index * 26
            if score >= 60:
                color = c["red"]
            elif score >= 35:
                color = c["orange"]
            else:
                color = c["green"]

            shown = name if len(name) <= 26 else name[:25] + "…"
            self.create_text(
                x0, y, text=shown, anchor="w",
                fill=c["text"], font=("Tahoma", 10)
            )
            auth_rounded_rect(
                self, bar_x0, y - 6, bar_x1, y + 6, 6,
                fill=c["field"], outline=""
            )
            fill_w = (bar_x1 - bar_x0) * score / 100.0
            if fill_w >= 12:
                auth_rounded_rect(
                    self, bar_x0, y - 6, bar_x0 + fill_w, y + 6, 6,
                    fill=color, outline=""
                )
            self.create_text(
                x0 + avail, y, text=f"{score:.0f}", anchor="e",
                fill=color, font=("Tahoma", 10, "bold")
            )


class StockApp:
    def __init__(self, root, user_id, username):
        self.root = root
        self.user_id = user_id
        self.username = username
        self.root.title(f"รู้เรื่องหุ้น - {self.username}")
        self.root.geometry("1150x850")
        self.root.minsize(1000, 700)

        self.portfolio = []
        self.selected_trade_record_id = None

        # ข้อมูลตลาดจริงสำหรับวิเคราะห์ความเสี่ยง (beta / ความผันผวน / drawdown)
        self.market_data = {}
        self._market_queue = queue.Queue()
        self._market_attempt = {}
        self._market_loading = False
        self._market_total = 0
        self._market_done = 0
        self._market_changed = False

        self.create_style()
        self.create_notebook()
        self.create_stock_analysis_page()
        self.create_portfolio_risk_page()
        self.create_trade_calendar_page()
        self.create_account_bar()

        self.create_database()
        self.load_market_cache()
        self.load_portfolio()
        self.refresh_trade_calendar()

    # ==================================================
    # ACCOUNT
    # ==================================================
    def create_account_bar(self):
        bar = ttk.Frame(self.root)
        bar.place(relx=1.0, x=-12, y=8, anchor="ne")
        ttk.Label(bar, text=f"ผู้ใช้: {self.username}").pack(side="left", padx=(0, 8))
        ttk.Button(bar, text="ออกจากระบบ", command=self.logout).pack(side="left")

    def logout(self):
        if not messagebox.askyesno("ออกจากระบบ", "ต้องการออกจากระบบหรือไม่?"):
            return
        # ใช้หน้าต่างเดิม ล้างหน้าจอเก่าออกก่อน แล้วสร้างหน้าเข้าสู่ระบบใหม่
        reset_root_window(self.root)
        LoginWindow(self.root)

    # ==================================================
    # DATABASE
    # ==================================================
    def connect_database(self):
        return sqlite3.connect(database_path())

    def create_database(self):
        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    company TEXT,
                    amount REAL NOT NULL,
                    industry TEXT,
                    UNIQUE(user_id, symbol),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    trade_date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    note TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_exchange_rates (
                    year_month TEXT PRIMARY KEY,
                    usd_thb REAL NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_risk_cache (
                    symbol TEXT PRIMARY KEY,
                    beta REAL,
                    beta_source TEXT,
                    volatility REAL,
                    max_drawdown REAL,
                    history_days INTEGER,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("PRAGMA table_info(portfolio_holdings)")
            portfolio_columns = {row[1] for row in cursor.fetchall()}
            if "user_id" not in portfolio_columns:
                cursor.execute("ALTER TABLE portfolio_holdings ADD COLUMN user_id INTEGER")

            cursor.execute("PRAGMA table_info(trade_transactions)")
            trade_columns = {row[1] for row in cursor.fetchall()}
            if "user_id" not in trade_columns:
                cursor.execute("ALTER TABLE trade_transactions ADD COLUMN user_id INTEGER")

            cursor.execute("PRAGMA index_list(portfolio_holdings)")
            portfolio_indexes = cursor.fetchall()
            has_symbol_only_unique = False
            for index_row in portfolio_indexes:
                index_name = index_row[1]
                is_unique = index_row[2]
                if is_unique:
                    cursor.execute(f"PRAGMA index_info({index_name})")
                    index_columns = [row[2] for row in cursor.fetchall()]
                    if index_columns == ["symbol"]:
                        has_symbol_only_unique = True
                        break

            if has_symbol_only_unique:
                cursor.execute("ALTER TABLE portfolio_holdings RENAME TO portfolio_holdings_old")
                cursor.execute("""
                    CREATE TABLE portfolio_holdings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        company TEXT,
                        amount REAL NOT NULL,
                        industry TEXT,
                        UNIQUE(user_id, symbol),
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
                cursor.execute("""
                    INSERT INTO portfolio_holdings
                    (id, user_id, symbol, company, amount, industry)
                    SELECT id, ?, symbol, company, amount, industry
                    FROM portfolio_holdings_old
                """, (self.user_id,))
                cursor.execute("DROP TABLE portfolio_holdings_old")

            cursor.execute(
                "UPDATE trade_transactions SET user_id = ? WHERE user_id IS NULL",
                (self.user_id,)
            )

            connection.commit()
            connection.close()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถสร้างฐานข้อมูลได้\n{error}"
            )

    # ==================================================
    # MARKET DATA (beta / ความผันผวน / drawdown ของหุ้นจริง)
    # ดึงใน thread แยกเพื่อไม่ให้หน้าจอค้าง แล้วแคชลง SQLite 24 ชั่วโมง
    # ==================================================
    MARKET_CACHE_HOURS = 24
    MARKET_RETRY_SECONDS = 600

    def load_market_cache(self):
        try:
            connection = self.connect_database()
            rows = connection.execute(
                """
                SELECT symbol, beta, beta_source, volatility,
                       max_drawdown, history_days, updated_at
                FROM stock_risk_cache
                """
            ).fetchall()
            connection.close()
        except sqlite3.Error:
            return

        for row in rows:
            self.market_data[str(row[0]).upper()] = {
                "beta": row[1],
                "beta_source": row[2],
                "volatility": row[3],
                "max_drawdown": row[4],
                "history_days": row[5],
                "updated_at": row[6],
            }

    def _market_is_fresh(self, entry):
        try:
            updated = datetime.strptime(entry["updated_at"], "%Y-%m-%d %H:%M:%S")
        except (KeyError, TypeError, ValueError):
            return False
        return datetime.now() - updated < timedelta(hours=self.MARKET_CACHE_HOURS)

    def _store_market_result(self, symbol, result):
        entry = {
            "beta": result.get("beta"),
            "beta_source": result.get("beta_source"),
            "volatility": result.get("volatility"),
            "max_drawdown": result.get("max_drawdown"),
            "history_days": result.get("history_days") or 0,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.market_data[symbol] = entry

        try:
            connection = self.connect_database()
            connection.execute(
                """
                INSERT INTO stock_risk_cache
                (symbol, beta, beta_source, volatility, max_drawdown,
                 history_days, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    beta = excluded.beta,
                    beta_source = excluded.beta_source,
                    volatility = excluded.volatility,
                    max_drawdown = excluded.max_drawdown,
                    history_days = excluded.history_days,
                    updated_at = excluded.updated_at
                """,
                (
                    symbol, entry["beta"], entry["beta_source"],
                    entry["volatility"], entry["max_drawdown"],
                    entry["history_days"], entry["updated_at"],
                )
            )
            connection.commit()
            connection.close()
        except sqlite3.Error:
            pass

    def request_market_data(self, force=False):
        """เริ่มดึงข้อมูลตลาดของหุ้นที่ยังไม่มี/หมดอายุ (ไม่ทำอะไรถ้ากำลังโหลดอยู่)"""
        if self._market_loading:
            return

        now = time.time()
        todo = []

        for item in self.portfolio:
            symbol = item["symbol"]
            entry = self.market_data.get(symbol)

            if not force:
                if entry and self._market_is_fresh(entry):
                    continue
                if now - self._market_attempt.get(symbol, 0) < self.MARKET_RETRY_SECONDS:
                    continue

            todo.append(symbol)

        if not todo:
            self.update_market_status()
            return

        self._market_loading = True
        self._market_total = len(todo)
        self._market_done = 0
        self._market_changed = False
        self.update_market_status()

        threading.Thread(
            target=self._market_worker,
            args=(todo,),
            daemon=True
        ).start()
        self.root.after(300, self._poll_market_queue)

    def _market_worker(self, symbols):
        """ทำงานใน thread แยก: ห้ามแตะ UI หรือฐานข้อมูลที่นี่ ส่งผลผ่าน queue เท่านั้น"""
        for symbol in symbols:
            try:
                result = get_risk_market_data(symbol)
            except Exception as error:
                result = {"symbol": symbol, "error": str(error)}

            self._market_queue.put(("result", symbol, result))
            time.sleep(0.2)

        self._market_queue.put(("done", None, None))

    def _poll_market_queue(self):
        finished = False

        try:
            while True:
                kind, symbol, result = self._market_queue.get_nowait()

                if kind == "result":
                    self._market_done += 1
                    self._market_attempt[symbol] = time.time()

                    if (
                        result.get("beta") is not None
                        or result.get("volatility") is not None
                    ):
                        self._store_market_result(symbol, result)
                        self._market_changed = True
                else:
                    finished = True

        except queue.Empty:
            pass

        try:
            if finished:
                self._market_loading = False

                if self._market_changed:
                    self._market_changed = False
                    self.analyze_portfolio_risk(request_market=False)

                self.update_market_status()
            else:
                self.update_market_status()
                self.root.after(300, self._poll_market_queue)

        except tk.TclError:
            # หน้าต่างถูกปิด (เช่น ออกจากระบบ) ระหว่างที่ยังโหลดอยู่
            self._market_loading = False

    def update_market_status(self):
        if not hasattr(self, "market_status_label"):
            return

        if self._market_loading:
            text = (
                f"กำลังดึงข้อมูลตลาดจริง {self._market_done}/{self._market_total} ตัว "
                "(beta / ความผันผวน / drawdown)..."
            )
            color = THEME_COLORS["cyan"]
        elif not self.portfolio:
            text = "ข้อมูลตลาดจริง: เพิ่มหุ้นเข้าพอร์ตเพื่อดึงข้อมูล"
            color = THEME_COLORS["muted"]
        else:
            symbols = [item["symbol"] for item in self.portfolio]
            have = [
                s for s in symbols
                if (self.market_data.get(s) or {}).get("beta") is not None
                or (self.market_data.get(s) or {}).get("volatility") is not None
            ]
            missing = [s for s in symbols if s not in have]
            updated = [
                self.market_data[s]["updated_at"] for s in have
                if self.market_data[s].get("updated_at")
            ]

            text = f"ข้อมูลตลาดจริง {len(have)}/{len(symbols)} ตัว"
            if updated:
                text += f" (อัปเดตล่าสุด {max(updated)[:16]})"
            if missing:
                text += f" | ไม่มีข้อมูล ใช้ค่าประมาณ: {', '.join(missing)}"
                color = THEME_COLORS["warning"]
            else:
                color = THEME_COLORS["positive"]

        self.market_status_label.config(text=text, foreground=color)

    def refresh_market_data(self):
        if self._market_loading:
            return
        if not self.portfolio:
            messagebox.showinfo("แจ้งเตือน", "เพิ่มหุ้นเข้าพอร์ตก่อน")
            return
        self.request_market_data(force=True)

    def save_stock_to_database(self, stock):
        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO portfolio_holdings
                (user_id, symbol, company, amount, industry)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.user_id,
                stock["symbol"],
                stock["company"],
                stock["amount"],
                stock["industry"]
            ))

            connection.commit()
            connection.close()

            return True

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถบันทึกข้อมูลได้\n{error}"
            )

            return False

    def delete_stock_from_database(self, symbol):
        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute("""
                DELETE FROM portfolio_holdings
                WHERE user_id = ? AND symbol = ?
            """, (self.user_id, symbol))

            connection.commit()
            connection.close()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถลบข้อมูลได้\n{error}"
            )

    def clear_database(self):
        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute(
                "DELETE FROM portfolio_holdings WHERE user_id = ?",
                (self.user_id,)
            )

            connection.commit()
            connection.close()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถล้างข้อมูลได้\n{error}"
            )

    def load_portfolio(self):
        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT symbol, company, amount, industry
                FROM portfolio_holdings
                WHERE user_id = ?
                ORDER BY id
            """, (self.user_id,))

            rows = cursor.fetchall()

            connection.close()

            self.portfolio.clear()

            # --------------------------------------------------
            # FALLBACK สำหรับข้อมูลเก่าที่เคยบันทึกเป็น "-" / "ไม่ระบุ"
            # เช่น RKLB ที่ถูกเพิ่มเข้าพอร์ตก่อน Finnhub ส่ง profile ได้
            # --------------------------------------------------
            fallback_stocks = {
                "AAPL": {"company": "Apple Inc.", "industry": "Technology"},
                "AMD": {"company": "Advanced Micro Devices", "industry": "Semiconductors"},
                "AMZN": {"company": "Amazon.com Inc.", "industry": "Retail"},
                "AVGO": {"company": "Broadcom Inc.", "industry": "Semiconductors"},
                "GOOGL": {"company": "Alphabet Inc.", "industry": "Media"},
                "GOOG": {"company": "Alphabet Inc.", "industry": "Media"},
                "META": {"company": "Meta Platforms Inc.", "industry": "Media"},
                "MSFT": {"company": "Microsoft Corp.", "industry": "Technology"},
                "MU": {"company": "Micron Technology Inc.", "industry": "Semiconductors"},
                "NBIS": {"company": "Nebius Group N.V.", "industry": "Technology"},
                "NVDA": {"company": "NVIDIA Corp.", "industry": "Semiconductors"},
                "RKLB": {"company": "Rocket Lab Corporation", "industry": "Aerospace & Defense"},
                "SMCI": {"company": "Super Micro Computer Inc.", "industry": "Technology"},
                "TSLA": {"company": "Tesla Inc.", "industry": "Automobiles"},
                "VRT": {"company": "Vertiv Holdings Co.", "industry": "Electrical Equipment"},
            }

            connection = self.connect_database()
            update_cursor = connection.cursor()

            for row in rows:

                symbol = str(row[0]).upper().strip()
                fallback = fallback_stocks.get(symbol, {})

                company = row[1]
                industry = row[3]

                if not company or company == "-":
                    company = fallback.get("company") or company or "-"

                if not industry or industry == "ไม่ระบุ":
                    industry = fallback.get("industry") or industry or "ไม่ระบุ"

                item = {
                    "symbol": symbol,
                    "company": company,
                    "amount": row[2],
                    "industry": industry
                }

                self.portfolio.append(item)

                # อัปเดตข้อมูลเดิมในฐานข้อมูลด้วย เพื่อไม่ให้กลับมาเป็น "-" อีก
                if company != row[1] or industry != row[3]:
                    update_cursor.execute(
                        """
                        UPDATE portfolio_holdings
                        SET company = ?, industry = ?
                        WHERE user_id = ? AND symbol = ?
                        """,
                        (company, industry, self.user_id, symbol)
                    )

            connection.commit()
            connection.close()

            self.update_portfolio()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถโหลดข้อมูลพอร์ตได้\n{error}"
            )

    # ==================================================
    # STYLE
    # ==================================================
    def create_style(self):
        """ตกแต่งหน้าตาโปรแกรมเท่านั้น ไม่เปลี่ยนการทำงานของฟีเจอร์เดิม"""
        style = ttk.Style()

        # โทนสีหลัก: พื้นหลังเทาอ่อน + น้ำเงินแบบแดชบอร์ดการเงิน
        self.ui_colors = {
            "background": "#0A1124",
            "surface": "#0F1830",
            "primary": "#4C7DFF",
            "primary_active": "#3B66DD",
            "text": "#E8EEFC",
            "muted": "#8D9BBC",
            "border": "#26365C",
            "selected": "#1C3485",
            "positive": "#34D399",
            "negative": "#F87171",
        }
        self.root.configure(bg=self.ui_colors["background"])

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # พื้นฐานของทุกพื้นที่
        style.configure("TFrame", background=self.ui_colors["background"])
        style.configure(
            "TLabel",
            background=self.ui_colors["background"],
            foreground=self.ui_colors["text"],
            font=("Tahoma", 10)
        )
        style.configure(
            "Title.TLabel",
            background=self.ui_colors["background"],
            foreground=self.ui_colors["text"],
            font=("Tahoma", 25, "bold")
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.ui_colors["background"],
            foreground=self.ui_colors["muted"],
            font=("Tahoma", 12)
        )
        style.configure(
            "Normal.TLabel",
            background=self.ui_colors["background"],
            foreground=self.ui_colors["text"],
            font=("Tahoma", 11)
        )

        # ปุ่มหลักให้ดูชัดและมีสถานะเมื่อชี้เมาส์
        style.configure(
            "TButton",
            font=("Tahoma", 10, "bold"),
            padding=(12, 7),
            background=self.ui_colors["surface"],
            foreground=self.ui_colors["text"],
            bordercolor=self.ui_colors["border"]
        )
        style.map(
            "TButton",
            background=[("active", self.ui_colors["selected"]), ("pressed", self.ui_colors["primary"])],
            foreground=[("pressed", "#FFFFFF")]
        )
        style.configure(
            "Primary.TButton",
            background=self.ui_colors["primary"],
            foreground="#FFFFFF",
            padding=(14, 8)
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.ui_colors["primary_active"]), ("pressed", self.ui_colors["primary_active"])],
            foreground=[("active", "#FFFFFF"), ("pressed", "#FFFFFF")]
        )

        # แถบเมนูด้านบน
        style.configure(
            "TNotebook",
            background=self.ui_colors["background"],
            borderwidth=0,
            tabmargins=(3, 5, 3, 0)
        )
        style.configure(
            "TNotebook.Tab",
            font=("Tahoma", 10, "bold"),
            padding=(16, 10),
            background="#E7EDF7",
            foreground=self.ui_colors["muted"]
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.ui_colors["primary"])],
            foreground=[("selected", "#FFFFFF")]
        )

        # ช่องกรอกข้อมูล
        style.configure(
            "TEntry",
            padding=7,
            fieldbackground=self.ui_colors["surface"],
            foreground=self.ui_colors["text"]
        )
        style.configure(
            "TCombobox",
            padding=6,
            fieldbackground=self.ui_colors["surface"],
            foreground=self.ui_colors["text"]
        )

        # ตารางข้อมูลหุ้นและพอร์ต
        style.configure(
            "Treeview",
            font=("Tahoma", 10),
            rowheight=31,
            background=self.ui_colors["surface"],
            fieldbackground=self.ui_colors["surface"],
            foreground=self.ui_colors["text"],
            bordercolor=self.ui_colors["border"],
            borderwidth=1
        )
        style.configure(
            "Treeview.Heading",
            font=("Tahoma", 10, "bold"),
            padding=(8, 8),
            background="#E7EDF7",
            foreground=self.ui_colors["text"]
        )
        style.map(
            "Treeview",
            background=[("selected", self.ui_colors["selected"])],
            foreground=[("selected", self.ui_colors["text"])]
        )
        style.configure(
            "Vertical.TScrollbar",
            background="#D7E0EF",
            troughcolor=self.ui_colors["background"],
            borderwidth=0,
            arrowsize=14
        )

        apply_ui_theme(self.root, self.ui_colors)

    # ==================================================
    # NOTEBOOK
    # ==================================================
    def create_notebook(self):

        self.notebook = ttk.Notebook(self.root)

        self.notebook.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.stock_page = ttk.Frame(
            self.notebook
        )

        self.risk_page = ttk.Frame(
            self.notebook
        )

        self.trade_page = ttk.Frame(
            self.notebook
        )

        self.notebook.add(
            self.stock_page,
            text="วิเคราะห์หุ้น"
        )

        self.notebook.add(
            self.risk_page,
            text="วิเคราะห์ความเสี่ยงพอร์ต"
        )

        self.notebook.add(
            self.trade_page,
            text="บันทึกกำไรขาดทุน"
        )

    # ==================================================
    # PAGE 1 : STOCK ANALYSIS
    # ==================================================
    def create_stock_analysis_page(self):

        # พื้นที่เลื่อนขึ้นลงสำหรับหน้าวิเคราะห์หุ้น
        scroll_canvas = tk.Canvas(
            self.stock_page,
            background=THEME_COLORS["bg"],
            highlightthickness=0,
            borderwidth=0
        )
        scroll_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            self.stock_page,
            orient="vertical",
            command=scroll_canvas.yview
        )
        scrollbar.pack(side="right", fill="y")

        stock_content = ttk.Frame(scroll_canvas)
        stock_window = scroll_canvas.create_window(
            (0, 0),
            window=stock_content,
            anchor="nw"
        )

        scroll_canvas.configure(yscrollcommand=scrollbar.set)

        def update_scroll_region(event=None):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        def resize_content(event):
            scroll_canvas.itemconfig(stock_window, width=event.width)

        stock_content.bind("<Configure>", update_scroll_region)
        scroll_canvas.bind("<Configure>", resize_content)

        def is_stock_tab_active():
            try:
                selected = self.notebook.select()
                return self.notebook.tab(selected, "text") == "วิเคราะห์หุ้น"
            except tk.TclError:
                return False

        def scroll_with_mouse(event):
            if is_stock_tab_active() and event.delta != 0:
                scroll_canvas.yview_scroll(int(-event.delta / 120), "units")

        def scroll_with_mouse_linux_up(event):
            if is_stock_tab_active():
                scroll_canvas.yview_scroll(-1, "units")

        def scroll_with_mouse_linux_down(event):
            if is_stock_tab_active():
                scroll_canvas.yview_scroll(1, "units")

        # ลูกกลิ้งเมาส์ทำงานได้แม้อยู่บน Label, Entry, Button หรือพื้นที่ด้านในหน้า
        scroll_canvas.bind_all("<MouseWheel>", scroll_with_mouse)
        scroll_canvas.bind_all("<Button-4>", scroll_with_mouse_linux_up)
        scroll_canvas.bind_all("<Button-5>", scroll_with_mouse_linux_down)

        self.stock_page = stock_content

        self.stock_banner = AnimatedBanner(
            self.stock_page,
            "วิเคราะห์หุ้น",
            "ดูราคา ตัวชี้วัดพื้นฐาน และคะแนนภาพรวมของหุ้นในที่เดียว",
            seed=11,
            tag="STOCK ANALYSIS"
        )
        self.stock_banner.pack(fill="x", padx=30, pady=(22, 12))

        # -----------------------------
        # SEARCH
        # -----------------------------
        search_frame = ttk.Frame(self.stock_page)
        search_frame.pack(pady=10)

        ttk.Label(
            search_frame,
            text="ชื่อหุ้น",
            style="Normal.TLabel"
        ).grid(row=0, column=0, padx=5)

        self.stock_symbol_entry = ttk.Entry(
            search_frame,
            width=20,
            font=("Tahoma", 12)
        )
        self.stock_symbol_entry.grid(row=0, column=1, padx=5)

        search_button = ttk.Button(
            search_frame,
            text="วิเคราะห์หุ้น",
            command=self.search_stock
        )
        search_button.grid(row=0, column=2, padx=5)

        # -----------------------------
        # RESULT
        # -----------------------------
        self.stock_result_frame = ttk.Frame(self.stock_page)
        self.stock_result_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=20
        )

        self.stock_info_label = ttk.Label(
            self.stock_result_frame,
            text="กรอกชื่อหุ้น เช่น NVDA, AAPL, GOOGL",
            style="Normal.TLabel",
            justify="left"
        )
        self.stock_info_label.pack(anchor="w", pady=10)

    # ==================================================
    # SEARCH STOCK
    # ==================================================
    def search_stock(self):

        symbol = (
            self.stock_symbol_entry
            .get()
            .strip()
            .upper()
        )

        if symbol == "":
            messagebox.showwarning(
                "แจ้งเตือน",
                "กรุณากรอกชื่อหุ้น"
            )
            return

        stock = get_stock_data(symbol)

        # แยกกรณี API มีปัญหาออกจากกรณีไม่พบ Symbol
        if isinstance(stock, dict) and stock.get("_api_error"):
            messagebox.showerror(
                "ไม่สามารถเชื่อมต่อข้อมูลหุ้น",
                "ไม่สามารถดึงข้อมูลราคาหุ้นจาก Finnhub ได้\n\n"
                "กรุณาตรวจสอบ Internet หรือรอสักครู่แล้วลองใหม่อีกครั้ง"
            )
            return

        # ถ้าไม่มีข้อมูล Quote จริง ๆ จึงถือว่าไม่พบหุ้น
        if stock is None or stock.get("price") is None:
            self.show_stock_not_found(symbol)
            return

        self.display_stock_data(stock)

    # ==================================================
    # FIND SIMILAR STOCKS
    # ==================================================
    def find_similar_stocks(self, symbol, limit=5):
        """
        ค้นหาหุ้นที่มีชื่อย่อใกล้เคียงกับคำที่ผู้ใช้กรอก
        โดยค้นจากตาราง stocks ก่อน และมีรายการหุ้นสำรองเพื่อให้
        สามารถแสดงคำแนะนำได้แม้ฐานข้อมูลหุ้นยังมีข้อมูลไม่ครบ
        """
        symbol = symbol.upper().strip()
        rows = []

        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT symbol, name
                FROM stocks
                WHERE symbol IS NOT NULL
            """)

            rows = cursor.fetchall()
            connection.close()

        except sqlite3.Error:
            rows = []

        # สร้าง dictionary เพื่อป้องกัน ticker ซ้ำ
        stock_names = {}

        for row in rows:
            stock_symbol = str(row[0]).upper().strip()

            if stock_symbol:
                stock_names[stock_symbol] = row[1] or "-"

        # รายการสำรองสำหรับกรณีตาราง stocks ยังมีข้อมูลไม่ครบ
        fallback_stocks = {
            "AAPL": "Apple Inc.",
            "AMD": "Advanced Micro Devices",
            "AMZN": "Amazon.com",
            "AVGO": "Broadcom",
            "GOOGL": "Alphabet Inc.",
            "GOOG": "Alphabet Inc.",
            "META": "Meta Platforms",
            "MSFT": "Microsoft",
            "MU": "Micron Technology",
            "NFLX": "Netflix",
            "NVDA": "NVIDIA",
            "ORCL": "Oracle",
            "PLTR": "Palantir Technologies",
            "QCOM": "QUALCOMM",
            "RKLB": "Rocket Lab",
            "SMCI": "Super Micro Computer",
            "TSLA": "Tesla",
            "TSM": "Taiwan Semiconductor Manufacturing",
            "VRT": "Vertiv Holdings",
            "ARM": "Arm Holdings",
            "ASML": "ASML Holding",
            "INTC": "Intel",
            "CRWD": "CrowdStrike",
            "COIN": "Coinbase",
            "HOOD": "Robinhood Markets",
            "MSTR": "Strategy",
            "MELI": "MercadoLibre",
            "COST": "Costco",
            "WMT": "Walmart",
            "JPM": "JPMorgan Chase",
            "BAC": "Bank of America",
            "V": "Visa",
            "MA": "Mastercard"
        }

        for stock_symbol, company_name in fallback_stocks.items():
            if stock_symbol not in stock_names:
                stock_names[stock_symbol] = company_name

        if not stock_names:
            return []

        stock_symbols = list(stock_names.keys())

        # จัดอันดับตามความใกล้เคียงของ ticker
        close_symbols = difflib.get_close_matches(
            symbol,
            stock_symbols,
            n=limit,
            cutoff=0.0
        )

        results = []

        for close_symbol in close_symbols:
            results.append({
                "symbol": close_symbol,
                "name": stock_names.get(close_symbol, "-")
            })

        return results

    # ==================================================
    # STOCK NOT FOUND
    # ==================================================
    def show_stock_not_found(self, symbol):

        for widget in self.stock_result_frame.winfo_children():
            widget.destroy()

        ttk.Label(
            self.stock_result_frame,
            text=f'ไม่พบหุ้น "{symbol}" ในระบบ',
            font=("Tahoma", 20, "bold")
        ).pack(
            anchor="w",
            pady=(5, 10)
        )

        ttk.Label(
            self.stock_result_frame,
            text="กรุณาตรวจสอบชื่อหุ้น แล้วลองเลือกจากหุ้นที่ใกล้เคียงด้านล่าง",
            style="Normal.TLabel"
        ).pack(
            anchor="w",
            pady=(0, 15)
        )

        similar_stocks = self.find_similar_stocks(symbol, limit=5)

        if not similar_stocks:

            ttk.Label(
                self.stock_result_frame,
                text="ยังไม่พบชื่อหุ้นที่ใกล้เคียงในฐานข้อมูล",
                style="Normal.TLabel"
            ).pack(
                anchor="w",
                pady=10
            )

            return

        suggestion_frame = ttk.LabelFrame(
            self.stock_result_frame,
            text="หุ้นที่ใกล้เคียง 5 อันดับ"
        )

        suggestion_frame.pack(
            fill="x",
            pady=10
        )

        for index, stock in enumerate(similar_stocks, start=1):

            row_frame = ttk.Frame(
                suggestion_frame
            )

            row_frame.pack(
                fill="x",
                padx=15,
                pady=6
            )

            ttk.Label(
                row_frame,
                text=f"{index}. {stock['symbol']}",
                font=("Tahoma", 13, "bold"),
                width=12
            ).pack(
                side="left"
            )

            ttk.Label(
                row_frame,
                text=stock["name"],
                style="Normal.TLabel"
            ).pack(
                side="left",
                padx=10
            )

            ttk.Button(
                row_frame,
                text="วิเคราะห์หุ้นนี้",
                command=lambda s=stock["symbol"]: self.search_suggested_stock(s)
            ).pack(
                side="right"
            )

    # ==================================================
    # SEARCH SUGGESTED STOCK
    # ==================================================
    def search_suggested_stock(self, symbol):

        self.stock_symbol_entry.delete(
            0,
            tk.END
        )

        self.stock_symbol_entry.insert(
            0,
            symbol
        )

        self.search_stock()

    # ==================================================
    # DISPLAY STOCK DATA
    # ==================================================
    def display_stock_data(self, stock):

        for widget in self.stock_result_frame.winfo_children():
            widget.destroy()

        company_name = stock.get(
            "company_name"
        ) or "-"

        industry = stock.get(
            "industry"
        ) or "-"

        exchange = stock.get(
            "exchange"
        ) or "-"

        country = stock.get(
            "country"
        ) or "-"

        price = stock.get("price")
        change = stock.get("change")
        change_percent = stock.get("change_percent")

        high = stock.get("high")
        low = stock.get("low")
        open_price = stock.get("open")
        previous_close = stock.get("previous_close")

        market_cap = stock.get("market_cap")

        pe = stock.get("pe")
        roe = stock.get("roe")
        roa = stock.get("roa")
        net_margin = stock.get("net_margin")

        # -----------------------------
        # COMPANY
        # -----------------------------
        ttk.Label(
            self.stock_result_frame,
            text=f"{stock['symbol']} - {company_name}",
            font=("Tahoma", 22, "bold")
        ).pack(
            anchor="w",
            pady=(0, 15)
        )

        self.build_stock_dashboard(stock)

        # -----------------------------
        # COMPANY INFO
        # -----------------------------
        info_frame = ttk.Frame(
            self.stock_result_frame
        )

        info_frame.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            info_frame,
            text=f"อุตสาหกรรม: {industry}",
            style="Normal.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=5
        )

        ttk.Label(
            info_frame,
            text=f"ตลาด: {exchange}",
            style="Normal.TLabel"
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=10,
            pady=5
        )

        ttk.Label(
            info_frame,
            text=f"ประเทศ: {country}",
            style="Normal.TLabel"
        ).grid(
            row=0,
            column=2,
            sticky="w",
            padx=10,
            pady=5
        )

        # -----------------------------
        # PRICE
        # -----------------------------
        price_frame = ttk.LabelFrame(
            self.stock_result_frame,
            text="ข้อมูลราคา"
        )

        price_frame.pack(
            fill="x",
            pady=10
        )

        price_text = (
            f"ราคาปัจจุบัน: "
            f"{self.format_number(price)}\n"
            f"เปลี่ยนแปลง: "
            f"{self.format_number(change)} "
            f"({self.format_number(change_percent)}%)\n"
            f"สูงสุดวันนี้: "
            f"{self.format_number(high)}\n"
            f"ต่ำสุดวันนี้: "
            f"{self.format_number(low)}\n"
            f"ราคาเปิด: "
            f"{self.format_number(open_price)}\n"
            f"ราคาปิดก่อนหน้า: "
            f"{self.format_number(previous_close)}"
        )

        ttk.Label(
            price_frame,
            text=price_text,
            style="Normal.TLabel",
            justify="left"
        ).pack(
            anchor="w",
            padx=15,
            pady=10
        )

        # -----------------------------
        # FUNDAMENTAL
        # -----------------------------
        fundamental_frame = ttk.LabelFrame(
            self.stock_result_frame,
            text="วิเคราะห์พื้นฐาน"
        )

        fundamental_frame.pack(
            fill="x",
            pady=10
        )

        fundamental_text = (
            f"P/E: "
            f"{self.format_pe(pe)}\n"
            f"ROE: "
            f"{self.format_percent(roe)}\n"
            f"ROA: "
            f"{self.format_percent(roa)}\n"
            f"Net Profit Margin: "
            f"{self.format_percent(net_margin)}"
        )

        ttk.Label(
            fundamental_frame,
            text=fundamental_text,
            style="Normal.TLabel",
            justify="left"
        ).pack(
            anchor="w",
            padx=15,
            pady=10
        )

        # -----------------------------
        # FUNDAMENTAL ANALYSIS
        # -----------------------------
        analysis_frame = ttk.LabelFrame(
            self.stock_result_frame,
            text="สรุปตัวชี้วัดพื้นฐาน"
        )

        analysis_frame.pack(
            fill="x",
            pady=10
        )

        analysis_text = self.analyze_fundamentals(
            pe,
            roe,
            roa,
            net_margin
        )

        ttk.Label(
            analysis_frame,
            text=analysis_text,
            style="Normal.TLabel",
            justify="left",
            wraplength=950
        ).pack(
            anchor="w",
            padx=15,
            pady=10
        )

        # -----------------------------
        # QUICK SCORE
        # -----------------------------
        score_frame = ttk.LabelFrame(
            self.stock_result_frame,
            text="สรุปภาพรวมเบื้องต้น"
        )
        score_frame.pack(fill="x", pady=10)

        score, score_text = self.calculate_fundamental_score(
            pe, roe, roa, net_margin
        )

        ttk.Label(
            score_frame,
            text=f"คะแนนเบื้องต้น: {score}/100\n{score_text}",
            style="Normal.TLabel",
            justify="left",
            wraplength=950
        ).pack(anchor="w", padx=15, pady=10)

        # -----------------------------
        # MARKET CAP
        # -----------------------------
        market_frame = ttk.LabelFrame(
            self.stock_result_frame,
            text="ข้อมูลเพิ่มเติม"
        )

        market_frame.pack(
            fill="x",
            pady=10
        )

        ttk.Label(
            market_frame,
            text=(
                f"Market Cap: "
                f"{self.format_number(market_cap)}"
            ),
            style="Normal.TLabel"
        ).pack(
            anchor="w",
            padx=15,
            pady=10
        )

    # ==================================================
    # ANALYZE FUNDAMENTALS
    # ==================================================
    def analyze_fundamentals(
        self,
        pe,
        roe,
        roa,
        net_margin
    ):

        strengths = []
        warnings = []
        neutral = []

        # ==================================================
        # P/E
        # ==================================================
        if pe is None:

            warnings.append(
                "P/E ไม่มีข้อมูล จึงไม่สามารถประเมินระดับราคาด้วยตัวชี้วัดนี้ได้"
            )

        else:

            try:
                pe_value = float(pe)

                if pe_value <= 0:

                    warnings.append(
                        "P/E ไม่เหมาะสำหรับใช้ประเมิน เนื่องจากค่าเป็นศูนย์หรือติดลบ"
                    )

                elif pe_value < 15:

                    strengths.append(
                        f"P/E {pe_value:.2f} เท่า อยู่ในระดับไม่สูงเมื่อเทียบกับเกณฑ์ทั่วไป"
                    )

                elif pe_value <= 25:

                    neutral.append(
                        f"P/E {pe_value:.2f} เท่า อยู่ในระดับปานกลาง"
                    )

                else:

                    warnings.append(
                        f"P/E {pe_value:.2f} เท่า ค่อนข้างสูง นักลงทุนกำลังจ่ายราคาสูงเมื่อเทียบกับกำไร"
                    )

            except (ValueError, TypeError):

                warnings.append(
                    "ไม่สามารถประเมิน P/E ได้"
                )

        # ==================================================
        # ROE
        # ==================================================
        if roe is None:

            warnings.append(
                "ไม่มีข้อมูล ROE"
            )

        else:

            try:
                roe_value = float(roe)

                if roe_value >= 20:

                    strengths.append(
                        f"ROE {roe_value:.2f}% อยู่ในระดับสูง แสดงถึงการใช้เงินทุนของผู้ถือหุ้นได้มีประสิทธิภาพ"
                    )

                elif roe_value >= 10:

                    neutral.append(
                        f"ROE {roe_value:.2f}% อยู่ในระดับปานกลาง"
                    )

                else:

                    warnings.append(
                        f"ROE {roe_value:.2f}% ค่อนข้างต่ำ"
                    )

            except (ValueError, TypeError):

                warnings.append(
                    "ไม่สามารถประเมิน ROE ได้"
                )

        # ==================================================
        # ROA
        # ==================================================
        if roa is None:

            warnings.append(
                "ไม่มีข้อมูล ROA"
            )

        else:

            try:
                roa_value = float(roa)

                if roa_value >= 10:

                    strengths.append(
                        f"ROA {roa_value:.2f}% อยู่ในระดับสูง สะท้อนประสิทธิภาพในการใช้สินทรัพย์"
                    )

                elif roa_value >= 5:

                    neutral.append(
                        f"ROA {roa_value:.2f}% อยู่ในระดับปานกลาง"
                    )

                else:

                    warnings.append(
                        f"ROA {roa_value:.2f}% ค่อนข้างต่ำ"
                    )

            except (ValueError, TypeError):

                warnings.append(
                    "ไม่สามารถประเมิน ROA ได้"
                )

        # ==================================================
        # NET PROFIT MARGIN
        # ==================================================
        if net_margin is None:

            warnings.append(
                "ไม่มีข้อมูล Net Profit Margin"
            )

        else:

            try:
                margin_value = float(net_margin)

                if margin_value >= 20:

                    strengths.append(
                        f"Net Profit Margin {margin_value:.2f}% สูง แสดงว่าบริษัทสามารถเปลี่ยนรายได้เป็นกำไรได้ดี"
                    )

                elif margin_value >= 10:

                    neutral.append(
                        f"Net Profit Margin {margin_value:.2f}% อยู่ในระดับปานกลาง"
                    )

                elif margin_value >= 0:

                    warnings.append(
                        f"Net Profit Margin {margin_value:.2f}% ค่อนข้างต่ำ"
                    )

                else:

                    warnings.append(
                        f"Net Profit Margin {margin_value:.2f}% ติดลบ แสดงว่าบริษัทขาดทุน"
                    )

            except (ValueError, TypeError):

                warnings.append(
                    "ไม่สามารถประเมิน Net Profit Margin ได้"
                )

        # ==================================================
        # OVERALL
        # ==================================================
        if len(strengths) >= 2 and len(warnings) == 0:

            overall = "ภาพรวมพื้นฐาน: ค่อนข้างแข็งแรง"

        elif len(warnings) >= 2:

            overall = "ภาพรวมพื้นฐาน: ควรระมัดระวัง"

        else:

            overall = "ภาพรวมพื้นฐาน: ปานกลาง ต้องพิจารณาหลายปัจจัยร่วมกัน"

        # ==================================================
        # BUILD TEXT
        # ==================================================
        result = overall + "\n\n"

        if len(strengths) > 0:

            result += "จุดเด่น:\n"

            for item in strengths:

                result += f"• {item}\n"

        if len(neutral) > 0:

            result += "\nข้อมูลที่ควรพิจารณา:\n"

            for item in neutral:

                result += f"• {item}\n"

        if len(warnings) > 0:

            result += "\nจุดที่ควรระวัง:\n"

            for item in warnings:

                result += f"• {item}\n"

        result += (
            "\nหมายเหตุ: การประเมินนี้ใช้ตัวชี้วัดพื้นฐานเบื้องต้น "
            "ไม่ควรใช้เป็นเหตุผลเดียวในการตัดสินใจลงทุน"
        )

        return result

    # ==================================================
    # FORMAT P/E
    # ==================================================
    def calculate_fundamental_score(self, pe, roe, roa, net_margin):

        score = 0
        reasons = []

        try:
            if pe is not None and float(pe) > 0:
                pe_value = float(pe)
                if pe_value < 15:
                    score += 25
                elif pe_value <= 25:
                    score += 18
                else:
                    score += 8
            else:
                reasons.append("P/E ไม่สามารถใช้ให้คะแนนได้")
        except (ValueError, TypeError):
            reasons.append("P/E ไม่สามารถใช้ให้คะแนนได้")

        try:
            roe_value = float(roe)
            if roe_value >= 20:
                score += 30
            elif roe_value >= 10:
                score += 20
            elif roe_value > 0:
                score += 10
        except (ValueError, TypeError):
            reasons.append("ROE ไม่มีข้อมูลเพียงพอ")

        try:
            roa_value = float(roa)
            if roa_value >= 10:
                score += 20
            elif roa_value >= 5:
                score += 14
            elif roa_value > 0:
                score += 7
        except (ValueError, TypeError):
            reasons.append("ROA ไม่มีข้อมูลเพียงพอ")

        try:
            margin_value = float(net_margin)
            if margin_value >= 20:
                score += 25
            elif margin_value >= 10:
                score += 17
            elif margin_value > 0:
                score += 8
        except (ValueError, TypeError):
            reasons.append("Net Profit Margin ไม่มีข้อมูลเพียงพอ")

        if score >= 80:
            conclusion = "ตัวชี้วัดพื้นฐานที่มีข้อมูลอยู่ในระดับแข็งแรงตามเกณฑ์เบื้องต้น"
        elif score >= 60:
            conclusion = "ตัวชี้วัดพื้นฐานโดยรวมอยู่ในระดับปานกลางถึงค่อนข้างดี"
        elif score >= 40:
            conclusion = "ตัวชี้วัดพื้นฐานมีทั้งจุดแข็งและจุดที่ควรติดตาม"
        else:
            conclusion = "ตัวชี้วัดพื้นฐานมีข้อจำกัดหรือสัญญาณที่ควรตรวจสอบเพิ่มเติม"

        if reasons:
            conclusion += "\n" + "\n".join(f"• {reason}" for reason in reasons)

        conclusion += "\nหมายเหตุ: คะแนนนี้เป็นเกณฑ์ภายในโปรแกรม ไม่ใช่คำแนะนำให้ซื้อหรือขายหุ้น"

        return score, conclusion

    def format_pe(self, value):

        if value is None:
            return "ไม่มีข้อมูล"

        try:

            pe_value = float(value)

            if pe_value <= 0:

                return "ไม่เหมาะสำหรับใช้ประเมิน"

            return f"{pe_value:,.2f} เท่า"

        except (ValueError, TypeError):

            return "ไม่สามารถประเมินได้"

    # ==================================================
    # PAGE 2 : PORTFOLIO RISK
    # ==================================================
    def create_portfolio_risk_page(self):

        # ==================================================
        # SCROLL AREA
        # ==================================================
        self.risk_canvas = tk.Canvas(
            self.risk_page,
            highlightthickness=0
        )

        self.risk_scrollbar = ttk.Scrollbar(
            self.risk_page,
            orient="vertical",
            command=self.risk_canvas.yview
        )

        self.risk_scrollable_frame = ttk.Frame(
            self.risk_canvas
        )

        self.risk_scrollable_frame.bind(
            "<Configure>",
            self.update_risk_scrollregion
        )

        self.risk_canvas_window = (
            self.risk_canvas.create_window(
                (0, 0),
                window=self.risk_scrollable_frame,
                anchor="nw"
            )
        )

        self.risk_canvas.configure(
            yscrollcommand=self.risk_scrollbar.set
        )

        self.risk_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.risk_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.risk_canvas.bind(
            "<Configure>",
            self.resize_risk_scrollable_frame
        )

        self.risk_canvas.bind(
            "<Enter>",
            self.enable_risk_mousewheel
        )

        self.risk_canvas.bind(
            "<Leave>",
            self.disable_risk_mousewheel
        )

        # ==================================================
        # TITLE
        # ==================================================
        self.risk_banner = AnimatedBanner(
            self.risk_scrollable_frame,
            "วิเคราะห์ความเสี่ยงของพอร์ต",
            "ดูว่าพอร์ตของคุณกระจุกตัวและมีความเสี่ยงมากแค่ไหน",
            seed=23,
            tag="PORTFOLIO RISK"
        )
        self.risk_banner.pack(fill="x", padx=30, pady=(22, 12))

        # ==================================================
        # PORTFOLIO SUMMARY
        # ==================================================
        # การ์ดตัวเลขสำคัญ 5 ใบเรียงกันแนวนอน
        cards_frame = ttk.Frame(self.risk_scrollable_frame)
        cards_frame.pack(fill="x", padx=25, pady=(0, 10))

        self.card_total = self.make_risk_card(
            cards_frame, "เงินลงทุนรวม", 0, THEME_COLORS["primary"]
        )
        self.card_count = self.make_risk_card(
            cards_frame, "จำนวนหุ้น", 1, THEME_COLORS["cyan"]
        )
        self.card_top_stock = self.make_risk_card(
            cards_frame, "หุ้นน้ำหนักสูงสุด", 2, THEME_COLORS["violet"]
        )
        self.card_top_industry = self.make_risk_card(
            cards_frame, "อุตสาหกรรมหลัก", 3, THEME_COLORS["warning"]
        )
        self.card_level = self.make_risk_card(
            cards_frame, "ระดับความเสี่ยง", 4, THEME_COLORS["positive"]
        )

        self.reset_risk_cards()

        # ==================================================
        # INPUT
        # ==================================================
        input_frame = ttk.Frame(
            self.risk_scrollable_frame
        )

        input_frame.pack(
            fill="x",
            padx=40,
            pady=10
        )

        ttk.Label(
            input_frame,
            text="ชื่อหุ้น",
            style="Normal.TLabel"
        ).grid(
            row=0,
            column=0,
            padx=10,
            pady=5
        )

        self.portfolio_symbol_entry = ttk.Entry(
            input_frame,
            width=20,
            font=("Tahoma", 12)
        )

        self.portfolio_symbol_entry.grid(
            row=0,
            column=1,
            padx=10,
            pady=5
        )

        ttk.Label(
            input_frame,
            text="เงินลงทุน",
            style="Normal.TLabel"
        ).grid(
            row=0,
            column=2,
            padx=10,
            pady=5
        )

        self.portfolio_amount_entry = ttk.Entry(
            input_frame,
            width=20,
            font=("Tahoma", 12)
        )

        self.portfolio_amount_entry.grid(
            row=0,
            column=3,
            padx=10,
            pady=5
        )

        ttk.Button(
            input_frame,
            text="เพิ่มเข้าพอร์ต",
            command=self.add_portfolio_stock
        ).grid(
            row=0,
            column=4,
            padx=10
        )

        ttk.Button(
            input_frame,
            text="ล้างพอร์ต",
            command=self.clear_portfolio
        ).grid(
            row=0,
            column=5,
            padx=10
        )

        # ==================================================
        # PORTFOLIO TABLE
        # ==================================================
        table_frame = ttk.Frame(
            self.risk_scrollable_frame
        )

        table_frame.pack(
            fill="x",
            padx=30,
            pady=15
        )

        columns = (
            "symbol",
            "company",
            "amount",
            "weight",
            "industry"
        )

        self.portfolio_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=8
        )

        self.portfolio_tree.heading(
            "symbol",
            text="หุ้น"
        )

        self.portfolio_tree.heading(
            "company",
            text="บริษัท"
        )

        self.portfolio_tree.heading(
            "amount",
            text="เงินลงทุน"
        )

        self.portfolio_tree.heading(
            "weight",
            text="สัดส่วน"
        )

        self.portfolio_tree.heading(
            "industry",
            text="อุตสาหกรรม"
        )

        self.portfolio_tree.column(
            "symbol",
            width=100
        )

        self.portfolio_tree.column(
            "company",
            width=240
        )

        self.portfolio_tree.column(
            "amount",
            width=150
        )

        self.portfolio_tree.column(
            "weight",
            width=130
        )

        self.portfolio_tree.column(
            "industry",
            width=240
        )

        table_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.portfolio_tree.yview
        )

        self.portfolio_tree.configure(
            yscrollcommand=table_scrollbar.set
        )

        self.portfolio_tree.pack(
            side="left",
            fill="x",
            expand=True
        )

        table_scrollbar.pack(
            side="right",
            fill="y"
        )

        # ==================================================
        # DELETE BUTTON
        # ==================================================
        action_frame = ttk.Frame(self.risk_scrollable_frame)
        action_frame.pack(pady=(0, 15))

        ttk.Button(
            action_frame,
            text="แก้ไขเงินลงทุน",
            command=self.edit_selected_stock
        ).grid(row=0, column=0, padx=6)

        ttk.Button(
            action_frame,
            text="ลบหุ้นที่เลือก",
            command=self.delete_selected_stock
        ).grid(row=0, column=1, padx=6)

        ttk.Button(
            action_frame,
            text="รีเฟรชข้อมูลตลาด",
            command=self.refresh_market_data
        ).grid(row=0, column=2, padx=6)

        self.market_status_label = ttk.Label(
            action_frame,
            text="ข้อมูลตลาดจริง: เพิ่มหุ้นเข้าพอร์ตเพื่อดึงข้อมูล",
            foreground=THEME_COLORS["muted"]
        )
        self.market_status_label.grid(
            row=1, column=0, columnspan=3, pady=(8, 0)
        )

        # ==================================================
        # RISK SUMMARY
        # ==================================================
        # ---- มาตรวัดความเสี่ยง + สรุปภาษาง่าย ----
        self.risk_gauge = RiskGauge(self.risk_scrollable_frame)
        self.risk_gauge.pack(fill="x", padx=30, pady=(0, 12))

        # ---- ตัวชี้วัดความเสี่ยงเชิงลึก (การ์ดเล็ก 4 ใบ) ----
        metric_frame = ttk.LabelFrame(
            self.risk_scrollable_frame,
            text="ตัวชี้วัดความเสี่ยงเชิงลึก"
        )
        metric_frame.pack(fill="x", padx=30, pady=(0, 10))

        metric_row = ttk.Frame(metric_frame)
        metric_row.pack(fill="x", padx=5, pady=8)

        self.metric_top3 = self.make_risk_card(
            metric_row, "3 อันดับแรกรวมกัน", 0, THEME_COLORS["primary"]
        )
        self.metric_effective = self.make_risk_card(
            metric_row, "จำนวนหุ้นที่แท้จริง", 1, THEME_COLORS["cyan"]
        )
        self.metric_hhi = self.make_risk_card(
            metric_row, "ดัชนีกระจุกตัว (HHI)", 2, THEME_COLORS["violet"]
        )
        self.metric_industry = self.make_risk_card(
            metric_row, "จำนวนอุตสาหกรรม", 3, THEME_COLORS["warning"]
        )

        for card in (
            self.metric_top3,
            self.metric_effective,
            self.metric_hhi,
            self.metric_industry
        ):
            card[0].config(text="-")
            card[1].config(text="เพิ่มหุ้นเพื่อคำนวณ")

        # ---- สรุปความเสี่ยง แยก 3 คอลัมน์ ----
        self.risk_summary_frame = ttk.LabelFrame(
            self.risk_scrollable_frame,
            text="สรุปความเสี่ยง"
        )

        self.risk_summary_frame.pack(
            fill="x",
            padx=30,
            pady=(0, 10)
        )

        self.risk_summary_label = ttk.Label(
            self.risk_summary_frame,
            text="เพิ่มหุ้นเข้าพอร์ตเพื่อเริ่มวิเคราะห์",
            style="Normal.TLabel",
            justify="left"
        )
        self.risk_summary_label.pack(anchor="w", padx=15, pady=(10, 5))

        text_row = ttk.Frame(self.risk_summary_frame)
        text_row.pack(fill="x", padx=10, pady=(0, 10))

        self.risk_points_label = self.make_text_box(
            text_row, "⚠ จุดที่ต้องระวัง", THEME_COLORS["negative"], 0
        )
        self.risk_protect_label = self.make_text_box(
            text_row, "✔ จุดที่ช่วยลดความเสี่ยง", THEME_COLORS["positive"], 1
        )
        self.risk_advice_label = self.make_text_box(
            text_row, "💡 คำแนะนำ", THEME_COLORS["cyan"], 2
        )

        # ==================================================
        # PORTFOLIO CHART
        # ==================================================
        chart_frame = ttk.LabelFrame(
            self.risk_scrollable_frame,
            text="สัดส่วนการลงทุนในพอร์ต"
        )

        chart_frame.pack(
            fill="x",
            padx=30,
            pady=(0, 12)
        )

        self.portfolio_chart = tk.Canvas(
            chart_frame,
            width=800,
            height=420,
            bg=THEME_COLORS["surface"],
            highlightthickness=0
        )

        self.portfolio_chart.pack(
            fill="x",
            padx=10,
            pady=10
        )

        # ---- ส่วนวิเคราะห์เชิงลึก (องค์ประกอบคะแนน, ธีม, stress test, ปรับสมดุล) ----
        self.create_risk_deep_sections()

        # ---- เกณฑ์ที่ใช้ประเมิน ----
        criteria_frame = ttk.LabelFrame(
            self.risk_deep_container,
            text="เกณฑ์ที่โปรแกรมใช้ประเมินความเสี่ยง"
        )
        criteria_frame.pack(fill="x", padx=30, pady=(0, 10))

        criteria_text = (
            "• คะแนนรวม 0-100 คำนวณจาก 5 องค์ประกอบ: การกระจุกตัวรายหุ้น 30% "
            "(น้ำหนักหุ้นใหญ่สุด + 3 อันดับแรก), การกระจุกตัวรายอุตสาหกรรม 25%, "
            "ความลึกของการกระจาย 20% (จำนวนหุ้นที่แท้จริงจาก HHI), "
            "ธีมที่ขับเคลื่อนร่วมกัน 15%, ความอ่อนไหวและความผันผวน 10%\n"
            "• ระดับ: ค่อนข้างต่ำ < 35 | ปานกลาง 35-54 | ปานกลางค่อนข้างสูง 55-74 | สูง ≥ 75\n"
            "• เกณฑ์ขั้นต่ำ (ระดับจะไม่ต่ำกว่านี้): สูง = หุ้นตัวเดียว ≥ 60% หรืออุตสาหกรรมเดียว ≥ 70% | "
            "ปานกลางค่อนข้างสูง = หุ้นตัวเดียว ≥ 40% หรืออุตสาหกรรมเดียว ≥ 50% หรือมีหุ้นไม่เกิน 2 ตัว | "
            "ปานกลาง = หุ้นตัวเดียว ≥ 30% หรืออุตสาหกรรมเดียว ≥ 40% หรือมีหุ้นไม่เกิน 4 ตัว\n"
            "• HHI = ผลรวมของ (สัดส่วน%)² ยิ่งสูงยิ่งกระจุกตัว "
            "(ต่ำกว่า 1,500 = กระจายดี, 1,500-2,500 = ปานกลาง, สูงกว่า 2,500 = กระจุกตัว)\n"
            "• ความอ่อนไหวต่อตลาด: ใช้ beta จริงของหุ้น (จาก Finnhub หรือคำนวณเทียบ SPY จากราคาปิด"
            "รายวันย้อนหลังประมาณ 1 ปี) 1.00 = ขึ้นลงเท่าตลาด ถ้าหุ้นตัวไหนดึงข้อมูลไม่ได้ "
            "จะใช้ค่าประมาณจากชื่ออุตสาหกรรมแทน และจะแจ้งไว้ในผลวิเคราะห์\n"
            "• ความผันผวน = ส่วนเบี่ยงเบนมาตรฐานของผลตอบแทนรายวันคูณ √252 (ต่อปี) | "
            "Drawdown สูงสุด = การลดลงจากจุดสูงสุดที่ลึกที่สุดในช่วงย้อนหลัง | "
            "ค่าเฉลี่ยถ่วงน้ำหนักของพอร์ตไม่ใช่ความผันผวนพอร์ตจริง เพราะยังไม่รวมค่าสหสัมพันธ์ระหว่างหุ้น\n"
            "• ธีม: จัดกลุ่มจากชื่ออุตสาหกรรม ไม่ใช่ค่าสหสัมพันธ์จริงของแต่ละหุ้น\n"
            "• Stress Test และเพดานอ้างอิง (หุ้น 25% / อุตสาหกรรม 40%) เป็นสมมติฐานเพื่อเปรียบเทียบ "
            "ไม่ใช่การพยากรณ์\n"
            "หมายเหตุ: เป็นการประเมินจากโครงสร้างพอร์ตเบื้องต้น ไม่ใช่คำแนะนำให้ซื้อหรือขายหุ้น"
        )

        criteria_label = ttk.Label(
            criteria_frame,
            text=criteria_text,
            style="Normal.TLabel",
            justify="left",
            foreground=THEME_COLORS["muted"]
        )
        criteria_label.pack(anchor="w", padx=15, pady=10)
        criteria_frame.bind(
            "<Configure>",
            lambda event: criteria_label.config(wraplength=event.width - 40)
        )

        # ==================================================
        # INDUSTRY TABLE
        # ==================================================
        industry_frame = ttk.LabelFrame(
            self.risk_deep_container,
            text="การกระจุกตัวตามอุตสาหกรรม"
        )

        industry_frame.pack(
            fill="x",
            padx=30,
            pady=(0, 20)
        )

        industry_columns = (
            "industry",
            "industry_amount",
            "industry_weight"
        )

        self.industry_chart = tk.Canvas(
            industry_frame,
            height=190,
            bg=THEME_COLORS["surface"],
            highlightthickness=0
        )
        self.industry_chart.pack(
            fill="x",
            padx=10,
            pady=(10, 0)
        )
        self.industry_chart.bind(
            "<Configure>",
            lambda event: self._draw_industry_bars(1.0)
            if hasattr(self, "_industry_items") else None
        )

        self.industry_tree = ttk.Treeview(
            industry_frame,
            columns=industry_columns,
            show="headings",
            height=5
        )

        self.industry_tree.heading(
            "industry",
            text="อุตสาหกรรม"
        )

        self.industry_tree.heading(
            "industry_amount",
            text="เงินลงทุน"
        )

        self.industry_tree.heading(
            "industry_weight",
            text="สัดส่วน"
        )

        self.industry_tree.column(
            "industry",
            width=350
        )

        self.industry_tree.column(
            "industry_amount",
            width=200
        )

        self.industry_tree.column(
            "industry_weight",
            width=180
        )

        self.industry_tree.pack(
            fill="x",
            padx=10,
            pady=10
        )

    # ==================================================
    # RISK PAGE HELPERS (ฟังก์ชันช่วยสร้างการ์ดและกล่องข้อความ)
    # ==================================================
    def make_risk_card(self, parent, title, column, accent):
        """สร้างการ์ดเล็ก: แถบสีด้านบน + หัวข้อ + ตัวเลขใหญ่ + หมายเหตุ"""
        card = tk.Frame(
            parent,
            bg=THEME_COLORS["surface"],
            highlightthickness=1,
            highlightbackground=THEME_COLORS["border"]
        )
        card.grid(row=0, column=column, sticky="nsew", padx=5, pady=2)
        parent.columnconfigure(column, weight=1, uniform="cards")

        tk.Frame(card, bg=accent, height=3).pack(fill="x")

        tk.Label(
            card,
            text=title,
            bg=THEME_COLORS["surface"],
            fg=THEME_COLORS["muted"],
            font=("Tahoma", 10),
            anchor="w"
        ).pack(fill="x", padx=14, pady=(10, 0))

        value_label = tk.Label(
            card,
            text="-",
            bg=THEME_COLORS["surface"],
            fg=THEME_COLORS["text"],
            font=("Tahoma", 16, "bold"),
            anchor="w"
        )
        value_label.pack(fill="x", padx=14)

        note_label = tk.Label(
            card,
            text="",
            bg=THEME_COLORS["surface"],
            fg=THEME_COLORS["muted"],
            font=("Tahoma", 9),
            anchor="w"
        )
        note_label.pack(fill="x", padx=14, pady=(0, 10))

        return value_label, note_label

    def make_text_box(self, parent, title, color, column):
        """สร้างกล่องข้อความ 1 คอลัมน์ มีหัวข้อสี และปรับการตัดบรรทัดตามความกว้าง"""
        box = tk.Frame(
            parent,
            bg=THEME_COLORS["surface"],
            highlightthickness=1,
            highlightbackground=THEME_COLORS["border"]
        )
        box.grid(row=0, column=column, sticky="nsew", padx=5, pady=2)
        parent.columnconfigure(column, weight=1, uniform="textbox")

        tk.Label(
            box,
            text=title,
            bg=THEME_COLORS["surface"],
            fg=color,
            font=("Tahoma", 11, "bold"),
            anchor="w"
        ).pack(fill="x", padx=14, pady=(10, 4))

        body = tk.Label(
            box,
            text="-",
            bg=THEME_COLORS["surface"],
            fg=THEME_COLORS["text"],
            font=("Tahoma", 10),
            justify="left",
            anchor="nw",
            wraplength=260
        )
        body.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        box.bind(
            "<Configure>",
            lambda event: body.config(wraplength=max(120, event.width - 30))
        )

        return body

    def reset_risk_cards(self):
        """คืนค่าการ์ดทั้งหมดเป็นค่าเริ่มต้น (ตอนยังไม่มีหุ้น)"""
        self.card_total[0].config(text="0.00", fg=THEME_COLORS["text"])
        self.card_total[1].config(text="บาท")
        self.card_count[0].config(text="0", fg=THEME_COLORS["text"])
        self.card_count[1].config(text="ตัว")
        self.card_top_stock[0].config(text="-", fg=THEME_COLORS["text"])
        self.card_top_stock[1].config(text="ยังไม่มีข้อมูล")
        self.card_top_industry[0].config(text="-", fg=THEME_COLORS["text"])
        self.card_top_industry[1].config(text="ยังไม่มีข้อมูล")
        self.card_level[0].config(text="-", fg=THEME_COLORS["text"])
        self.card_level[1].config(text="ยังไม่มีข้อมูล")

        if hasattr(self, "metric_top3"):
            for card in (
                self.metric_top3,
                self.metric_effective,
                self.metric_hhi,
                self.metric_industry
            ):
                card[0].config(text="-", fg=THEME_COLORS["text"])
                card[1].config(text="เพิ่มหุ้นเพื่อคำนวณ")

        if hasattr(self, "risk_points_label"):
            self.risk_points_label.config(text="-")
            self.risk_protect_label.config(text="-")
            self.risk_advice_label.config(text="-")

        self.reset_risk_deep_analysis()
        self.update_market_status()

    # ==================================================
    # RISK DEEP ANALYSIS : ส่วนวิเคราะห์เชิงลึกของหน้าความเสี่ยง
    # ==================================================
    def _make_risk_tree(self, parent, columns, height):
        """สร้างตารางในกรอบ: columns = [(id, หัวตาราง, ความกว้าง, ตำแหน่งข้อความ)]"""
        tree = ttk.Treeview(
            parent,
            columns=[c[0] for c in columns],
            show="headings",
            height=height
        )
        for column_id, heading, width, anchor in columns:
            tree.heading(column_id, text=heading)
            tree.column(column_id, width=width, anchor=anchor)

        tree.tag_configure("high", foreground=THEME_COLORS["negative"])
        tree.tag_configure("mid", foreground=THEME_COLORS["warning"])
        tree.tag_configure("good", foreground=THEME_COLORS["positive"])
        tree.pack(fill="x", padx=10, pady=(10, 10))
        return tree

    def toggle_risk_deep(self):
        """ยุบ/ขยายส่วนวิเคราะห์เชิงลึก (ค่าเริ่มต้น: ยุบไว้)"""
        if self._risk_deep_visible:
            self.risk_deep_container.pack_forget()
            self._risk_deep_visible = False
            self.risk_deep_button.config(text="▼  ดูรายละเอียดเชิงลึก")
        else:
            self.risk_deep_container.pack(
                fill="x", after=self.risk_deep_button_row
            )
            self._risk_deep_visible = True
            self.risk_deep_button.config(text="▲  ซ่อนรายละเอียดเชิงลึก")

        self.root.update_idletasks()
        self.update_risk_scrollregion()

    def create_risk_deep_sections(self):
        pad = dict(fill="x", padx=30, pady=(0, 10))

        # ---- ปุ่มเปิด/ปิดส่วนเชิงลึก ----
        self.risk_deep_button_row = ttk.Frame(self.risk_scrollable_frame)
        self.risk_deep_button_row.pack(fill="x", padx=30, pady=(0, 10))

        self.risk_deep_button = ttk.Button(
            self.risk_deep_button_row,
            text="▼  ดูรายละเอียดเชิงลึก",
            command=self.toggle_risk_deep
        )
        self.risk_deep_button.pack(pady=4)

        ttk.Label(
            self.risk_deep_button_row,
            text=(
                "องค์ประกอบคะแนน, รายหุ้น, ธีม, อุตสาหกรรม, Stress Test, "
                "แนวทางปรับสมดุล, บทวิเคราะห์ และเกณฑ์ที่ใช้ประเมิน"
            ),
            foreground=THEME_COLORS["muted"]
        ).pack()

        # กล่องรวมส่วนเชิงลึกทั้งหมด (ซ่อนไว้ก่อน กดปุ่มด้านบนเพื่อขยาย)
        self.risk_deep_container = ttk.Frame(self.risk_scrollable_frame)
        self._risk_deep_visible = False
        container = self.risk_deep_container

        # ---- องค์ประกอบของคะแนนความเสี่ยง ----
        factor_frame = ttk.LabelFrame(
            container,
            text="องค์ประกอบของคะแนนความเสี่ยง (5 ปัจจัย)"
        )
        factor_frame.pack(**pad)

        self.risk_factor_canvas = tk.Canvas(
            factor_frame,
            height=5 * 64 + 10,
            bg=THEME_COLORS["surface"],
            highlightthickness=0
        )
        self.risk_factor_canvas.pack(fill="x", padx=10, pady=10)
        self.risk_factor_canvas.bind(
            "<Configure>",
            lambda event: self._draw_risk_factors()
        )
        self._risk_factor_data = None

        # ---- การ์ดตัวชี้วัดเพิ่มเติม ----
        extra_frame = ttk.LabelFrame(
            container,
            text="ตัวชี้วัดเพิ่มเติม"
        )
        extra_frame.pack(**pad)

        extra_row = ttk.Frame(extra_frame)
        extra_row.pack(fill="x", padx=5, pady=8)

        self.metric_theme = self.make_risk_card(
            extra_row, "ธีมหลักของพอร์ต", 0, THEME_COLORS["cyan"]
        )
        self.metric_sens = self.make_risk_card(
            extra_row, "ความอ่อนไหวต่อตลาด", 1, THEME_COLORS["violet"]
        )
        self.metric_stress = self.make_risk_card(
            extra_row, "ตลาดลง 20% พอร์ตอาจลด", 2, THEME_COLORS["warning"]
        )
        self.risk_extra_cards = (
            self.metric_theme,
            self.metric_sens,
            self.metric_stress
        )

        # ---- ความเสี่ยงรายหุ้น ----
        stock_frame = ttk.LabelFrame(
            container,
            text="ความเสี่ยงรายหุ้น (สัดส่วนที่หุ้นแต่ละตัวส่งผลต่อความเสี่ยงของพอร์ต)"
        )
        stock_frame.pack(**pad)
        self.risk_stock_tree = self._make_risk_tree(
            stock_frame,
            [
                ("symbol", "หุ้น", 80, "w"),
                ("weight", "น้ำหนัก", 80, "e"),
                ("sens", "Beta / ความอ่อนไหว", 150, "center"),
                ("vol", "ผันผวน/ปี", 100, "e"),
                ("dd", "Drawdown สูงสุด", 120, "e"),
                ("share", "สัดส่วนความเสี่ยง", 120, "e"),
                ("theme", "ธีม", 200, "w"),
                ("note", "ข้อสังเกต", 220, "w"),
            ],
            5
        )

        # ---- ธีม ----
        theme_frame = ttk.LabelFrame(
            container,
            text="การกระจุกตัวตามธีม (ความเสี่ยงซ่อนเร้นจากหุ้นที่ขึ้นลงตามปัจจัยเดียวกัน)"
        )
        theme_frame.pack(**pad)
        self.risk_theme_tree = self._make_risk_tree(
            theme_frame,
            [
                ("theme", "ธีม", 250, "w"),
                ("weight", "น้ำหนัก", 90, "e"),
                ("amount", "เงินลงทุน", 130, "e"),
                ("sens", "ความอ่อนไหว", 110, "center"),
                ("members", "หุ้นในธีม", 300, "w"),
            ],
            4
        )

        # ---- Stress test ----
        stress_frame = ttk.LabelFrame(
            container,
            text="สถานการณ์จำลอง (Stress Test) — สมมติฐานเพื่อเปรียบเทียบ ไม่ใช่การพยากรณ์"
        )
        stress_frame.pack(**pad)
        self.risk_stress_tree = self._make_risk_tree(
            stress_frame,
            [
                ("name", "สถานการณ์", 200, "w"),
                ("assumption", "สมมติฐาน", 330, "w"),
                ("loss_pct", "พอร์ตลดลง", 90, "e"),
                ("loss_amount", "มูลค่าที่หาย (บาท)", 140, "e"),
                ("remaining", "มูลค่าคงเหลือ (บาท)", 150, "e"),
            ],
            6
        )

        # ---- แนวทางปรับสมดุล ----
        rebalance_frame = ttk.LabelFrame(
            container,
            text="แนวทางปรับสมดุลพอร์ต (เทียบกับน้ำหนักเท่ากัน และเพดานอ้างอิง)"
        )
        rebalance_frame.pack(**pad)
        self.risk_rebalance_tree = self._make_risk_tree(
            rebalance_frame,
            [
                ("symbol", "หุ้น", 90, "w"),
                ("weight", "น้ำหนักปัจจุบัน", 130, "e"),
                ("equal", "น้ำหนักเท่ากัน", 130, "e"),
                ("diff", "ต่างจากเท่ากัน", 130, "e"),
                ("excess", "ส่วนที่เกินเพดาน (บาท)", 180, "e"),
            ],
            5
        )

        # ---- บทวิเคราะห์เชิงลึก ----
        self.risk_deep_frame = ttk.LabelFrame(
            container,
            text="บทวิเคราะห์เชิงลึก"
        )
        self.risk_deep_frame.pack(**pad)
        self._risk_deep_labels = []
        self.risk_deep_frame.bind(
            "<Configure>",
            lambda event: [
                label.config(wraplength=max(200, event.width - 50))
                for label in self._risk_deep_labels
            ]
        )
        self.reset_risk_deep_analysis()

    def _draw_risk_factors(self):
        canvas = self.risk_factor_canvas
        canvas.delete("all")

        data = self._risk_factor_data
        if not data:
            canvas.create_text(
                20, 30,
                text="เพิ่มหุ้นเข้าพอร์ตเพื่อดูองค์ประกอบของคะแนน",
                fill=THEME_COLORS["muted"],
                font=("Tahoma", 11),
                anchor="w"
            )
            return

        width = max(canvas.winfo_width(), 400)
        left, right = 14, width - 14

        for index, factor in enumerate(data):
            top = 8 + index * 64
            score = factor["score"]

            if score >= 60:
                color = THEME_COLORS["negative"]
            elif score >= 35:
                color = THEME_COLORS["warning"]
            else:
                color = THEME_COLORS["positive"]

            canvas.create_text(
                left, top,
                text=f"{factor['name']}  (น้ำหนักในคะแนน {factor['weight']}%)",
                fill=THEME_COLORS["text"],
                font=("Tahoma", 11, "bold"),
                anchor="nw"
            )
            verdict = (
                "เสี่ยงสูง" if score >= 60
                else "ควรจับตา" if score >= 35
                else "ปกติ"
            )
            canvas.create_text(
                right, top,
                text=f"{verdict}  ·  {score:.0f}/100",
                fill=color,
                font=("Tahoma", 11, "bold"),
                anchor="ne"
            )

            bar_top, bar_bottom = top + 24, top + 34
            auth_rounded_rect(
                canvas, left, bar_top, right, bar_bottom, 5,
                fill=THEME_COLORS["field"], outline=""
            )
            fill_w = (right - left) * score / 100.0
            if fill_w >= 10:
                auth_rounded_rect(
                    canvas, left, bar_top, left + fill_w, bar_bottom, 5,
                    fill=color, outline=""
                )
            elif score > 0:
                canvas.create_rectangle(
                    left, bar_top, left + fill_w, bar_bottom,
                    fill=color, outline=""
                )

            canvas.create_text(
                left, top + 40,
                text=factor["note"],
                fill=THEME_COLORS["muted"],
                font=("Tahoma", 9),
                anchor="nw",
                width=right - left
            )

    def reset_risk_deep_analysis(self):
        """ล้างส่วนวิเคราะห์เชิงลึกทั้งหมดกลับเป็นค่าเริ่มต้น"""
        if not hasattr(self, "risk_deep_frame"):
            return

        for tree in (
            self.risk_stock_tree,
            self.risk_theme_tree,
            self.risk_stress_tree,
            self.risk_rebalance_tree
        ):
            for row in tree.get_children():
                tree.delete(row)

        for card in self.risk_extra_cards:
            card[0].config(text="-", fg=THEME_COLORS["text"])
            card[1].config(text="เพิ่มหุ้นเพื่อคำนวณ")

        self._risk_factor_data = None
        self._draw_risk_factors()

        self._render_risk_narrative([
            ("", "เพิ่มหุ้นเข้าพอร์ตเพื่อดูบทวิเคราะห์เชิงลึก")
        ])

    def _render_risk_narrative(self, sections):
        for child in self.risk_deep_frame.winfo_children():
            child.destroy()
        self._risk_deep_labels = []

        for title, body in sections:
            if title:
                tk.Label(
                    self.risk_deep_frame,
                    text=title,
                    bg=THEME_COLORS["bg"],
                    fg=THEME_COLORS["cyan"],
                    font=("Tahoma", 11, "bold"),
                    anchor="w"
                ).pack(fill="x", padx=15, pady=(10, 2))

            body_label = tk.Label(
                self.risk_deep_frame,
                text=body,
                bg=THEME_COLORS["bg"],
                fg=THEME_COLORS["text"],
                font=("Tahoma", 10),
                justify="left",
                anchor="w",
                wraplength=max(200, self.risk_deep_frame.winfo_width() - 50)
            )
            body_label.pack(fill="x", padx=15, pady=(0, 4))
            self._risk_deep_labels.append(body_label)

        tk.Frame(
            self.risk_deep_frame, bg=THEME_COLORS["bg"], height=8
        ).pack(fill="x")

    def update_risk_deep_analysis(self, report):
        """แสดงผลวิเคราะห์เชิงลึกจาก build_portfolio_risk_report()"""
        self.reset_risk_deep_analysis()

        # ---- องค์ประกอบคะแนน ----
        self._risk_factor_data = report["factors"]
        self._draw_risk_factors()

        # ---- การ์ดเพิ่มเติม ----
        theme = report["top_theme"]
        self.metric_theme[0].config(
            text=theme["theme"][:14],
            fg=(
                THEME_COLORS["negative"] if theme["weight"] >= 70
                else THEME_COLORS["warning"] if theme["weight"] >= 50
                else THEME_COLORS["text"]
            )
        )
        self.metric_theme[1].config(text=f"{theme['weight']:.1f}% ของพอร์ต")

        sens = report["avg_sensitivity"]
        self.metric_sens[0].config(
            text=f"{sens:.2f} เท่า",
            fg=(
                THEME_COLORS["negative"] if sens >= 1.3
                else THEME_COLORS["warning"] if sens >= 1.1
                else THEME_COLORS["positive"]
            )
        )
        if report["beta_coverage"] >= 99.9:
            sens_note = "beta จริงทุกตัว (1.00 = เท่าตลาด)"
        elif report["beta_count"] > 0:
            sens_note = f"beta จริง {report['beta_count']}/{report['count']} ตัว ที่เหลือประมาณ"
        else:
            sens_note = "1.00 = เท่าตลาด (ประมาณการ)"
        self.metric_sens[1].config(text=sens_note)

        market = report["scenarios"][0]
        self.metric_stress[0].config(
            text=f"-{market['loss_pct']:.1f}%",
            fg=(
                THEME_COLORS["negative"] if market["loss_pct"] >= 25
                else THEME_COLORS["warning"] if market["loss_pct"] >= 15
                else THEME_COLORS["positive"]
            )
        )
        self.metric_stress[1].config(
            text=f"≈ {market['loss_amount']:,.0f} บาท"
        )

        # ---- ตารางรายหุ้น ----
        for s in report["stocks"]:
            notes = []
            if s["risk_share"] > s["weight"] * 1.15:
                notes.append("ส่งผลต่อความเสี่ยงมากกว่าน้ำหนัก")
            elif s["risk_share"] < s["weight"] * 0.85:
                notes.append("ผันผวนต่ำกว่าเฉลี่ยพอร์ต")
            if s["weight"] >= report["stock_cap"]:
                notes.append(f"เกินเพดาน {report['stock_cap']:.0f}%")
            if not s["known"]:
                notes.append("ไม่มีข้อมูลอุตสาหกรรม")
            if s["volatility"] is not None and s["volatility"] >= 60:
                notes.append("ผันผวนสูงมาก")
            if s["max_drawdown"] is not None and s["max_drawdown"] >= 40:
                notes.append(f"เคยลดลง {s['max_drawdown']:.0f}% จากจุดสูงสุด")
            if s["sens_source"] != "beta":
                notes.append("ความอ่อนไหวเป็นค่าประมาณ")

            if s["weight"] >= 40 or s["risk_share"] >= 45:
                tag = "high"
            elif s["weight"] >= 25 or s["risk_share"] >= 30:
                tag = "mid"
            else:
                tag = ""

            self.risk_stock_tree.insert(
                "", "end",
                values=(
                    s["symbol"],
                    f"{s['weight']:.1f}%",
                    (
                        f"{s['sensitivity']:.2f} ({s['sens_label']})"
                        if s["sens_source"] == "beta"
                        else f"~{s['sensitivity']:.2f} ({s['sens_label']})"
                    ),
                    (
                        f"{s['volatility']:.1f}%"
                        if s["volatility"] is not None else "-"
                    ),
                    (
                        f"-{s['max_drawdown']:.1f}%"
                        if s["max_drawdown"] is not None else "-"
                    ),
                    f"{s['risk_share']:.1f}%",
                    s["theme"],
                    ", ".join(notes) if notes else "-"
                ),
                tags=(tag,)
            )
        self.risk_stock_tree.configure(
            height=min(max(len(report["stocks"]), 3), 12)
        )

        # ---- ตารางธีม ----
        for t in report["themes"]:
            if t["weight"] >= 60:
                tag = "high"
            elif t["weight"] >= 40:
                tag = "mid"
            else:
                tag = ""
            self.risk_theme_tree.insert(
                "", "end",
                values=(
                    t["theme"],
                    f"{t['weight']:.1f}%",
                    f"{t['amount']:,.2f}",
                    f"{t['sensitivity']:.2f}",
                    ", ".join(t["members"])
                ),
                tags=(tag,)
            )
        self.risk_theme_tree.configure(
            height=min(max(len(report["themes"]), 2), 8)
        )

        # ---- Stress test ----
        for sc in report["scenarios"]:
            self.risk_stress_tree.insert(
                "", "end",
                values=(
                    sc["name"],
                    sc["assumption"],
                    f"-{sc['loss_pct']:.1f}%",
                    f"{sc['loss_amount']:,.0f}",
                    f"{sc['remaining']:,.0f}"
                ),
                tags=(sc["severity"],)
            )
        self.risk_stress_tree.configure(
            height=min(max(len(report["scenarios"]), 3), 10)
        )

        # ---- ปรับสมดุล ----
        for row in report["rebalance"]:
            if row["excess_amount"] > 0:
                tag = "high"
            elif row["diff"] > 5:
                tag = "mid"
            else:
                tag = ""
            self.risk_rebalance_tree.insert(
                "", "end",
                values=(
                    row["symbol"],
                    f"{row['weight']:.1f}%",
                    f"{row['equal_weight']:.1f}%",
                    f"{row['diff']:+.1f} จุด",
                    f"{row['excess_amount']:,.0f}" if row["excess_amount"] > 0 else "-"
                ),
                tags=(tag,)
            )
        self.risk_rebalance_tree.configure(
            height=min(max(len(report["rebalance"]), 3), 12)
        )

        # ---- บทวิเคราะห์ ----
        self._render_risk_narrative(report["narrative"])

    # ==================================================
    # SCROLL FUNCTIONS
    # ==================================================
    def update_risk_scrollregion(self, event=None):
        self.risk_canvas.configure(
            scrollregion=self.risk_canvas.bbox("all")
        )

    def resize_risk_scrollable_frame(self, event):
        self.risk_canvas.itemconfig(
            self.risk_canvas_window,
            width=event.width
        )

    def enable_risk_mousewheel(self, event=None):
        self.risk_canvas.bind_all(
            "<MouseWheel>",
            self.scroll_risk
        )

    def disable_risk_mousewheel(self, event=None):
        self.risk_canvas.unbind_all(
            "<MouseWheel>"
        )

    def scroll_risk(self, event):
        self.risk_canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    # ==================================================
    # ADD STOCK
    # ==================================================
    def add_portfolio_stock(self):

        symbol = (
            self.portfolio_symbol_entry
            .get()
            .strip()
            .upper()
        )

        amount_text = (
            self.portfolio_amount_entry
            .get()
            .strip()
        )

        if symbol == "":
            messagebox.showwarning(
                "แจ้งเตือน",
                "กรุณากรอกชื่อหุ้น"
            )
            return

        if amount_text == "":
            messagebox.showwarning(
                "แจ้งเตือน",
                "กรุณากรอกเงินลงทุน"
            )
            return

        try:

            amount = float(
                amount_text.replace(",", "")
            )

            if amount <= 0:
                raise ValueError

        except ValueError:

            messagebox.showwarning(
                "แจ้งเตือน",
                "เงินลงทุนต้องเป็นตัวเลขที่มากกว่า 0"
            )

            return

        # ==================================================
        # DUPLICATE CHECK
        # ==================================================
        for item in self.portfolio:

            if item["symbol"] == symbol:

                messagebox.showwarning(
                    "แจ้งเตือน",
                    f"{symbol} มีอยู่ในพอร์ตแล้ว"
                )

                return

        # ==================================================
        # GET API DATA
        # ==================================================
        stock = get_stock_data(symbol)

        if stock is None:

            messagebox.showerror(
                "เกิดข้อผิดพลาด",
                f"ไม่พบข้อมูลหุ้น {symbol}"
            )

            return

        # --------------------------------------------------
        # FALLBACK COMPANY / INDUSTRY
        # ใช้เมื่อ Finnhub ไม่ส่งข้อมูล profile ของหุ้นกลับมา
        # --------------------------------------------------
        fallback_stocks = {
            "AAPL": {"company": "Apple Inc.", "industry": "Technology"},
            "AMD": {"company": "Advanced Micro Devices", "industry": "Semiconductors"},
            "AMZN": {"company": "Amazon.com Inc.", "industry": "Retail"},
            "AVGO": {"company": "Broadcom Inc.", "industry": "Semiconductors"},
            "GOOGL": {"company": "Alphabet Inc.", "industry": "Media"},
            "GOOG": {"company": "Alphabet Inc.", "industry": "Media"},
            "META": {"company": "Meta Platforms Inc.", "industry": "Media"},
            "MSFT": {"company": "Microsoft Corp.", "industry": "Technology"},
            "MU": {"company": "Micron Technology Inc.", "industry": "Semiconductors"},
            "NBIS": {"company": "Nebius Group N.V.", "industry": "Technology"},
            "NVDA": {"company": "NVIDIA Corp.", "industry": "Semiconductors"},
            "RKLB": {"company": "Rocket Lab Corporation", "industry": "Aerospace & Defense"},
            "SMCI": {"company": "Super Micro Computer Inc.", "industry": "Technology"},
            "TSLA": {"company": "Tesla Inc.", "industry": "Automobiles"},
            "VRT": {"company": "Vertiv Holdings Co.", "industry": "Electrical Equipment"},
        }

        fallback = fallback_stocks.get(symbol, {})

        company = stock.get("company_name") or fallback.get("company") or "-"
        industry = stock.get("industry") or fallback.get("industry") or "ไม่ระบุ"

        portfolio_item = {
            "symbol": symbol,
            "company": company,
            "amount": amount,
            "industry": industry
        }

        # ==================================================
        # SAVE DATABASE
        # ==================================================
        saved = self.save_stock_to_database(
            portfolio_item
        )

        if not saved:
            return

        self.portfolio.append(
            portfolio_item
        )

        self.portfolio_symbol_entry.delete(
            0,
            tk.END
        )

        self.portfolio_amount_entry.delete(
            0,
            tk.END
        )

        self.update_portfolio()

    # ==================================================
    # EDIT SELECTED STOCK
    # ==================================================
    def edit_selected_stock(self):

        selected_items = self.portfolio_tree.selection()

        if len(selected_items) == 0:
            messagebox.showwarning(
                "แจ้งเตือน",
                "กรุณาเลือกหุ้นที่ต้องการแก้ไข"
            )
            return

        selected_item = selected_items[0]
        values = self.portfolio_tree.item(selected_item, "values")
        symbol = values[0]

        current_amount = 0
        for item in self.portfolio:
            if item["symbol"] == symbol:
                current_amount = item["amount"]
                break

        new_amount = simpledialog.askfloat(
            "แก้ไขเงินลงทุน",
            f"เงินลงทุนของ {symbol} (บาท):",
            initialvalue=current_amount,
            minvalue=0.01,
            parent=self.root
        )

        if new_amount is None:
            return

        try:
            connection = self.connect_database()
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE portfolio_holdings SET amount = ? WHERE user_id = ? AND symbol = ?",
                (new_amount, self.user_id, symbol)
            )
            connection.commit()
            connection.close()

            for item in self.portfolio:
                if item["symbol"] == symbol:
                    item["amount"] = new_amount
                    break

            self.update_portfolio()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถแก้ไขข้อมูลได้\n{error}"
            )

    # ==================================================
    # DELETE SELECTED STOCK
    # ==================================================
    def delete_selected_stock(self):

        selected_items = (
            self.portfolio_tree.selection()
        )

        if len(selected_items) == 0:

            messagebox.showwarning(
                "แจ้งเตือน",
                "กรุณาเลือกหุ้นที่ต้องการลบ"
            )

            return

        selected_item = selected_items[0]

        values = self.portfolio_tree.item(
            selected_item,
            "values"
        )

        symbol = values[0]

        self.delete_stock_from_database(
            symbol
        )

        new_portfolio = []

        for item in self.portfolio:

            if item["symbol"] != symbol:
                new_portfolio.append(item)

        self.portfolio = new_portfolio

        self.update_portfolio()

    # ==================================================
    # UPDATE PORTFOLIO
    # ==================================================
    def update_portfolio(self):

        for item in self.portfolio_tree.get_children():

            self.portfolio_tree.delete(
                item
            )

        if len(self.portfolio) == 0:

            self.risk_summary_label.config(
                text="เพิ่มหุ้นเข้าพอร์ตเพื่อเริ่มวิเคราะห์"
            )

            self.risk_gauge.set_empty()

            self.reset_risk_cards()

            self.clear_industry_table()
            self.clear_portfolio_chart()

            return

        total_amount = 0

        for item in self.portfolio:

            total_amount += item["amount"]

        # เรียงจากสัดส่วนมากไปน้อย และไฮไลต์แถวที่น้ำหนักสูง
        self.portfolio_tree.tag_configure(
            "high", foreground=THEME_COLORS["negative"]
        )
        self.portfolio_tree.tag_configure(
            "mid", foreground=THEME_COLORS["warning"]
        )

        sorted_portfolio = sorted(
            self.portfolio,
            key=lambda stock: stock["amount"],
            reverse=True
        )

        for item in sorted_portfolio:

            weight = (
                item["amount"]
                / total_amount
            ) * 100

            if weight >= 40:
                row_tag = "high"
            elif weight >= 30:
                row_tag = "mid"
            else:
                row_tag = ""

            self.portfolio_tree.insert(
                "",
                "end",
                values=(
                    item["symbol"],
                    item["company"],
                    f"{item['amount']:,.2f}",
                    f"{weight:.2f}%",
                    item["industry"]
                ),
                tags=(row_tag,)
            )

        self.analyze_portfolio_risk()

    # ==================================================
    # ANALYZE PORTFOLIO RISK
    # ==================================================
    def analyze_portfolio_risk(self, request_market=True):

        if len(self.portfolio) == 0:
            return

        # ==================================================
        # TOTAL
        # ==================================================
        total_amount = 0

        for item in self.portfolio:

            total_amount += item["amount"]

        # ==================================================
        # STOCK WEIGHTS
        # ==================================================
        stock_weights = {}

        for item in self.portfolio:

            stock_weights[item["symbol"]] = (
                item["amount"]
                / total_amount
            ) * 100

        highest_stock_symbol = ""
        highest_stock_weight = 0

        for symbol, weight in stock_weights.items():

            if weight > highest_stock_weight:

                highest_stock_weight = weight
                highest_stock_symbol = symbol

        # ==================================================
        # INDUSTRY TOTAL
        # ==================================================
        industry_totals = {}

        for item in self.portfolio:

            industry = item["industry"]

            if industry not in industry_totals:

                industry_totals[industry] = 0

            industry_totals[industry] += item["amount"]

        # ==================================================
        # INDUSTRY WEIGHTS
        # ==================================================
        industry_weights = {}

        for industry, amount in industry_totals.items():

            industry_weights[industry] = (
                amount
                / total_amount
            ) * 100

        highest_industry = ""
        highest_industry_weight = 0

        for industry, weight in industry_weights.items():

            if weight > highest_industry_weight:

                highest_industry_weight = weight
                highest_industry = industry

        # ==================================================
        # RISK LEVEL
        # คะแนนรวมจาก 5 องค์ประกอบ + เกณฑ์ขั้นต่ำแบบเดิม (ใช้ระดับที่สูงกว่า)
        # ==================================================
        stock_count = len(self.portfolio)

        report = build_portfolio_risk_report(self.portfolio, self.market_data)

        level_names = [
            "ค่อนข้างต่ำ",
            "ปานกลาง",
            "ปานกลางค่อนข้างสูง",
            "สูง"
        ]
        level_floors = [0, 35, 55, 75]

        if (
            highest_stock_weight >= 60
            or highest_industry_weight >= 70
        ):
            rule_index = 3
        elif (
            highest_stock_weight >= 40
            or highest_industry_weight >= 50
            or stock_count <= 2
        ):
            rule_index = 2
        elif (
            highest_stock_weight >= 30
            or highest_industry_weight >= 40
            or stock_count <= 4
        ):
            rule_index = 1
        else:
            rule_index = 0

        score_index = 0
        for index, floor in enumerate(level_floors):
            if report["score"] >= floor:
                score_index = index

        level_index = max(rule_index, score_index)
        risk_level = level_names[level_index]
        risk_value = max(report["score"], level_floors[level_index])

        # ==================================================
        # DETAILED RISK ANALYSIS
        # ==================================================
        risk_points = []
        risk_protection = []
        recommendations = []

        # -----------------------------
        # STOCK CONCENTRATION
        # -----------------------------
        if highest_stock_weight >= 60:

            risk_points.append(
                f"{highest_stock_symbol} มีน้ำหนัก "
                f"{highest_stock_weight:.2f}% "
                f"ทำให้พอร์ตพึ่งพาหุ้นตัวนี้สูงมาก"
            )

            recommendations.append(
                f"พิจารณาลดสัดส่วน {highest_stock_symbol} "
                f"หากต้องการลดความเสี่ยงจากหุ้นรายตัว"
            )

        elif highest_stock_weight >= 40:

            risk_points.append(
                f"{highest_stock_symbol} มีน้ำหนัก "
                f"{highest_stock_weight:.2f}% "
                f"ถือว่าค่อนข้างกระจุกตัวในหุ้นตัวเดียว"
            )

            recommendations.append(
                f"ควรติดตามความเสี่ยงของ {highest_stock_symbol} "
                f"เป็นพิเศษ"
            )

        else:

            risk_protection.append(
                f"ไม่มีหุ้นตัวใดมีน้ำหนักเกิน "
                f"{highest_stock_weight:.2f}%"
            )

        # -----------------------------
        # INDUSTRY CONCENTRATION
        # -----------------------------
        if highest_industry_weight >= 70:

            risk_points.append(
                f"อุตสาหกรรม {highest_industry} "
                f"มีสัดส่วน {highest_industry_weight:.2f}% "
                f"ทำให้พอร์ตได้รับผลกระทบจากปัจจัยของอุตสาหกรรมนี้สูง"
            )

            recommendations.append(
                "พิจารณาเพิ่มสินทรัพย์จากอุตสาหกรรมอื่น "
                "เพื่อกระจายความเสี่ยง"
            )

        elif highest_industry_weight >= 50:

            risk_points.append(
                f"อุตสาหกรรม {highest_industry} "
                f"มีสัดส่วน {highest_industry_weight:.2f}% "
                f"ค่อนข้างสูง"
            )

            recommendations.append(
                "ควรตรวจสอบว่าหุ้นในพอร์ตพึ่งพาปัจจัยเศรษฐกิจ "
                "หรืออุตสาหกรรมเดียวกันมากเกินไปหรือไม่"
            )

        elif highest_industry_weight >= 40:

            risk_points.append(
                f"อุตสาหกรรม {highest_industry} "
                f"มีสัดส่วน {highest_industry_weight:.2f}%"
            )

        else:

            risk_protection.append(
                "การกระจายตัวตามอุตสาหกรรมอยู่ในระดับหนึ่ง"
            )

        # -----------------------------
        # STOCK COUNT
        # -----------------------------
        if stock_count == 1:

            risk_points.append(
                "พอร์ตมีหุ้นเพียง 1 ตัว "
                "จึงไม่มีการกระจายความเสี่ยงระหว่างหุ้น"
            )

            recommendations.append(
                "หากเป้าหมายคือการลดความเสี่ยง "
                "ควรพิจารณากระจายการลงทุนมากกว่า 1 หุ้น"
            )

        elif stock_count == 2:

            risk_points.append(
                "พอร์ตมีเพียง 2 ตัว "
                "การกระจายความเสี่ยงยังมีจำกัด"
            )

        elif stock_count <= 4:

            risk_points.append(
                f"พอร์ตมี {stock_count} ตัว "
                "การกระจายความเสี่ยงยังไม่มากนัก"
            )

        else:

            risk_protection.append(
                f"พอร์ตมีหุ้น {stock_count} ตัว "
                "ช่วยกระจายความเสี่ยงระหว่างหุ้นได้มากขึ้น"
            )

        # ==================================================
        # EXTRA INSIGHTS (จากเอนจินวิเคราะห์เชิงลึก)
        # ==================================================
        risk_points.extend(report["extra_points"])
        risk_protection.extend(report["extra_protect"])
        recommendations.extend(report["extra_advice"])

        # ==================================================
        # DEFAULT MESSAGES
        # ==================================================
        if len(risk_points) == 0:

            risk_points.append(
                "ไม่พบการกระจุกตัวที่โดดเด่นจากเกณฑ์ที่ระบบกำหนด"
            )

        if len(risk_protection) == 0:

            risk_protection.append(
                "ยังไม่มีปัจจัยเด่นที่ช่วยลดความเสี่ยงจากโครงสร้างพอร์ต"
            )

        if len(recommendations) == 0:

            recommendations.append(
                "โครงสร้างพอร์ตอยู่ในระดับที่ค่อนข้างกระจายตัว "
                "แต่ควรติดตามสัดส่วนเมื่อมูลค่าพอร์ตเปลี่ยนแปลง"
            )

        # ==================================================
        # EXTRA METRICS (ตัวชี้วัดเพิ่มเติม)
        # ==================================================
        # น้ำหนักรวม 3 อันดับแรก
        sorted_weights = sorted(stock_weights.values(), reverse=True)
        top3_weight = sum(sorted_weights[:3])

        # HHI = ผลรวมของ (สัดส่วน%)^2 ค่าเต็ม 10,000 = หุ้นตัวเดียว
        hhi = 0
        for weight in stock_weights.values():
            hhi += weight * weight

        # จำนวนหุ้นที่แท้จริง = 10000 / HHI
        effective_stocks = 10000 / hhi

        industry_count = len(industry_totals)

        if hhi < 1500:
            hhi_note = "กระจายตัวดี"
            hhi_color = THEME_COLORS["positive"]
        elif hhi <= 2500:
            hhi_note = "กระจุกตัวปานกลาง"
            hhi_color = THEME_COLORS["warning"]
        else:
            hhi_note = "กระจุกตัวสูง"
            hhi_color = THEME_COLORS["negative"]

        if top3_weight >= 80:
            top3_color = THEME_COLORS["negative"]
        elif top3_weight >= 60:
            top3_color = THEME_COLORS["warning"]
        else:
            top3_color = THEME_COLORS["positive"]

        # สีของระดับความเสี่ยง
        level_color = [
            THEME_COLORS["positive"],
            THEME_COLORS["cyan"],
            THEME_COLORS["warning"],
            THEME_COLORS["negative"]
        ][level_index]

        # ==================================================
        # UPDATE CARDS
        # ==================================================
        self.card_total[0].config(text=f"{total_amount:,.2f}")
        self.card_total[1].config(text="บาท")

        self.card_count[0].config(text=str(stock_count))
        self.card_count[1].config(text="ตัวในพอร์ต")

        self.card_top_stock[0].config(
            text=highest_stock_symbol,
            fg=THEME_COLORS["text"]
        )
        self.card_top_stock[1].config(
            text=f"{highest_stock_weight:.2f}% ของพอร์ต"
        )

        self.card_top_industry[0].config(
            text=str(highest_industry)[:16],
            fg=THEME_COLORS["text"]
        )
        self.card_top_industry[1].config(
            text=f"{highest_industry_weight:.2f}% ของพอร์ต"
        )

        self.card_level[0].config(text=risk_level, fg=level_color)
        self.card_level[1].config(text=f"คะแนนความเสี่ยง {risk_value:.0f}/100")

        self.metric_top3[0].config(
            text=f"{top3_weight:.2f}%", fg=top3_color
        )
        self.metric_top3[1].config(text="ยิ่งสูงยิ่งพึ่งหุ้นไม่กี่ตัว")

        self.metric_effective[0].config(
            text=f"{effective_stocks:.1f} ตัว",
            fg=THEME_COLORS["text"]
        )
        self.metric_effective[1].config(
            text=f"จากที่ถืออยู่จริง {stock_count} ตัว"
        )

        self.metric_hhi[0].config(text=f"{hhi:,.0f}", fg=hhi_color)
        self.metric_hhi[1].config(text=hhi_note)

        self.metric_industry[0].config(
            text=f"{industry_count} กลุ่ม",
            fg=THEME_COLORS["text"]
        )
        self.metric_industry[1].config(text="ยิ่งมากยิ่งกระจายความเสี่ยง")

        # ==================================================
        # BUILD DETAILED SUMMARY (แยกเป็น 3 กล่อง)
        # ==================================================
        self.risk_summary_label.config(
            text=(
                f"พอร์ตนี้มีหุ้น {stock_count} ตัว "
                f"เงินลงทุนรวม {total_amount:,.2f} บาท "
                f"ประเมินว่ามีความเสี่ยงระดับ \"{risk_level}\""
            )
        )

        points_text = ""
        for reason in risk_points:
            points_text += f"• {reason}\n\n"

        protect_text = ""
        for protection in risk_protection:
            protect_text += f"• {protection}\n\n"

        advice_text = ""
        for recommendation in recommendations:
            advice_text += f"• {recommendation}\n\n"

        self.risk_points_label.config(text=points_text.strip())
        self.risk_protect_label.config(text=protect_text.strip())
        self.risk_advice_label.config(text=advice_text.strip())

        # ---------- สรุปภาษาง่ายสำหรับมาตรวัด ----------
        ranked_factors = sorted(
            report["factors"], key=lambda f: -f["contribution"]
        )
        top_theme = report["top_theme"]
        reason_map = {
            "stock": (
                f"เงินลงทุนกองอยู่ที่ {highest_stock_symbol} "
                f"ถึง {highest_stock_weight:.0f}% ของพอร์ต"
            ),
            "industry": (
                f"อุตสาหกรรม {highest_industry} มีสัดส่วน "
                f"{highest_industry_weight:.0f}% ของพอร์ต"
            ),
            "depth": (
                f"ถือ {stock_count} ตัว แต่เทียบเท่าหุ้นน้ำหนักเท่ากัน "
                f"เพียง {report['effective_stocks']:.1f} ตัว"
            ),
            "theme": (
                f"ธีม \"{top_theme['theme']}\" รวมกัน "
                f"{top_theme['weight']:.0f}% ซึ่งมักขึ้นลงตามกัน"
            ),
            "sens": (
                f"พอร์ตมีแนวโน้มแกว่งแรงกว่าตลาด "
                f"{report['avg_sensitivity']:.2f} เท่า"
            ),
        }
        level_lead = [
            "โครงสร้างพอร์ตค่อนข้างกระจายตัวดี",
            "พอร์ตอยู่ในระดับกลาง ยังมีจุดที่ปรับให้ดีขึ้นได้",
            "พอร์ตเริ่มกระจุกตัว ควรเริ่มปรับสมดุล",
            "พอร์ตกระจุกตัวสูง หากจุดหลักพลาดอาจเสียหายหนัก",
        ]
        market_case = report["scenarios"][0]
        gauge_headline = (
            f"{level_lead[level_index]}\n"
            f"จุดที่ควรดูก่อน: {reason_map[ranked_factors[0]['key']]}\n"
            f"ถ้าตลาดลง 20% พอร์ตอาจลดราว {market_case['loss_pct']:.0f}% "
            f"(≈ {market_case['loss_amount']:,.0f} บาท)"
        )

        self.risk_gauge.set_result(
            risk_value,
            risk_level,
            level_color,
            gauge_headline,
            [(f["name"], f["score"]) for f in ranked_factors[:3]]
        )

        self.update_industry_table(
            industry_totals,
            industry_weights
        )

        self.draw_portfolio_chart(
            stock_weights
        )

        self.update_risk_deep_analysis(report)

        # แสดงผลทันทีด้วยข้อมูลที่มี (แคช/ค่าประมาณ) แล้วดึงข้อมูลตลาดจริง
        # ของหุ้นที่ยังขาดใน thread แยก เมื่อเสร็จจะคำนวณและแสดงผลใหม่อีกครั้ง
        if request_market:
            self.request_market_data()
        else:
            self.update_market_status()

    # ==================================================
    # DRAW PORTFOLIO PIE CHART
    # ==================================================
    def _chart_text(self, *args, **kwargs):
        """ข้อความบนกราฟพอร์ต ใช้สีตัวอักษรของธีมมืด"""
        kwargs.setdefault("fill", THEME_COLORS["text"])
        return self.portfolio_chart.create_text(*args, **kwargs)

    def draw_portfolio_chart(self, stock_weights):
        """เริ่มแอนิเมชันกราฟโดนัทของพอร์ต"""
        job = getattr(self, "_donut_job", None)
        if job is not None:
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
            self._donut_job = None

        self._donut_step(dict(stock_weights), 0)

    def _donut_step(self, weights, step):
        steps = 22
        progress = step / steps
        eased = 1 - (1 - progress) ** 3

        self._draw_portfolio_frame(weights, eased)

        if step < steps:
            self._donut_job = self.root.after(
                25,
                lambda: self._donut_step(weights, step + 1)
            )
        else:
            self._donut_job = None

    def _draw_portfolio_frame(self, stock_weights, progress=1.0):

        self.portfolio_chart.delete("all")

        if len(stock_weights) == 0:
            return

        canvas_width = 800
        canvas_height = 420

        center_x = 250
        center_y = 210

        radius = 145

        chart_colors = [
            "#4C7DFF",
            "#38D6F0",
            "#8B7CFF",
            "#34D399",
            "#F5A524",
            "#F87171",
            "#6C93FF",
            "#B39DFF",
            "#5EEAD4",
            "#FBBF24"
        ]

        start_angle = 0

        sorted_stocks = sorted(
            stock_weights.items(),
            key=lambda item: item[1],
            reverse=True
        )

        legend_x = 470
        legend_y = 70

        for index, (symbol, weight) in enumerate(
            sorted_stocks
        ):

            extent = (
                weight
                / 100
            ) * 360 * progress

            color = chart_colors[
                index % len(chart_colors)
            ]

            self.portfolio_chart.create_arc(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                start=start_angle,
                extent=extent,
                fill=color,
                outline=THEME_COLORS["surface"],
                width=2
            )

            legend_box_size = 18

            self.portfolio_chart.create_rectangle(
                legend_x,
                legend_y,
                legend_x + legend_box_size,
                legend_y + legend_box_size,
                fill=color,
                outline=""
            )

            self._chart_text(
                legend_x + 28,
                legend_y + 9,
                text=(
                    f"{symbol}  "
                    f"{weight:.2f}%"
                ),
                anchor="w",
                font=("Tahoma", 11)
            )

            start_angle += extent
            legend_y += 38

        self.portfolio_chart.create_oval(
            center_x - 60,
            center_y - 60,
            center_x + 60,
            center_y + 60,
            fill=THEME_COLORS["surface"],
            outline=THEME_COLORS["surface"]
        )

        total_stocks = len(stock_weights)

        self._chart_text(
            center_x,
            center_y - 8,
            text=str(total_stocks),
            font=("Tahoma", 20, "bold")
        )

        self._chart_text(
            center_x,
            center_y + 18,
            text="หุ้น",
            font=("Tahoma", 11)
        )

        self._chart_text(
            250,
            385,
            text="สัดส่วนเงินลงทุนของแต่ละหุ้น",
            font=("Tahoma", 12)
        )

    # ==================================================
    # CLEAR PORTFOLIO CHART
    # ==================================================
    def clear_portfolio_chart(self):

        job = getattr(self, "_donut_job", None)
        if job is not None:
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
            self._donut_job = None

        self.portfolio_chart.delete(
            "all"
        )

        self._chart_text(
            400,
            210,
            text="เพิ่มหุ้นเข้าพอร์ตเพื่อแสดงกราฟ",
            font=("Tahoma", 14)
        )

    # ==================================================
    # INDUSTRY TABLE
    # ==================================================
    def update_industry_table(
        self,
        industry_totals,
        industry_weights
    ):

        self.clear_industry_table()

        sorted_industries = sorted(
            industry_totals.items(),
            key=lambda item: item[1],
            reverse=True
        )

        self.start_industry_bars(
            sorted_industries,
            industry_weights
        )

        for industry, amount in sorted_industries:

            weight = industry_weights[
                industry
            ]

            self.industry_tree.insert(
                "",
                "end",
                values=(
                    industry,
                    f"{amount:,.2f}",
                    f"{weight:.2f}%"
                )
            )

    # ==================================================
    # CLEAR INDUSTRY TABLE
    # ==================================================
    def clear_industry_table(self):

        job = getattr(self, "_industry_job", None)
        if job is not None:
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
            self._industry_job = None

        if hasattr(self, "industry_chart"):
            self.industry_chart.delete("all")

        for item in self.industry_tree.get_children():

            self.industry_tree.delete(
                item
            )

    # ==================================================
    # CLEAR PORTFOLIO
    # ==================================================
    def clear_portfolio(self):

        if len(self.portfolio) == 0:
            return

        confirm = messagebox.askyesno(
            "ยืนยัน",
            "ต้องการล้างหุ้นทั้งหมดออกจากพอร์ตหรือไม่?"
        )

        if not confirm:
            return

        self.clear_database()

        self.portfolio.clear()

        for item in self.portfolio_tree.get_children():

            self.portfolio_tree.delete(
                item
            )

        self.clear_industry_table()
        self.clear_portfolio_chart()

        self.risk_summary_label.config(
            text="เพิ่มหุ้นเข้าพอร์ตเพื่อเริ่มวิเคราะห์"
        )

        self.risk_gauge.set_empty()

        self.reset_risk_cards()

    # ==================================================
    # PAGE 3 : TRADE PROFIT / LOSS CALENDAR
    # ==================================================
    def create_trade_calendar_page(self):

        self.trade_calendar_year = datetime.now().year
        self.trade_calendar_month = datetime.now().month
        self.selected_trade_date = datetime.now().strftime("%Y-%m-%d")
        self.calendar_cells = {}

        self.trade_scroll_canvas = tk.Canvas(
            self.trade_page,
            highlightthickness=0
        )
        self.trade_scroll_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            self.trade_page,
            orient="vertical",
            command=self.trade_scroll_canvas.yview
        )
        scrollbar.pack(
            side="right",
            fill="y"
        )

        trade_content = ttk.Frame(
            self.trade_scroll_canvas
        )
        trade_window = self.trade_scroll_canvas.create_window(
            (0, 0),
            window=trade_content,
            anchor="nw"
        )

        self.trade_scroll_canvas.configure(
            yscrollcommand=scrollbar.set
        )

        def update_scroll_region(event=None):
            self.trade_scroll_canvas.configure(
                scrollregion=self.trade_scroll_canvas.bbox("all")
            )

        def resize_content(event):
            self.trade_scroll_canvas.itemconfig(
                trade_window,
                width=event.width
            )

        trade_content.bind(
            "<Configure>",
            update_scroll_region
        )
        self.trade_scroll_canvas.bind(
            "<Configure>",
            resize_content
        )

        def is_trade_tab_active():
            try:
                selected = self.notebook.select()
                return (
                    self.notebook.tab(selected, "text")
                    == "บันทึกกำไรขาดทุน"
                )
            except tk.TclError:
                return False

        def scroll_with_mouse(event):
            if is_trade_tab_active() and event.delta != 0:
                self.trade_scroll_canvas.yview_scroll(
                    int(-event.delta / 120),
                    "units"
                )

        def scroll_with_mouse_linux_up(event):
            if is_trade_tab_active():
                self.trade_scroll_canvas.yview_scroll(
                    -1,
                    "units"
                )

        def scroll_with_mouse_linux_down(event):
            if is_trade_tab_active():
                self.trade_scroll_canvas.yview_scroll(
                    1,
                    "units"
                )

        self.trade_scroll_canvas.bind_all(
            "<MouseWheel>",
            scroll_with_mouse
        )
        self.trade_scroll_canvas.bind_all(
            "<Button-4>",
            scroll_with_mouse_linux_up
        )
        self.trade_scroll_canvas.bind_all(
            "<Button-5>",
            scroll_with_mouse_linux_down
        )

        self.trade_page_content = trade_content

        self.trade_banner = AnimatedBanner(
            trade_content,
            "ปฏิทินกำไรขาดทุน",
            "คลิกวันที่เพื่อดูรายการซื้อขาย กำไร/ขาดทุน และหุ้นคงเหลือ",
            seed=37,
            tag="TRADE JOURNAL"
        )
        self.trade_banner.pack(fill="x", padx=35, pady=(22, 12))

        # ==================================================
        # TRANSACTION INPUT
        # ==================================================
        input_frame = ttk.LabelFrame(
            trade_content,
            text="บันทึกรายการซื้อ / ขาย"
        )
        input_frame.pack(
            fill="x",
            padx=35,
            pady=10
        )

        self.trade_selected_date_label = ttk.Label(
            input_frame,
            text="วันที่เลือก: " + self.selected_trade_date,
            font=("Tahoma", 12, "bold")
        )
        self.trade_selected_date_label.grid(
            row=0,
            column=0,
            columnspan=6,
            padx=10,
            pady=(10, 5),
            sticky="w"
        )

        ttk.Label(
            input_frame,
            text="หุ้น",
            style="Normal.TLabel"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=10,
            sticky="w"
        )

        self.trade_symbol_entry = ttk.Entry(
            input_frame,
            width=14,
            font=("Tahoma", 11)
        )
        self.trade_symbol_entry.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )

        ttk.Label(
            input_frame,
            text="ประเภท",
            style="Normal.TLabel"
        ).grid(
            row=1,
            column=2,
            padx=10,
            pady=10,
            sticky="w"
        )

        self.trade_type_combo = ttk.Combobox(
            input_frame,
            values=("ซื้อ", "ขาย"),
            state="readonly",
            width=10,
            font=("Tahoma", 11)
        )
        self.trade_type_combo.grid(
            row=1,
            column=3,
            padx=10,
            pady=10
        )
        self.trade_type_combo.set("ซื้อ")

        ttk.Label(
            input_frame,
            text="จำนวนหุ้น",
            style="Normal.TLabel"
        ).grid(
            row=1,
            column=4,
            padx=10,
            pady=10,
            sticky="w"
        )

        self.trade_quantity_entry = ttk.Entry(
            input_frame,
            width=16,
            font=("Tahoma", 11)
        )
        self.trade_quantity_entry.grid(
            row=1,
            column=5,
            padx=10,
            pady=10
        )

        ttk.Label(
            input_frame,
            text="ราคาต่อหุ้น (USD)",
            style="Normal.TLabel"
        ).grid(
            row=2,
            column=0,
            padx=10,
            pady=10,
            sticky="w"
        )

        self.trade_price_entry = ttk.Entry(
            input_frame,
            width=16,
            font=("Tahoma", 11)
        )
        self.trade_price_entry.grid(
            row=2,
            column=1,
            padx=10,
            pady=10
        )

        ttk.Label(
            input_frame,
            text="หมายเหตุ",
            style="Normal.TLabel"
        ).grid(
            row=2,
            column=2,
            padx=10,
            pady=10,
            sticky="w"
        )

        self.trade_note_entry = ttk.Entry(
            input_frame,
            width=28,
            font=("Tahoma", 11)
        )
        self.trade_note_entry.grid(
            row=2,
            column=3,
            columnspan=3,
            padx=10,
            pady=10,
            sticky="ew"
        )

        input_frame.columnconfigure(
            5,
            weight=1
        )

        button_frame = ttk.Frame(
            trade_content
        )
        button_frame.pack(
            pady=8
        )

        ttk.Button(
            button_frame,
            text="บันทึกการซื้อ/ขาย",
            command=self.save_trade_transaction
        ).grid(
            row=0,
            column=0,
            padx=6
        )

        ttk.Button(
            button_frame,
            text="ล้างข้อมูล",
            command=self.clear_trade_form
        ).grid(
            row=0,
            column=1,
            padx=6
        )

        ttk.Button(
            button_frame,
            text="ลบรายการที่เลือก",
            command=self.delete_trade_transaction
        ).grid(
            row=0,
            column=2,
            padx=6
        )

        # ==================================================
        # MONTH NAVIGATION
        # ==================================================
        month_frame = ttk.Frame(
            trade_content
        )
        month_frame.pack(
            fill="x",
            padx=35,
            pady=(15, 8)
        )

        ttk.Button(
            month_frame,
            text="‹ เดือนก่อน",
            command=self.previous_trade_month
        ).pack(
            side="left"
        )

        self.trade_month_label = ttk.Label(
            month_frame,
            text="",
            font=("Tahoma", 18, "bold")
        )
        self.trade_month_label.pack(
            side="left",
            expand=True
        )

        ttk.Button(
            month_frame,
            text="เดือนปัจจุบัน",
            command=self.current_trade_month
        ).pack(
            side="right",
            padx=5
        )

        ttk.Button(
            month_frame,
            text="เดือนถัดไป ›",
            command=self.next_trade_month
        ).pack(
            side="right"
        )

        ttk.Button(
            month_frame,
            text="สรุปกำไร–ขาดทุนการลงทุน",
            command=self.show_investment_summary
        ).pack(
            side="right",
            padx=10
        )

        # ==================================================
        # CALENDAR
        # ==================================================
        calendar_frame = ttk.LabelFrame(
            trade_content,
            text="ปฏิทินการซื้อขาย"
        )
        calendar_frame.pack(
            fill="x",
            padx=35,
            pady=5
        )

        self.calendar_grid = ttk.Frame(
            calendar_frame
        )
        self.calendar_grid.pack(
            fill="x",
            padx=8,
            pady=8
        )

        weekdays = [
            "จันทร์",
            "อังคาร",
            "พุธ",
            "พฤหัสบดี",
            "ศุกร์",
            "เสาร์",
            "อาทิตย์"
        ]

        for column, weekday in enumerate(weekdays):
            ttk.Label(
                self.calendar_grid,
                text=weekday,
                anchor="center",
                font=("Tahoma", 10, "bold")
            ).grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=2,
                pady=2
            )
            self.calendar_grid.columnconfigure(
                column,
                weight=1,
                minsize=100
            )

        # กำหนดความสูงของแถวปฏิทินให้เห็นช่องวันที่ชัดเจน
        for row in range(1, 7):
            self.calendar_grid.rowconfigure(
                row,
                minsize=92
            )

        # ==================================================
        # MONTH SUMMARY
        # ==================================================
        summary_frame = ttk.LabelFrame(
            trade_content,
            text="สรุปผลการซื้อขายของเดือน"
        )
        summary_frame.pack(
            fill="x",
            padx=35,
            pady=(0, 10)
        )

        self.trade_summary_label = ttk.Label(
            summary_frame,
            text="",
            style="Normal.TLabel",
            justify="left"
        )
        self.trade_summary_label.pack(
            anchor="w",
            padx=15,
            pady=(8, 5)
        )

        self.month_chart = tk.Canvas(
            summary_frame,
            height=190,
            bg=THEME_COLORS["surface"],
            highlightthickness=0
        )
        self.month_chart.pack(
            fill="x",
            padx=15,
            pady=(4, 10)
        )
        self.month_chart.bind(
            "<Configure>",
            lambda event: self._draw_month_chart(1.0)
            if hasattr(self, "_month_chart_data") else None
        )

        exchange_frame = ttk.Frame(summary_frame)
        exchange_frame.pack(
            fill="x",
            padx=15,
            pady=(0, 12)
        )

        ttk.Label(
            exchange_frame,
            text="อัตราแลกเปลี่ยนเดือนนี้: 1 USD =",
            style="Normal.TLabel"
        ).pack(
            side="left"
        )

        self.trade_exchange_rate_entry = ttk.Entry(
            exchange_frame,
            width=14,
            font=("Tahoma", 11)
        )
        self.trade_exchange_rate_entry.pack(
            side="left",
            padx=(8, 5)
        )

        ttk.Label(
            exchange_frame,
            text="บาท",
            style="Normal.TLabel"
        ).pack(
            side="left"
        )

        ttk.Button(
            exchange_frame,
            text="บันทึกค่าเงิน",
            command=self.save_trade_exchange_rate
        ).pack(
            side="left",
            padx=10
        )

        self.trade_exchange_rate_status = ttk.Label(
            exchange_frame,
            text="กรอกค่าเงินดอลลาร์ก่อน เพื่อคำนวณกำไรสุทธิเป็นบาท",
            style="Normal.TLabel"
        )
        self.trade_exchange_rate_status.pack(
            side="left",
            padx=5
        )

        # ==================================================
        # CURRENT HOLDINGS
        # ==================================================
        holdings_frame = ttk.LabelFrame(
            trade_content,
            text="หุ้นที่ถืออยู่ในปัจจุบัน"
        )
        holdings_frame.pack(
            fill="x",
            padx=35,
            pady=(5, 10)
        )

        self.holdings_status_label = ttk.Label(
            holdings_frame,
            text="",
            style="Normal.TLabel"
        )
        self.holdings_status_label.pack(
            anchor="w",
            padx=12,
            pady=(8, 2)
        )

        holdings_columns = (
            "symbol",
            "quantity",
            "avg_cost",
            "total_cost"
        )

        self.holdings_tree = ttk.Treeview(
            holdings_frame,
            columns=holdings_columns,
            show="headings",
            height=6
        )

        holdings_headings = {
            "symbol": "หุ้น",
            "quantity": "จำนวนหุ้น",
            "avg_cost": "ต้นทุนเฉลี่ย/หุ้น (USD)",
            "total_cost": "ต้นทุนรวม (USD)"
        }

        holdings_widths = {
            "symbol": 110,
            "quantity": 140,
            "avg_cost": 190,
            "total_cost": 180
        }

        for column in holdings_columns:
            self.holdings_tree.heading(
                column,
                text=holdings_headings[column]
            )
            self.holdings_tree.column(
                column,
                width=holdings_widths[column],
                anchor="center" if column == "symbol" else "e"
            )

        self.holdings_tree.pack(
            fill="x",
            padx=10,
            pady=(2, 10)
        )

        # ==================================================
        # SELECTED DAY
        # ==================================================
        records_frame = ttk.LabelFrame(
            trade_content,
            text="รายการของวันที่เลือก"
        )
        records_frame.pack(
            fill="x",
            padx=35,
            pady=(10, 10)
        )

        self.selected_date_label = ttk.Label(
            records_frame,
            text="",
            style="Normal.TLabel"
        )
        self.selected_date_label.pack(
            anchor="w",
            padx=10,
            pady=(10, 5)
        )

        columns = (
            "id",
            "type",
            "symbol",
            "quantity",
            "amount",
            "price",
            "pnl",
            "remaining",
            "note"
        )

        self.trade_tree = ttk.Treeview(
            records_frame,
            columns=columns,
            show="headings",
            height=9
        )

        headings = {
            "id": "ID",
            "type": "รายการ",
            "symbol": "หุ้น",
            "quantity": "จำนวนหุ้น",
            "amount": "จำนวนเงิน (USD)",
            "price": "ราคา/หุ้น (USD)",
            "pnl": "กำไร/ขาดทุน (USD)",
            "remaining": "หุ้นคงเหลือ",
            "note": "หมายเหตุ"
        }

        widths = {
            "id": 50,
            "type": 80,
            "symbol": 90,
            "quantity": 100,
            "amount": 125,
            "price": 110,
            "pnl": 125,
            "remaining": 110,
            "note": 220
        }

        for column in columns:
            self.trade_tree.heading(
                column,
                text=headings[column]
            )
            self.trade_tree.column(
                column,
                width=widths[column],
                anchor="center" if column in (
                    "id",
                    "type",
                    "symbol"
                ) else "e"
            )

        self.trade_tree.column(
            "note",
            anchor="w"
        )

        self.trade_tree.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

        self.trade_tree.bind(
            "<<TreeviewSelect>>",
            self.on_trade_tree_select
        )
        self.trade_tree.bind(
            "<ButtonRelease-1>",
            self.on_trade_tree_click
        )

        # ==================================================
        # MONTH TRANSACTION SUMMARY
        # ==================================================
        month_records_frame = ttk.LabelFrame(
            trade_content,
            text="รายการซื้อขายภายในเดือน"
        )
        month_records_frame.pack(
            fill="x",
            padx=35,
            pady=(5, 25)
        )

        columns = (
            "date",
            "type",
            "symbol",
            "quantity",
            "amount",
            "pnl",
            "remaining"
        )

        self.month_trade_tree = ttk.Treeview(
            month_records_frame,
            columns=columns,
            show="headings",
            height=10
        )

        headings = {
            "date": "วันที่",
            "type": "รายการ",
            "symbol": "หุ้น",
            "quantity": "จำนวนหุ้น",
            "amount": "จำนวนเงิน (USD)",
            "pnl": "กำไร/ขาดทุน (USD)",
            "remaining": "หุ้นคงเหลือ"
        }

        for column in columns:
            self.month_trade_tree.heading(
                column,
                text=headings[column]
            )

        self.month_trade_tree.column(
            "date",
            width=110,
            anchor="center"
        )
        self.month_trade_tree.column(
            "type",
            width=80,
            anchor="center"
        )
        self.month_trade_tree.column(
            "symbol",
            width=90,
            anchor="center"
        )
        self.month_trade_tree.column(
            "quantity",
            width=110,
            anchor="e"
        )
        self.month_trade_tree.column(
            "amount",
            width=130,
            anchor="e"
        )
        self.month_trade_tree.column(
            "pnl",
            width=130,
            anchor="e"
        )
        self.month_trade_tree.column(
            "remaining",
            width=120,
            anchor="e"
        )

        self.month_trade_tree.pack(
            fill="x",
            padx=10,
            pady=10
        )

        self.month_trade_tree.bind(
            "<<TreeviewSelect>>",
            self.on_month_trade_tree_select
        )
        self.month_trade_tree.bind(
            "<ButtonRelease-1>",
            self.on_month_trade_tree_click
        )

    def on_month_trade_tree_select(self, event=None):
        """เก็บ ID ของรายการที่เลือกจากตารางทั้งเดือน"""
        selected_items = self.month_trade_tree.selection()

        if len(selected_items) == 0:
            return

        record_id = self.month_trade_tree.item(
            selected_items[0],
            "iid"
        )

        if record_id:
            self.selected_trade_record_id = str(record_id)

        if hasattr(self, "trade_tree"):
            self.trade_tree.selection_remove(
                self.trade_tree.selection()
            )

    def on_month_trade_tree_click(self, event=None):
        """รับ ID จากแถวที่คลิกโดยตรง เพื่อให้ปุ่มลบใช้ ID ได้แน่นอน"""
        if event is None:
            return

        item_id = self.month_trade_tree.identify_row(event.y)

        if not item_id:
            return

        self.selected_trade_record_id = str(item_id)

        self.month_trade_tree.selection_set(item_id)
        self.month_trade_tree.focus(item_id)

        if hasattr(self, "trade_tree"):
            self.trade_tree.selection_remove(
                self.trade_tree.selection()
            )

    def calculate_current_holdings(self, records=None):
        """
        คำนวณหุ้นที่ถืออยู่ในปัจจุบันจากประวัติการซื้อขายทั้งหมด
        ใช้ต้นทุนแบบ FIFO เพื่อหาต้นทุนของหุ้นที่ยังเหลือ
        """
        if records is None:
            records = self.get_all_trade_transactions()

        lots = {}

        for record in records:
            (
                record_id,
                trade_date,
                symbol,
                transaction_type,
                quantity,
                total_amount,
                note
            ) = record

            symbol = str(symbol).upper()
            quantity = float(quantity)
            total_amount = float(total_amount)

            if symbol not in lots:
                lots[symbol] = []

            if transaction_type == "ซื้อ":
                unit_cost = (
                    total_amount / quantity
                    if quantity > 0
                    else 0.0
                )

                lots[symbol].append({
                    "quantity": quantity,
                    "remaining": quantity,
                    "unit_cost": unit_cost
                })

            elif transaction_type == "ขาย":
                remaining_to_sell = quantity

                for lot in lots[symbol]:
                    if remaining_to_sell <= 0:
                        break

                    if lot["remaining"] <= 0:
                        continue

                    matched_quantity = min(
                        remaining_to_sell,
                        lot["remaining"]
                    )

                    lot["remaining"] -= matched_quantity
                    remaining_to_sell -= matched_quantity

        holdings = []

        for symbol, symbol_lots in lots.items():
            quantity = 0.0
            total_cost = 0.0

            for lot in symbol_lots:
                if lot["remaining"] <= 0:
                    continue

                quantity += lot["remaining"]
                total_cost += (
                    lot["remaining"] * lot["unit_cost"]
                )

            if quantity > 0:
                average_cost = total_cost / quantity

                holdings.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "average_cost": average_cost,
                    "total_cost": total_cost
                })

        holdings.sort(
            key=lambda item: item["symbol"]
        )

        return holdings

    def refresh_current_holdings(self):
        """รีเฟรชตารางหุ้นที่ถืออยู่ในปัจจุบัน"""
        if not hasattr(self, "holdings_tree"):
            return

        for item in self.holdings_tree.get_children():
            self.holdings_tree.delete(item)

        records = self.get_all_trade_transactions()
        holdings = self.calculate_current_holdings(records)

        if not holdings:
            self.holdings_status_label.config(
                text="ขณะนี้ไม่มีหุ้นที่ถืออยู่"
            )
            return

        total_cost = 0.0
        total_quantity = 0.0

        for holding in holdings:
            quantity = holding["quantity"]
            average_cost = holding["average_cost"]
            holding_cost = holding["total_cost"]

            total_quantity += quantity
            total_cost += holding_cost

            quantity_text = (
                f"{quantity:,.4f}".rstrip("0").rstrip(".")
            )

            self.holdings_tree.insert(
                "",
                "end",
                values=(
                    holding["symbol"],
                    quantity_text,
                    f"{average_cost:,.4f}",
                    f"{holding_cost:,.2f}"
                )
            )

        self.holdings_status_label.config(
            text=(
                f"ถืออยู่ {len(holdings)} หุ้น"
                f"    |    "
                f"จำนวนรวม {total_quantity:,.4f} หุ้น"
                f"    |    "
                f"ต้นทุนรวม {total_cost:,.2f} USD"
            )
        )

    # ==================================================
    # TRADE TRANSACTION DATABASE
    # ==================================================
    def get_all_trade_transactions(self):
        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    trade_date,
                    symbol,
                    transaction_type,
                    quantity,
                    total_amount,
                    note
                FROM trade_transactions
                WHERE user_id = ?
                ORDER BY trade_date ASC, id ASC
                """, (self.user_id,)
            )

            records = cursor.fetchall()
            connection.close()

            return records

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถโหลดรายการซื้อขายได้\n{error}"
            )
            return []

    def calculate_trade_matches(
        self,
        records=None
    ):
        """
        คำนวณกำไร/ขาดทุนจากการขายด้วยวิธี FIFO
        โดยไม่แก้ข้อมูลดิบในฐานข้อมูล
        """
        if records is None:
            records = self.get_all_trade_transactions()

        lots = {}
        sell_results = {}
        invalid_sales = []

        for record in records:
            (
                record_id,
                trade_date,
                symbol,
                transaction_type,
                quantity,
                total_amount,
                note
            ) = record

            symbol = symbol.upper()
            quantity = float(quantity)
            total_amount = float(total_amount)

            if symbol not in lots:
                lots[symbol] = []

            if transaction_type == "ซื้อ":
                unit_cost = (
                    total_amount / quantity
                    if quantity != 0
                    else 0
                )

                lots[symbol].append({
                    "record_id": record_id,
                    "date": trade_date,
                    "quantity": quantity,
                    "remaining": quantity,
                    "unit_cost": unit_cost
                })

            elif transaction_type == "ขาย":
                remaining_to_sell = quantity
                sale_unit_price = (
                    total_amount / quantity
                    if quantity != 0
                    else 0
                )
                realized_pnl = 0.0

                for lot in lots[symbol]:
                    if remaining_to_sell <= 0:
                        break

                    if lot["remaining"] <= 0:
                        continue

                    matched_quantity = min(
                        remaining_to_sell,
                        lot["remaining"]
                    )

                    cost = (
                        matched_quantity
                        * lot["unit_cost"]
                    )
                    proceeds = (
                        matched_quantity
                        * sale_unit_price
                    )

                    realized_pnl += (
                        proceeds - cost
                    )

                    lot["remaining"] -= matched_quantity
                    remaining_to_sell -= matched_quantity

                if remaining_to_sell > 0:
                    invalid_sales.append({
                        "id": record_id,
                        "date": trade_date,
                        "symbol": symbol,
                        "quantity": quantity,
                        "unmatched": remaining_to_sell
                    })

                sell_results[record_id] = realized_pnl

        return sell_results, invalid_sales

    def calculate_remaining_positions(self, records=None):
        """คำนวณจำนวนหุ้นคงเหลือหลังรายการแต่ละรายการ รองรับการขายบางส่วน"""
        if records is None:
            records = self.get_all_trade_transactions()

        positions = {}
        remaining_after = {}

        for record in records:
            record_id, trade_date, symbol, transaction_type, quantity, total_amount, note = record
            symbol = symbol.upper()
            quantity = float(quantity)

            if symbol not in positions:
                positions[symbol] = 0.0

            if transaction_type == "ซื้อ":
                positions[symbol] += quantity
            elif transaction_type == "ขาย":
                positions[symbol] -= quantity

            remaining_after[record_id] = max(0.0, positions[symbol])

        return remaining_after

    def save_trade_transaction(self):

        # วันที่มาจากวันที่ผู้ใช้คลิกบนปฏิทินโดยตรง
        trade_date = self.selected_trade_date
        symbol = self.trade_symbol_entry.get().strip().upper()
        transaction_type = self.trade_type_combo.get().strip()
        note = self.trade_note_entry.get().strip()

        if symbol == "":
            messagebox.showwarning(
                "ข้อมูลไม่ครบ",
                "กรุณากรอกชื่อหุ้น"
            )
            return

        if transaction_type not in ("ซื้อ", "ขาย"):
            messagebox.showwarning(
                "ข้อมูลไม่ครบ",
                "กรุณาเลือกว่ารายการนี้เป็นการซื้อหรือขาย"
            )
            return

        try:
            quantity = float(
                self.trade_quantity_entry.get().replace(",", "")
            )
            price_per_share = float(
                self.trade_price_entry.get().replace(",", "")
            )
        except (ValueError, TypeError):
            messagebox.showwarning(
                "ข้อมูลไม่ถูกต้อง",
                "จำนวนหุ้นและราคาต่อหุ้นต้องเป็นตัวเลข"
            )
            return

        if quantity <= 0:
            messagebox.showwarning(
                "ข้อมูลไม่ถูกต้อง",
                "จำนวนหุ้นต้องมากกว่า 0"
            )
            return

        if price_per_share <= 0:
            messagebox.showwarning(
                "ข้อมูลไม่ถูกต้อง",
                "ราคาต่อหุ้นต้องมากกว่า 0"
            )
            return

        # คำนวณมูลค่ารายการอัตโนมัติจาก จำนวนหุ้น × ราคาต่อหุ้น
        total_amount = quantity * price_per_share

        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    trade_date,
                    symbol,
                    transaction_type,
                    quantity,
                    total_amount,
                    note
                FROM trade_transactions
                WHERE user_id = ?
                ORDER BY trade_date ASC, id ASC
                """, (self.user_id,)
            )

            existing_records = cursor.fetchall()

            temporary_id = -1
            candidate = (
                temporary_id,
                trade_date,
                symbol,
                transaction_type,
                quantity,
                total_amount,
                note
            )

            test_records = existing_records + [candidate]
            test_records.sort(
                key=lambda record: (
                    record[1],
                    record[0]
                )
            )

            _, invalid_sales = self.calculate_trade_matches(
                test_records
            )

            candidate_invalid = any(
                item["id"] == temporary_id
                for item in invalid_sales
            )

            if candidate_invalid:
                connection.close()

                messagebox.showwarning(
                    "จำนวนหุ้นไม่เพียงพอ",
                    (
                        f"ไม่สามารถขาย {symbol} "
                        f"{quantity:,.4f} หุ้นได้\n"
                        "เพราะจำนวนหุ้นที่ซื้อไว้ก่อนวันขายไม่เพียงพอ"
                    )
                )
                return

            cursor.execute(
                """
                INSERT INTO trade_transactions
                (
                    user_id,
                    trade_date,
                    symbol,
                    transaction_type,
                    quantity,
                    total_amount,
                    note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    trade_date,
                    symbol,
                    transaction_type,
                    quantity,
                    total_amount,
                    note
                )
            )

            connection.commit()
            connection.close()

            selected_date = datetime.strptime(
                trade_date,
                "%Y-%m-%d"
            )

            self.trade_calendar_year = selected_date.year
            self.trade_calendar_month = selected_date.month
            self.selected_trade_date = trade_date

            self.clear_trade_form(
                keep_date=True
            )

            self.refresh_trade_calendar()

            if hasattr(self, "trade_symbol_entry"):
                self.trade_symbol_entry.focus_set()

            if transaction_type == "ขาย":
                all_records = self.get_all_trade_transactions()
                sell_results, _ = self.calculate_trade_matches(
                    all_records
                )

                saved_record = max(
                    all_records,
                    key=lambda item: item[0]
                )

                realized_pnl = sell_results.get(
                    saved_record[0],
                    0.0
                )

                messagebox.showinfo(
                    "บันทึกสำเร็จ",
                    (
                        f"ขาย {symbol} {quantity:,.4f} หุ้น\n"
                        f"ยอดขาย {total_amount:,.2f} USD\n"
                        f"กำไร/ขาดทุนที่รับรู้ "
                        f"{realized_pnl:+,.2f} USD"
                    )
                )
            else:
                unit_price = total_amount / quantity

                messagebox.showinfo(
                    "บันทึกสำเร็จ",
                    (
                        f"ซื้อ {symbol} {quantity:,.4f} หุ้น\n"
                        f"จำนวนเงิน {total_amount:,.2f} USD\n"
                        f"ราคาเฉลี่ย {unit_price:,.4f} USD/หุ้น"
                    )
                )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถบันทึกรายการได้\n{error}"
            )

    def delete_trade_transaction(self):
        """ลบรายการซื้อขายที่ผู้ใช้เลือก"""

        # ใช้ ID ที่เก็บไว้ตอนผู้ใช้คลิกแถวเป็นตัวหลัก
        record_id = getattr(
            self,
            "selected_trade_record_id",
            None
        )

        # ถ้ายังไม่มี ID ค่อยตรวจจากตารางรายวัน
        if record_id is None and hasattr(self, "trade_tree"):
            selected_items = self.trade_tree.selection()

            if selected_items:
                record_id = self.trade_tree.item(
                    selected_items[0],
                    "iid"
                )

        # ถ้ายังไม่มี ID ค่อยตรวจจากตารางทั้งเดือน
        if record_id is None and hasattr(self, "month_trade_tree"):
            selected_items = self.month_trade_tree.selection()

            if selected_items:
                record_id = self.month_trade_tree.item(
                    selected_items[0],
                    "iid"
                )

        # ใช้ focus เป็นตัวช่วยสุดท้าย
        if record_id is None and hasattr(self, "trade_tree"):
            selected_item = self.trade_tree.focus()

            if selected_item:
                record_id = selected_item

        if record_id is None and hasattr(self, "month_trade_tree"):
            selected_item = self.month_trade_tree.focus()

            if selected_item:
                record_id = selected_item

        if record_id is None or str(record_id).strip() == "":
            self.selected_trade_record_id = None
            messagebox.showwarning(
                "แจ้งเตือน",
                "กรุณาคลิกเลือกรายการที่ต้องการลบก่อน"
            )
            return

        try:
            record_id = int(record_id)
        except (ValueError, TypeError):
            messagebox.showerror(
                "Database Error",
                "ไม่สามารถระบุ ID ของรายการที่เลือกได้"
            )
            return

        if not messagebox.askyesno(
            "ยืนยันการลบ",
            f"ต้องการลบรายการ ID {record_id} หรือไม่?\n\n"
            "ข้อมูลกำไร/ขาดทุนและจำนวนหุ้นจะถูกคำนวณใหม่หลังลบ"
        ):
            return

        connection = None

        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            # เช็กก่อนว่ารายการนี้มีอยู่และเป็นของผู้ใช้คนนี้
            cursor.execute(
                """
                SELECT id
                FROM trade_transactions
                WHERE id = ? AND user_id = ?
                """,
                (record_id, self.user_id)
            )

            row = cursor.fetchone()

            if row is None:
                connection.rollback()
                self.selected_trade_record_id = None
                messagebox.showwarning(
                    "แจ้งเตือน",
                    "ไม่พบรายการที่เลือกในฐานข้อมูล"
                )
                return

            cursor.execute(
                """
                DELETE FROM trade_transactions
                WHERE id = ? AND user_id = ?
                """,
                (record_id, self.user_id)
            )

            if cursor.rowcount != 1:
                connection.rollback()
                messagebox.showwarning(
                    "แจ้งเตือน",
                    "ไม่สามารถลบรายการที่เลือกได้"
                )
                return

            connection.commit()
            self.selected_trade_record_id = None

            # ล้างการเลือกของทั้งสองตาราง
            if hasattr(self, "trade_tree"):
                self.trade_tree.selection_remove(
                    self.trade_tree.selection()
                )
                self.trade_tree.focus("")

            if hasattr(self, "month_trade_tree"):
                self.month_trade_tree.selection_remove(
                    self.month_trade_tree.selection()
                )
                self.month_trade_tree.focus("")

            self.refresh_trade_calendar()

            messagebox.showinfo(
                "ลบสำเร็จ",
                f"ลบรายการ ID {record_id} เรียบร้อยแล้ว"
            )

        except sqlite3.Error as error:
            if connection is not None:
                connection.rollback()

            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถลบรายการได้\n{error}"
            )

        finally:
            if connection is not None:
                connection.close()

    def clear_trade_form(self, keep_date=False):

        # วันที่ใช้จากวันที่เลือกบนปฏิทิน ไม่ต้องกรอกวันที่เอง
        if hasattr(self, "trade_selected_date_label"):
            self.trade_selected_date_label.config(
                text="วันที่เลือก: " + self.selected_trade_date
            )

        self.trade_symbol_entry.delete(0, tk.END)
        self.trade_type_combo.set("ซื้อ")
        self.trade_quantity_entry.delete(0, tk.END)
        self.trade_price_entry.delete(0, tk.END)
        self.trade_note_entry.delete(0, tk.END)

    def on_trade_tree_select(self, event=None):

        selected_items = self.trade_tree.selection()

        if len(selected_items) == 0:
            return

        selected_item = selected_items[0]

        self.selected_trade_record_id = str(
            self.trade_tree.item(
                selected_item,
                "iid"
            )
        )

        if hasattr(self, "month_trade_tree"):
            self.month_trade_tree.selection_remove(
                self.month_trade_tree.selection()
            )

        values = self.trade_tree.item(
            selected_item,
            "values"
        )

        if len(values) >= 3:
            self.trade_symbol_entry.delete(
                0,
                tk.END
            )
            self.trade_symbol_entry.insert(
                0,
                values[2]
            )

    def on_trade_tree_click(self, event=None):
        """รับ ID จากแถวที่คลิกโดยตรง เพื่อให้ปุ่มลบใช้ ID ได้แน่นอน"""
        if event is None:
            return

        item_id = self.trade_tree.identify_row(event.y)

        if not item_id:
            return

        self.selected_trade_record_id = str(item_id)

        self.trade_tree.selection_set(item_id)
        self.trade_tree.focus(item_id)

        if hasattr(self, "month_trade_tree"):
            self.month_trade_tree.selection_remove(
                self.month_trade_tree.selection()
            )

    # ==================================================
    # INVESTMENT SUMMARY
    # ==================================================
    def get_summary_start_date(self, months):
        # เริ่มจากวันแรกของเดือนที่ย้อนหลังไป เพื่อให้รวมทั้งเดือนปัจจุบัน
        today = datetime.now()

        month = today.month - months
        year = today.year

        while month <= 0:
            month += 12
            year -= 1

        return datetime(year, month, 1).strftime("%Y-%m-%d")

    def get_trade_exchange_rate_by_date(self, trade_date):
        """หาอัตราแลกเปลี่ยนของเดือนที่มีรายการซื้อขาย"""
        try:
            year_month = trade_date[:7]

            connection = self.connect_database()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT usd_thb FROM trade_exchange_rates WHERE year_month = ?",
                (year_month,)
            )

            row = cursor.fetchone()
            connection.close()

            if row is None:
                return None

            return float(row[0])

        except sqlite3.Error:
            return None

    def show_investment_summary(self):
        summary_window = tk.Toplevel(self.root)
        summary_window.title("สรุปกำไร–ขาดทุนการลงทุน")
        summary_window.configure(bg=THEME_COLORS["bg"])
        summary_window.geometry("1050x700")
        summary_window.transient(self.root)
        summary_window.grab_set()

        ttk.Label(
            summary_window,
            text="สรุปกำไร–ขาดทุนการลงทุน",
            font=("Tahoma", 20, "bold")
        ).pack(pady=(20, 5))

        ttk.Label(
            summary_window,
            text="เลือกช่วงเวลาที่ต้องการดูข้อมูล",
            style="Subtitle.TLabel"
        ).pack(pady=(0, 15))

        option_frame = ttk.Frame(summary_window)
        option_frame.pack(fill="x", padx=30)

        ttk.Button(
            option_frame,
            text="3 เดือนก่อน",
            command=lambda: self.load_investment_summary(
                summary_window, 3
            )
        ).pack(side="left", padx=5)

        ttk.Button(
            option_frame,
            text="6 เดือนก่อน",
            command=lambda: self.load_investment_summary(
                summary_window, 6
            )
        ).pack(side="left", padx=5)

        custom_frame = ttk.LabelFrame(
            summary_window,
            text="กำหนดช่วงเวลาเอง"
        )
        custom_frame.pack(fill="x", padx=30, pady=15)

        ttk.Label(custom_frame, text="วันที่เริ่ม").grid(
            row=0, column=0, padx=8, pady=10
        )

        start_entry = ttk.Entry(custom_frame, width=14)
        start_entry.grid(row=0, column=1, padx=8, pady=10)

        ttk.Label(custom_frame, text="ถึงวันที่").grid(
            row=0, column=2, padx=8, pady=10
        )

        end_entry = ttk.Entry(custom_frame, width=14)
        end_entry.grid(row=0, column=3, padx=8, pady=10)
        end_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        def use_custom_range():
            start_date = start_entry.get().strip()
            end_date = end_entry.get().strip()

            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning(
                    "ข้อมูลไม่ถูกต้อง",
                    "กรุณาใส่วันที่ในรูปแบบ YYYY-MM-DD"
                )
                return

            if start_date > end_date:
                messagebox.showwarning(
                    "ข้อมูลไม่ถูกต้อง",
                    "วันที่เริ่มต้องไม่มากกว่าวันที่สิ้นสุด"
                )
                return

            self.load_investment_summary(
                summary_window, None, start_date, end_date
            )

        ttk.Button(
            custom_frame,
            text="ดูสรุป",
            command=use_custom_range
        ).grid(row=0, column=4, padx=10, pady=10)

        result_frame = ttk.LabelFrame(
            summary_window,
            text="ผลสรุป"
        )
        result_frame.pack(
            fill="both", expand=True, padx=30, pady=(0, 20)
        )

        self.investment_summary_result = result_frame

    def load_investment_summary(
        self,
        summary_window,
        months=None,
        start_date=None,
        end_date=None
    ):
        if months is not None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = self.get_summary_start_date(months)

        if not start_date or not end_date:
            return

        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return

        all_records = self.get_all_trade_transactions()

        # เอารายการก่อนช่วงที่เลือกมาด้วย เพื่อคำนวณ FIFO ให้ถูกต้อง
        fifo_records = []
        for record in all_records:
            if record[1] <= end_date:
                fifo_records.append(record)

        sell_results, invalid_sales = self.calculate_trade_matches(
            fifo_records
        )

        period_records = []
        for record in all_records:
            if start_date <= record[1] <= end_date:
                period_records.append(record)

        buy_orders = 0
        sell_orders = 0
        total_buy_usd = 0.0
        total_sell_usd = 0.0
        total_profit_usd = 0.0
        total_loss_usd = 0.0

        total_buy_thb = 0.0
        total_sell_thb = 0.0
        total_profit_thb = 0.0
        total_loss_thb = 0.0

        missing_rate_months = []

        for record in period_records:
            trade_date = record[1]
            transaction_type = record[3]
            amount_usd = float(record[5])
            exchange_rate = self.get_trade_exchange_rate_by_date(trade_date)

            if exchange_rate is None:
                month_name = trade_date[:7]
                if month_name not in missing_rate_months:
                    missing_rate_months.append(month_name)
            else:
                amount_thb = amount_usd * exchange_rate

            if transaction_type == "ซื้อ":
                buy_orders += 1
                total_buy_usd += amount_usd

                if exchange_rate is not None:
                    total_buy_thb += amount_thb

            elif transaction_type == "ขาย":
                sell_orders += 1
                total_sell_usd += amount_usd

                if exchange_rate is not None:
                    total_sell_thb += amount_thb

                pnl_usd = sell_results.get(record[0], 0.0)

                if pnl_usd > 0:
                    total_profit_usd += pnl_usd
                elif pnl_usd < 0:
                    total_loss_usd += abs(pnl_usd)

                if exchange_rate is not None:
                    pnl_thb = pnl_usd * exchange_rate

                    if pnl_thb > 0:
                        total_profit_thb += pnl_thb
                    elif pnl_thb < 0:
                        total_loss_thb += abs(pnl_thb)

        net_pnl_usd = total_profit_usd - total_loss_usd

        if missing_rate_months:
            net_pnl_thb = total_profit_thb - total_loss_thb
        else:
            net_pnl_thb = total_profit_thb - total_loss_thb

        for widget in self.investment_summary_result.winfo_children():
            widget.destroy()

        ttk.Label(
            self.investment_summary_result,
            text=f"ช่วงวันที่ {start_date} ถึง {end_date}",
            font=("Tahoma", 13, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))

        summary_grid = ttk.Frame(self.investment_summary_result)
        summary_grid.pack(fill="x", padx=15)

        if missing_rate_months:
            rate_text = (
                "ยังไม่มีค่าเงินของเดือน: "
                + ", ".join(missing_rate_months)
                + "\nกรุณาไปที่ปฏิทินแล้วบันทึก 1 USD = กี่บาท ของเดือนนั้น"
            )
        else:
            rate_text = "แปลงเป็นเงินบาทจากอัตราแลกเปลี่ยนของแต่ละเดือนแล้ว"

        ttk.Label(
            self.investment_summary_result,
            text=rate_text,
            foreground="#F5A524" if missing_rate_months else "#34D399"
        ).pack(anchor="w", padx=20, pady=(0, 8))

        summary_items = [
            (
                "ซื้อทั้งหมด",
                f"{total_buy_usd:,.2f} USD\n"
                f"{total_buy_thb:,.2f} บาท"
            ),
            (
                "ขายทั้งหมด",
                f"{total_sell_usd:,.2f} USD\n"
                f"{total_sell_thb:,.2f} บาท"
            ),
            (
                "กำไรทั้งหมด",
                f"+{total_profit_usd:,.2f} USD\n"
                f"+{total_profit_thb:,.2f} บาท"
            ),
            (
                "ขาดทุนทั้งหมด",
                f"-{total_loss_usd:,.2f} USD\n"
                f"-{total_loss_thb:,.2f} บาท"
            ),
            (
                "กำไร/ขาดทุนสุทธิ",
                f"{net_pnl_usd:+,.2f} USD\n"
                f"{net_pnl_thb:+,.2f} บาท"
            ),
            ("ออเดอร์ซื้อ", f"{buy_orders} รอบ"),
            ("ออเดอร์ขาย", f"{sell_orders} รอบ")
        ]

        for index, item in enumerate(summary_items):
            row = index // 2
            column = index % 2

            box = ttk.LabelFrame(summary_grid, text=item[0])
            box.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=5,
                pady=5
            )

            ttk.Label(
                box,
                text=item[1],
                font=("Tahoma", 12, "bold"),
                justify="center"
            ).pack(padx=15, pady=10)

        summary_grid.columnconfigure(0, weight=1)
        summary_grid.columnconfigure(1, weight=1)

        if invalid_sales:
            ttk.Label(
                self.investment_summary_result,
                text=(
                    f"หมายเหตุ: มีรายการขาย {len(invalid_sales)} รายการ "
                    "ที่จำนวนหุ้นไม่ตรงกับรายการซื้อที่มีอยู่"
                ),
                foreground="#F87171"
            ).pack(anchor="w", padx=20, pady=8)

        detail_frame = ttk.LabelFrame(
            self.investment_summary_result,
            text="รายการซื้อขายในช่วงที่เลือก"
        )
        detail_frame.pack(
            fill="both", expand=True, padx=15, pady=10
        )

        columns = (
            "date",
            "symbol",
            "type",
            "quantity",
            "amount_usd",
            "amount_thb",
            "pnl_usd",
            "pnl_thb"
        )

        tree = ttk.Treeview(
            detail_frame,
            columns=columns,
            show="headings",
            height=8
        )

        headings = {
            "date": "วันที่",
            "symbol": "หุ้น",
            "type": "รายการ",
            "quantity": "จำนวน",
            "amount_usd": "จำนวนเงิน USD",
            "amount_thb": "จำนวนเงิน บาท",
            "pnl_usd": "กำไร/ขาดทุน USD",
            "pnl_thb": "กำไร/ขาดทุน บาท"
        }

        widths = {
            "date": 90,
            "symbol": 75,
            "type": 65,
            "quantity": 80,
            "amount_usd": 110,
            "amount_thb": 120,
            "pnl_usd": 115,
            "pnl_thb": 120
        }

        for column in columns:
            tree.heading(column, text=headings[column])
            tree.column(column, width=widths[column], anchor="center")

        tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(8, 0),
            pady=8
        )

        scrollbar = ttk.Scrollbar(
            detail_frame,
            orient="vertical",
            command=tree.yview
        )
        scrollbar.pack(side="right", fill="y", padx=8, pady=8)
        tree.configure(yscrollcommand=scrollbar.set)

        for record in period_records:
            trade_date = record[1]
            amount_usd = float(record[5])
            exchange_rate = self.get_trade_exchange_rate_by_date(trade_date)

            if exchange_rate is None:
                amount_thb_text = "-"
            else:
                amount_thb_text = f"{amount_usd * exchange_rate:,.2f}"

            pnl_usd_text = "-"
            pnl_thb_text = "-"

            if record[3] == "ขาย":
                pnl_usd = sell_results.get(record[0], 0.0)
                pnl_usd_text = f"{pnl_usd:+,.2f}"

                if exchange_rate is not None:
                    pnl_thb_text = f"{pnl_usd * exchange_rate:+,.2f}"

            quantity_text = (
                f"{float(record[4]):,.4f}".rstrip("0").rstrip(".")
            )

            tree.insert(
                "",
                "end",
                values=(
                    trade_date,
                    record[2],
                    record[3],
                    quantity_text,
                    f"{amount_usd:,.2f}",
                    amount_thb_text,
                    pnl_usd_text,
                    pnl_thb_text
                )
            )

    # ==================================================
    # CALENDAR NAVIGATION
    # ==================================================
    def previous_trade_month(self):

        self.trade_calendar_month -= 1

        if self.trade_calendar_month == 0:
            self.trade_calendar_month = 12
            self.trade_calendar_year -= 1

        self.refresh_trade_calendar()

    def next_trade_month(self):

        self.trade_calendar_month += 1

        if self.trade_calendar_month == 13:
            self.trade_calendar_month = 1
            self.trade_calendar_year += 1

        self.refresh_trade_calendar()

    def current_trade_month(self):

        today = datetime.now()

        self.trade_calendar_year = today.year
        self.trade_calendar_month = today.month
        self.selected_trade_date = today.strftime(
            "%Y-%m-%d"
        )

        if hasattr(self, "trade_selected_date_label"):
            self.trade_selected_date_label.config(
                text="วันที่เลือก: " + self.selected_trade_date
            )

        self.refresh_trade_calendar()

    def select_trade_calendar_date(
        self,
        year,
        month,
        day
    ):

        self.selected_trade_date = (
            f"{year:04d}-{month:02d}-{day:02d}"
        )

        if hasattr(self, "trade_selected_date_label"):
            self.trade_selected_date_label.config(
                text="วันที่เลือก: " + self.selected_trade_date
            )

        # เปลี่ยนวันที่แล้วเตรียมฟอร์มสำหรับบันทึกรายการของวันนั้น
        self.clear_trade_form(keep_date=True)

        self.refresh_trade_records()
        self.update_calendar_selection()

        if hasattr(self, "trade_symbol_entry"):
            self.trade_symbol_entry.focus_set()

    # ==================================================
    # REFRESH CALENDAR
    # ==================================================
    def refresh_trade_calendar(self):

        if not hasattr(self, "calendar_grid"):
            return

        monthly_records = self.get_month_trade_records()
        sell_results, invalid_sales = (
            self.calculate_trade_matches()
        )

        self.refresh_current_holdings()

        daily_records = {}

        for record in monthly_records:
            trade_date = record[1]

            if trade_date not in daily_records:
                daily_records[trade_date] = []

            daily_records[trade_date].append(
                record
            )

        for widget in self.calendar_grid.winfo_children():
            if int(
                widget.grid_info().get(
                    "row",
                    0
                )
            ) > 0:
                widget.destroy()

        month_names = [
            "",
            "มกราคม",
            "กุมภาพันธ์",
            "มีนาคม",
            "เมษายน",
            "พฤษภาคม",
            "มิถุนายน",
            "กรกฎาคม",
            "สิงหาคม",
            "กันยายน",
            "ตุลาคม",
            "พฤศจิกายน",
            "ธันวาคม"
        ]

        self.trade_month_label.config(
            text=(
                f"{month_names[self.trade_calendar_month]} "
                f"{self.trade_calendar_year + 543}"
            )
        )

        self.load_trade_exchange_rate_to_form()

        self.calendar_cells.clear()

        month_weeks = calendar.monthcalendar(
            self.trade_calendar_year,
            self.trade_calendar_month
        )

        for week_index, week in enumerate(
            month_weeks,
            start=1
        ):

            for column, day in enumerate(week):

                cell = tk.Frame(
                    self.calendar_grid,
                    bd=0,
                    relief="flat",
                    height=92,
                    highlightthickness=1,
                    highlightbackground=THEME_COLORS["border"],
                    highlightcolor=THEME_COLORS["border"]
                )

                cell.grid(
                    row=week_index,
                    column=column,
                    sticky="nsew",
                    padx=2,
                    pady=2
                )

                cell.grid_propagate(False)

                if day == 0:
                    cell.configure(
                        bg=THEME_COLORS["bg"],
                        highlightbackground=THEME_COLORS["bg"]
                    )
                    continue

                trade_date = (
                    f"{self.trade_calendar_year:04d}-"
                    f"{self.trade_calendar_month:02d}-"
                    f"{day:02d}"
                )

                day_label = tk.Label(
                    cell,
                    text=str(day),
                    font=("Tahoma", 11, "bold"),
                    anchor="nw"
                )
                day_label.pack(
                    fill="x",
                    padx=6,
                    pady=(4, 0)
                )

                records = daily_records.get(
                    trade_date,
                    []
                )

                # แสดงรายการซื้อ/ขายจริงภายในช่องวันที่
                # ไม่แสดงเป็น "ซื้อ 1 รายการ" แต่บอกชื่อหุ้นและจำนวนหุ้นทันที
                for record in records:
                    transaction_type = record[3]
                    symbol = str(record[2]).upper()
                    quantity = float(record[4])

                    quantity_text = (
                        f"{quantity:,.4f}".rstrip("0").rstrip(".")
                    )

                    if transaction_type == "ซื้อ":
                        transaction_text = (
                            f"ซื้อ {symbol} {quantity_text} หุ้น"
                        )
                        transaction_color = "#6C93FF"
                    else:
                        transaction_text = (
                            f"ขาย {symbol} {quantity_text} หุ้น"
                        )
                        transaction_color = "#B39DFF"

                    transaction_label = tk.Label(
                        cell,
                        text=transaction_text,
                        fg=transaction_color,
                        font=("Tahoma", 8, "bold"),
                        anchor="w"
                    )
                    transaction_label.pack(
                        fill="x",
                        anchor="w",
                        padx=6,
                        pady=(1, 0)
                    )

                    self.bind_calendar_widget(
                        transaction_label,
                        self.trade_calendar_year,
                        self.trade_calendar_month,
                        day
                    )

                day_pnl = 0.0
                has_sale = False

                for record in records:
                    if record[3] == "ขาย":
                        has_sale = True
                        day_pnl += sell_results.get(
                            record[0],
                            0.0
                        )

                # ถ้าวันนั้นมีการขาย ต้องแสดงผลกำไร/ขาดทุนเสมอ
                # เพื่อให้ผู้ใช้เห็นผลของรายการขาย แม้กำไรจะเป็น 0
                if has_sale:
                    if day_pnl > 0:
                        pnl_text = (
                            f"กำไร +{day_pnl:,.2f} USD"
                        )
                        pnl_color = "#34D399"
                    elif day_pnl < 0:
                        pnl_text = (
                            f"ขาดทุน {day_pnl:,.2f} USD"
                        )
                        pnl_color = "#F87171"
                    else:
                        pnl_text = "กำไร/ขาดทุน 0.00 USD"
                        pnl_color = "#8D9BBC"

                    pnl_label = tk.Label(
                        cell,
                        text=pnl_text,
                        fg=pnl_color,
                        font=("Tahoma", 9, "bold")
                    )
                    pnl_label.pack(
                        anchor="w",
                        padx=6
                    )

                    self.bind_calendar_widget(
                        pnl_label,
                        self.trade_calendar_year,
                        self.trade_calendar_month,
                        day
                    )

                self.bind_calendar_widget(
                    cell,
                    self.trade_calendar_year,
                    self.trade_calendar_month,
                    day
                )

                self.bind_calendar_widget(
                    day_label,
                    self.trade_calendar_year,
                    self.trade_calendar_month,
                    day
                )

                self.calendar_cells[
                    trade_date
                ] = cell

        self.update_calendar_selection()
        self.start_month_chart(
            monthly_records,
            sell_results
        )

        self.update_trade_summary(
            monthly_records,
            sell_results
        )

        self.refresh_trade_records()
        self.refresh_month_trade_records(
            monthly_records,
            sell_results
        )

        if invalid_sales:
            self.trade_summary_label.config(
                text=(
                    self.trade_summary_label.cget("text")
                    + "\nคำเตือน: พบรายการขายที่จำนวนหุ้นก่อนวันขายไม่เพียงพอ"
                )
            )

    def update_calendar_selection(self):
        """ไฮไลต์วันที่เลือก (ขอบสีฟ้า) และวันนี้ (ขอบสีน้ำเงิน)"""
        today = datetime.now().strftime("%Y-%m-%d")

        for trade_date, cell in self.calendar_cells.items():
            if trade_date == self.selected_trade_date:
                color = THEME_COLORS["cyan"]
                thickness = 2
            elif trade_date == today:
                color = THEME_COLORS["primary"]
                thickness = 2
            else:
                color = THEME_COLORS["border"]
                thickness = 1

            cell.configure(
                highlightbackground=color,
                highlightcolor=color,
                highlightthickness=thickness
            )

    def bind_calendar_widget(
        self,
        widget,
        year,
        month,
        day
    ):

        widget.bind(
            "<Button-1>",
            lambda event: self.select_trade_calendar_date(
                year,
                month,
                day
            )
        )

    def get_month_trade_records(self):

        month_prefix = (
            f"{self.trade_calendar_year:04d}-"
            f"{self.trade_calendar_month:02d}-"
        )

        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    trade_date,
                    symbol,
                    transaction_type,
                    quantity,
                    total_amount,
                    note
                FROM trade_transactions
                WHERE user_id = ?
                  AND trade_date LIKE ?
                ORDER BY trade_date ASC, id ASC
                """,
                (self.user_id, month_prefix + "%")
            )

            records = cursor.fetchall()
            connection.close()

            return records

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถโหลดรายการซื้อขายได้\n{error}"
            )
            return []

    def get_trade_exchange_rate(self):
        """อ่านอัตรา USD/THB ของเดือนที่กำลังเปิด"""
        year_month = (
            f"{self.trade_calendar_year:04d}-"
            f"{self.trade_calendar_month:02d}"
        )

        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT usd_thb
                FROM trade_exchange_rates
                WHERE year_month = ?
                """,
                (year_month,)
            )

            row = cursor.fetchone()
            connection.close()

            if row is None:
                return None

            return float(row[0])

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถโหลดค่าเงินได้\\n{error}"
            )
            return None

    def save_trade_exchange_rate(self):
        """บันทึกอัตราแลกเปลี่ยนของเดือนปัจจุบัน"""
        try:
            rate = float(
                self.trade_exchange_rate_entry.get().replace(",", "")
            )
        except (ValueError, TypeError):
            messagebox.showwarning(
                "ข้อมูลไม่ถูกต้อง",
                "กรุณากรอกอัตราแลกเปลี่ยน เช่น 32.50"
            )
            return

        if rate <= 0:
            messagebox.showwarning(
                "ข้อมูลไม่ถูกต้อง",
                "อัตราแลกเปลี่ยนต้องมากกว่า 0"
            )
            return

        year_month = (
            f"{self.trade_calendar_year:04d}-"
            f"{self.trade_calendar_month:02d}"
        )

        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO trade_exchange_rates
                (year_month, usd_thb, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(year_month)
                DO UPDATE SET
                    usd_thb = excluded.usd_thb,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (year_month, rate)
            )

            connection.commit()
            connection.close()

            self.refresh_trade_calendar()

            messagebox.showinfo(
                "บันทึกสำเร็จ",
                f"บันทึกอัตราแลกเปลี่ยน {rate:,.4f} บาท/USD แล้ว"
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถบันทึกค่าเงินได้\\n{error}"
            )

    def load_trade_exchange_rate_to_form(self):
        """โหลดค่าเงินของเดือนที่กำลังเปิดมาแสดงในช่อง"""
        if not hasattr(self, "trade_exchange_rate_entry"):
            return

        rate = self.get_trade_exchange_rate()

        self.trade_exchange_rate_entry.delete(
            0,
            tk.END
        )

        if rate is not None:
            self.trade_exchange_rate_entry.insert(
                0,
                f"{rate:.4f}"
            )
            self.trade_exchange_rate_status.config(
                text=(
                    f"ใช้ 1 USD = {rate:,.4f} บาท "
                    f"สำหรับเดือนนี้"
                )
            )
        else:
            self.trade_exchange_rate_status.config(
                text=(
                    "ยังไม่ได้กรอกค่าเงินดอลลาร์ "
                    "จึงยังไม่แสดงกำไรสุทธิเป็นบาท"
                )
            )

    def update_trade_summary(
        self,
        records,
        sell_results
    ):

        total_profit = 0.0
        total_loss = 0.0
        net_pnl = 0.0
        buy_count = 0
        sell_count = 0
        total_bought = 0.0
        total_sold = 0.0

        for record in records:
            record_id = record[0]
            transaction_type = record[3]

            if transaction_type == "ซื้อ":
                buy_count += 1
                total_bought += float(record[4])

            elif transaction_type == "ขาย":
                sell_count += 1
                total_sold += float(record[4])

                pnl = sell_results.get(
                    record_id,
                    0.0
                )

                net_pnl += pnl

                if pnl > 0:
                    total_profit += pnl
                elif pnl < 0:
                    total_loss += abs(pnl)

        exchange_rate = self.get_trade_exchange_rate()

        if net_pnl > 0:
            result_usd = f"กำไรสุทธิ +{net_pnl:,.2f} USD"
        elif net_pnl < 0:
            result_usd = f"ขาดทุนสุทธิ {net_pnl:,.2f} USD"
        else:
            result_usd = "ยังไม่มีกำไร/ขาดทุนที่รับรู้"

        if exchange_rate is not None:
            net_pnl_thb = net_pnl * exchange_rate
            profit_thb = total_profit * exchange_rate
            loss_thb = total_loss * exchange_rate

            if net_pnl_thb > 0:
                baht_result = (
                    f"กำไรสุทธิ +{net_pnl_thb:,.2f} บาท"
                )
            elif net_pnl_thb < 0:
                baht_result = (
                    f"ขาดทุนสุทธิ {net_pnl_thb:,.2f} บาท"
                )
            else:
                baht_result = "กำไรสุทธิ 0.00 บาท"

            baht_detail = (
                f"{baht_result}\n"
                f"กำไรรวม: +{profit_thb:,.2f} บาท"
                f"    |    "
                f"ขาดทุนรวม: -{loss_thb:,.2f} บาท"
            )
        else:
            baht_detail = (
                "กำไรสุทธิเป็นบาท: กรุณากรอกอัตราแลกเปลี่ยน "
                "1 USD = กี่บาท แล้วกด “บันทึกค่าเงิน”"
            )

        self.trade_summary_label.config(
            text=(
                f"{result_usd}\n"
                f"กำไรรวม: +{total_profit:,.2f} USD"
                f"    |    "
                f"ขาดทุนรวม: -{total_loss:,.2f} USD\n"
                f"{baht_detail}\n"
                f"ซื้อ: {buy_count} รายการ ({total_bought:,.4f} หุ้น)"
                f"    |    "
                f"ขาย: {sell_count} รายการ ({total_sold:,.4f} หุ้น)"
            )
        )

    def refresh_trade_records(self):

        if not hasattr(self, "trade_tree"):
            return

        for item in self.trade_tree.get_children():
            self.trade_tree.delete(item)

        selected_date = self.selected_trade_date

        try:
            datetime.strptime(
                selected_date,
                "%Y-%m-%d"
            )
        except ValueError:
            selected_date = (
                f"{self.trade_calendar_year:04d}-"
                f"{self.trade_calendar_month:02d}-01"
            )
            self.selected_trade_date = selected_date

        self.selected_date_label.config(
            text=f"รายการซื้อขายวันที่ {selected_date}"
        )

        try:
            connection = self.connect_database()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    trade_date,
                    symbol,
                    transaction_type,
                    quantity,
                    total_amount,
                    note
                FROM trade_transactions
                WHERE user_id = ?
                  AND trade_date = ?
                ORDER BY id ASC
                """,
                (self.user_id, selected_date)
            )

            records = cursor.fetchall()
            connection.close()

            sell_results, _ = (
                self.calculate_trade_matches()
            )
            all_records = self.get_all_trade_transactions()
            remaining_positions = self.calculate_remaining_positions(all_records)

            for record in records:
                (
                    record_id,
                    trade_date,
                    symbol,
                    transaction_type,
                    quantity,
                    total_amount,
                    note
                ) = record

                unit_price = (
                    total_amount / quantity
                    if quantity
                    else 0
                )

                pnl = (
                    sell_results.get(
                        record_id,
                        0.0
                    )
                    if transaction_type == "ขาย"
                    else 0.0
                )

                pnl_text = (
                    f"{pnl:+,.2f}"
                    if transaction_type == "ขาย"
                    else "-"
                )
                remaining_text = f"{remaining_positions.get(record_id, 0.0):,.4f}"

                self.trade_tree.insert(
                    "",
                    "end",
                    iid=str(record_id),
                    values=(
                        record_id,
                        transaction_type,
                        symbol,
                        f"{quantity:,.4f}",
                        f"{total_amount:,.2f}",
                        f"{unit_price:,.4f}",
                        pnl_text,
                        remaining_text,
                        note or ""
                    )
                )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"ไม่สามารถโหลดรายการของวันที่เลือกได้\n{error}"
            )

    def refresh_month_trade_records(
        self,
        records=None,
        sell_results=None
    ):

        if not hasattr(
            self,
            "month_trade_tree"
        ):
            return

        for item in self.month_trade_tree.get_children():
            self.month_trade_tree.delete(item)

        if records is None:
            records = self.get_month_trade_records()

        if sell_results is None:
            sell_results, _ = (
                self.calculate_trade_matches()
            )

        all_records = self.get_all_trade_transactions()
        remaining_positions = self.calculate_remaining_positions(all_records)

        for record in records:
            (
                record_id,
                trade_date,
                symbol,
                transaction_type,
                quantity,
                total_amount,
                note
            ) = record

            pnl = (
                sell_results.get(
                    record_id,
                    0.0
                )
                if transaction_type == "ขาย"
                else 0.0
            )

            pnl_text = (
                f"{pnl:+,.2f}"
                if transaction_type == "ขาย"
                else "-"
            )

            self.month_trade_tree.insert(
                "",
                "end",
                iid=str(record_id),
                values=(
                    trade_date,
                    transaction_type,
                    symbol,
                    f"{quantity:,.4f}",
                    f"{total_amount:,.2f}",
                    pnl_text,
                    f"{remaining_positions.get(record_id, 0.0):,.4f}"
                )
            )

    
    # ==================================================
    # DASHBOARD / CHART HELPERS (ตกแต่งและกราฟเคลื่อนไหว)
    # ==================================================
    def build_stock_dashboard(self, stock):
        score, _ = self.calculate_fundamental_score(
            stock.get("pe"),
            stock.get("roe"),
            stock.get("roa"),
            stock.get("net_margin")
        )

        dashboard = StockDashboard(
            self.stock_result_frame,
            stock,
            score
        )
        dashboard.pack(
            fill="x",
            pady=(0, 10)
        )

    def start_industry_bars(self, items, weights):
        self._industry_items = (list(items), dict(weights))

        shown = min(len(items), 8)
        self.industry_chart.configure(
            height=max(80, 28 + 36 * shown)
        )

        self._industry_step(0)

    def _industry_step(self, step):
        steps = 22
        eased = 1 - (1 - step / steps) ** 3

        self._draw_industry_bars(eased)

        if step < steps:
            self._industry_job = self.root.after(
                25,
                lambda: self._industry_step(step + 1)
            )
        else:
            self._industry_job = None

    def _draw_industry_bars(self, progress):
        canvas = self.industry_chart
        canvas.delete("all")

        items, weights = self._industry_items
        width = canvas.winfo_width()
        if width < 300:
            width = 700

        palette = [
            "#4C7DFF", "#38D6F0", "#8B7CFF", "#34D399",
            "#F5A524", "#F87171", "#6C93FF", "#B39DFF"
        ]

        label_width = 190
        x0 = label_width + 10
        x1 = width - 80

        for index, (industry, amount) in enumerate(items[:8]):
            y = 20 + index * 36
            weight = weights.get(industry, 0.0)

            name = str(industry)
            if len(name) > 24:
                name = name[:23] + "…"

            canvas.create_text(
                10, y + 9, text=name, anchor="w",
                fill=THEME_COLORS["text"], font=("Tahoma", 10)
            )

            auth_rounded_rect(
                canvas, x0, y, x1, y + 18, 9,
                fill="#16224A", outline=""
            )

            bar_width = (x1 - x0) * (weight / 100) * progress
            if bar_width >= 8:
                auth_rounded_rect(
                    canvas, x0, y, x0 + bar_width, y + 18, 9,
                    fill=palette[index % len(palette)], outline=""
                )

            canvas.create_text(
                width - 10, y + 9, text=f"{weight * progress:.1f}%",
                anchor="e", fill=THEME_COLORS["text"],
                font=("Tahoma", 10, "bold")
            )

    def start_month_chart(self, records, sell_results):
        if not hasattr(self, "month_chart"):
            return

        days = calendar.monthrange(
            self.trade_calendar_year,
            self.trade_calendar_month
        )[1]

        daily = [0.0] * days
        has_sale = False

        for record in records:
            if record[3] != "ขาย":
                continue

            has_sale = True

            try:
                day = int(str(record[1])[8:10])
            except ValueError:
                continue

            if 1 <= day <= days:
                daily[day - 1] += sell_results.get(record[0], 0.0)

        self._month_chart_data = (daily, has_sale)

        job = getattr(self, "_month_chart_job", None)
        if job is not None:
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
            self._month_chart_job = None

        self._month_chart_step(0)

    def _month_chart_step(self, step):
        steps = 20
        eased = 1 - (1 - step / steps) ** 3

        self._draw_month_chart(eased)

        if step < steps:
            self._month_chart_job = self.root.after(
                25,
                lambda: self._month_chart_step(step + 1)
            )
        else:
            self._month_chart_job = None

    def _draw_month_chart(self, progress):
        canvas = self.month_chart
        canvas.delete("all")

        daily, has_sale = self._month_chart_data

        width = canvas.winfo_width()
        if width < 300:
            width = 900
        height = int(canvas.cget("height"))

        colors = THEME_COLORS

        if not has_sale:
            canvas.create_text(
                width / 2, height / 2,
                text="ยังไม่มีกำไร/ขาดทุนที่รับรู้ในเดือนนี้ "
                     "บันทึกรายการขายเพื่อดูกราฟ",
                fill=colors["muted"], font=("Tahoma", 11)
            )
            return

        pad_left, pad_right, pad_top, pad_bottom = 64, 24, 30, 28

        cumulative = []
        running = 0.0
        for value in daily:
            running += value
            cumulative.append(running)

        max_abs = max(
            max(abs(v) for v in daily),
            max(abs(v) for v in cumulative),
            0.01
        )

        plot_h = height - pad_top - pad_bottom
        zero_y = pad_top + plot_h / 2
        scale = (plot_h / 2) / max_abs * 0.92

        canvas.create_text(
            pad_left, 12, anchor="w",
            text="กำไร/ขาดทุนรายวัน (แท่ง) และสะสมในเดือน (เส้น) หน่วย USD",
            fill=colors["muted"], font=("Tahoma", 9, "bold")
        )

        for fraction, label in ((-1, f"-{max_abs:,.0f}"), (0, "0"), (1, f"+{max_abs:,.0f}")):
            y = zero_y - fraction * (plot_h / 2) * 0.92
            canvas.create_line(
                pad_left, y, width - pad_right, y,
                fill=colors["border"],
                dash=() if fraction == 0 else (2, 5)
            )
            canvas.create_text(
                pad_left - 8, y, text=label, anchor="e",
                fill=colors["muted"], font=("Tahoma", 8)
            )

        count = len(daily)
        slot = (width - pad_left - pad_right) / count
        bar_width = max(3, slot * 0.55)

        for index, value in enumerate(daily):
            x = pad_left + slot * (index + 0.5)

            if (index + 1) == 1 or (index + 1) % 5 == 0:
                canvas.create_text(
                    x, height - 12, text=str(index + 1),
                    fill=colors["muted"], font=("Tahoma", 8)
                )

            if value == 0:
                continue

            top = zero_y - value * scale * progress
            canvas.create_rectangle(
                x - bar_width / 2, zero_y, x + bar_width / 2, top,
                fill=colors["positive"] if value > 0 else colors["negative"],
                outline=""
            )

        points = []
        for index, value in enumerate(cumulative):
            x = pad_left + slot * (index + 0.5)
            y = zero_y - value * scale * progress
            points.extend((x, y))

        if len(points) >= 4:
            canvas.create_line(
                points, fill=colors["cyan"], width=2.5,
                smooth=False, capstyle="round", joinstyle="round"
            )
            canvas.create_oval(
                points[-2] - 5, points[-1] - 5,
                points[-2] + 5, points[-1] + 5,
                fill="#FFFFFF", outline=colors["cyan"], width=2
            )

    # ==================================================
    # FORMAT NUMBER
    # ==================================================
    def format_number(self, value):

        if value is None:
            return "-"

        try:

            return f"{float(value):,.2f}"

        except (ValueError, TypeError):

            return str(value)

    # ==================================================
    # FORMAT PERCENT
    # ==================================================
    def format_percent(self, value):

        if value is None:
            return "-"

        try:

            return f"{float(value):,.2f}%"

        except (ValueError, TypeError):

            return str(value)

    # ==================================================
    # FORMAT METRIC
    # ==================================================


# ==================================================
# AUTHENTICATION
# ==================================================
def database_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock.db")

def ensure_auth_database():
    connection = sqlite3.connect(database_path())
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
    finally:
        connection.close()

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 120000
    ).hex()
    return password_hash, salt

def validate_password(password):
    errors = []
    if len(password) < 8:
        errors.append("อย่างน้อย 8 ตัวอักษร")
    if not re.search(r"[A-Z]", password):
        errors.append("ตัวพิมพ์ใหญ่ 1 ตัว")
    if not re.search(r"[a-z]", password):
        errors.append("ตัวพิมพ์เล็ก 1 ตัว")
    if not re.search(r"[0-9]", password):
        errors.append("ตัวเลข 1 ตัว")
    digits = "0123456789"
    reversed_digits = digits[::-1]
    has_sequential_digits = any(
        password.find(digits[i:i + 4]) >= 0
        or password.find(reversed_digits[i:i + 4]) >= 0
        for i in range(len(digits) - 3)
    )
    if has_sequential_digits:
        errors.append("ห้ามใช้ตัวเลขเรียงกัน 4 ตัวขึ้นไป")
    return errors

def authenticate_user(username, password):
    connection = sqlite3.connect(database_path())
    try:
        row = connection.execute(
            "SELECT id, username, password_hash, password_salt FROM users WHERE username = ? COLLATE NOCASE",
            (username,)
        ).fetchone()
        if row is None:
            return None
        password_hash, _ = hash_password(password, row[3])
        if secrets.compare_digest(password_hash, row[2]):
            return row[0], row[1]
        return None
    finally:
        connection.close()

# ==================================================
# AUTH UI THEME (ธีมมืดสำหรับหน้าเข้าสู่ระบบ/สมัครสมาชิก)
# ตกแต่งหน้าตาเท่านั้น ไม่เกี่ยวกับการตรวจสอบหรือบันทึกข้อมูล
# ==================================================
import math
from tkinter import font as tkfont

AUTH_COLORS = {
    "bg_top": "#070C1B",
    "bg_bottom": "#0E1A3B",
    "card": "#0F1830",
    "card_border": "#26365C",
    "panel": "#10215C",
    "panel_soft": "#1C3485",
    "field": "#0A1226",
    "field_border": "#2A3B63",
    "text": "#E8EEFC",
    "muted": "#8D9BBC",
    "primary": "#4C7DFF",
    "primary_hover": "#6C93FF",
    "cyan": "#38D6F0",
    "violet": "#8B7CFF",
    "green": "#34D399",
    "red": "#F87171",
    "orange": "#F5A524",
}


def auth_blend(color_a, color_b, t):
    """ผสมสองสีแบบ #RRGGBB ตามสัดส่วน t (0-1)"""
    t = max(0.0, min(1.0, t))
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def auth_rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    """สี่เหลี่ยมมุมมน"""
    r = max(1, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1,
        x2, y1 + r, x2, y1 + r, x2, y2 - r, x2, y2 - r, x2, y2,
        x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2, x1, y2,
        x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


def draw_auth_background(canvas, width, height):
    """พื้นหลังไล่สีน้ำเงินเข้ม พร้อมแสงเรืองนุ่ม ๆ (สร้างเป็นภาพเนียน ไม่มีขอบวงกลม)"""
    canvas.delete("bg")
    c = AUTH_COLORS

    def to_rgb(color):
        return [int(color[i:i + 2], 16) for i in (1, 3, 5)]

    step = 4 if width * height > 400000 else 2
    sw = max(1, -(-width // step))
    sh = max(1, -(-height // step))
    top, bottom = to_rgb(c["bg_top"]), to_rgb(c["bg_bottom"])
    glows = [
        (width * 0.10, height * 0.12, max(width, height) * 0.55, to_rgb("#2F54E0"), 0.55),
        (width * 0.92, height * 0.92, max(width, height) * 0.60, to_rgb("#0E9CC0"), 0.50),
        (width * 0.82, height * 0.08, max(width, height) * 0.36, to_rgb("#7550E8"), 0.40),
    ]
    rows = []
    for j in range(sh):
        t = j / max(1, sh - 1)
        base = [top[k] + (bottom[k] - top[k]) * t for k in range(3)]
        y = j * step
        row = []
        for i in range(sw):
            x = i * step
            r, g, b = base
            for gx, gy, radius, color, power in glows:
                dx, dy = x - gx, y - gy
                d2 = dx * dx + dy * dy
                if d2 < radius * radius:
                    s = (1 - math.sqrt(d2) / radius) ** 2.2 * power
                    r += (color[0] - r) * s
                    g += (color[1] - g) * s
                    b += (color[2] - b) * s
            row.append("#%02x%02x%02x" % (int(r), int(g), int(b)))
        rows.append("{" + " ".join(row) + "}")
    small = tk.PhotoImage(width=sw, height=sh)
    small.put(" ".join(rows))
    image = small.zoom(step, step)
    canvas.auth_bg_image = image  # เก็บอ้างอิงไว้ ไม่ให้ภาพหาย
    canvas.create_image(0, 0, anchor="nw", image=image, tags="bg")
    canvas.tag_lower("bg")


def auth_shadow(canvas, x1, y1, x2, y2, r, tags):
    """เงาใต้การ์ด"""
    c = AUTH_COLORS
    layers = 9
    for i in range(layers):
        grow = (layers - i) * 2
        auth_rounded_rect(
            canvas, x1 - grow, y1 - grow + 16, x2 + grow, y2 + grow + 16, r + grow,
            fill=auth_blend(c["bg_bottom"], "#02040A", (i + 1) / layers * 0.42),
            outline="", tags=tags
        )


class AuthFieldBox:
    """ช่องกรอกแบบกล่องมุมมน มีไฮไลต์ตอนคลิก และปุ่มแสดง/ซ่อนรหัสผ่าน"""

    def __init__(self, canvas, secret=False):
        c = AUTH_COLORS
        self.canvas = canvas
        self.secret = secret
        self.rect = None
        self.entry = tk.Entry(
            canvas,
            show="•" if secret else "",
            font=("Tahoma", 11),
            relief="flat",
            bd=0,
            bg=c["field"],
            fg=c["text"],
            insertbackground=c["cyan"],
            selectbackground=c["primary"],
            selectforeground="#FFFFFF",
            highlightthickness=0
        )
        self.window = canvas.create_window(0, 0, window=self.entry, anchor="w")
        self.entry.bind("<FocusIn>", lambda event: self.set_focus(True))
        self.entry.bind("<FocusOut>", lambda event: self.set_focus(False))

    def set_focus(self, focused):
        c = AUTH_COLORS
        if self.rect is not None:
            self.canvas.itemconfigure(
                self.rect,
                outline=c["cyan"] if focused else c["field_border"],
                width=2 if focused else 1
            )

    def toggle_secret(self, event=None):
        shown = self.entry.cget("show") == ""
        self.entry.config(show="•" if shown else "")
        self.canvas.itemconfigure(self.toggle_item, text="แสดง" if shown else "ซ่อน")

    def place(self, x, y, w, h=46):
        c = AUTH_COLORS
        canvas = self.canvas
        self.rect = auth_rounded_rect(
            canvas, x, y, x + w, y + h, 14,
            fill=c["field"], outline=c["field_border"], width=1, tags="ui"
        )
        right_pad = 16
        if self.secret:
            shown = self.entry.cget("show") == ""
            self.toggle_item = canvas.create_text(
                x + w - 16, y + h / 2, text="ซ่อน" if shown else "แสดง",
                anchor="e", fill=c["muted"], font=("Tahoma", 9, "bold"), tags="ui"
            )
            canvas.tag_bind(self.toggle_item, "<Button-1>", self.toggle_secret)
            canvas.tag_bind(self.toggle_item, "<Enter>", lambda e: canvas.config(cursor="hand2"))
            canvas.tag_bind(self.toggle_item, "<Leave>", lambda e: canvas.config(cursor=""))
            right_pad = 66
        canvas.coords(self.window, x + 16, y + h / 2)
        canvas.itemconfigure(self.window, width=max(40, w - 16 - right_pad), height=h - 16)
        self.set_focus(self.entry == self.entry.focus_get())


def auth_logo(canvas, x, y, size=44, tags="ui"):
    """โลโก้ "รู้" มุมมนสีน้ำเงิน"""
    c = AUTH_COLORS
    auth_rounded_rect(
        canvas, x, y, x + size, y + size, size * 0.3,
        fill=c["primary"], outline=auth_blend(c["primary"], "#FFFFFF", 0.3), tags=tags
    )
    canvas.create_text(
        x + size / 2, y + size / 2, text="รู้", fill="#FFFFFF",
        font=("Tahoma", int(size * 0.36), "bold"), tags=tags
    )


def auth_button(canvas, x, y, w, h, text, tag):
    """ปุ่มมุมมนสีน้ำเงินพร้อมไฮไลต์ด้านบน (ผูกการคลิกภายหลังด้วย tag)"""
    c = AUTH_COLORS
    auth_rounded_rect(
        canvas, x, y, x + w, y + h, 15,
        fill=c["primary"], outline=auth_blend(c["primary"], "#FFFFFF", 0.25),
        tags=("ui", tag, tag + "_bg")
    )
    canvas.create_text(
        x + w / 2, y + h / 2, text=text, fill="#FFFFFF",
        font=("Tahoma", 12, "bold"), tags=("ui", tag)
    )


def auth_bind_button(canvas, tag, command):
    c = AUTH_COLORS

    def enter(event):
        canvas.itemconfigure(tag + "_bg", fill=c["primary_hover"])
        canvas.config(cursor="hand2")

    def leave(event):
        canvas.itemconfigure(tag + "_bg", fill=c["primary"])
        canvas.config(cursor="")

    canvas.tag_bind(tag, "<Enter>", enter)
    canvas.tag_bind(tag, "<Leave>", leave)
    canvas.tag_bind(tag, "<Button-1>", lambda event: command())


def reset_root_window(root):
    """ล้างทุกอย่างในหน้าต่างหลัก เพื่อสลับระหว่างหน้าเข้าสู่ระบบกับหน้าโปรแกรม"""
    # ยกเลิกงานที่ตั้งเวลาไว้ (แอนิเมชัน, การดึงข้อมูล) ไม่ให้ไปแตะวิดเจ็ตที่ถูกลบแล้ว
    try:
        for job in root.tk.splitlist(root.tk.call("after", "info")):
            try:
                root.after_cancel(job)
            except tk.TclError:
                pass
    except tk.TclError:
        pass

    # ปลดการผูกลูกกลิ้งเมาส์ของหน้าเดิม
    for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        try:
            root.unbind_all(sequence)
        except tk.TclError:
            pass

    root.unbind("<Destroy>")

    for child in list(root.winfo_children()):
        try:
            child.destroy()
        except tk.TclError:
            pass

    root.minsize(1, 1)
    root.resizable(True, True)
    root.state("normal")
    root.update_idletasks()


class RegisterWindow:
    def __init__(self, parent, on_registered):
        self.parent = parent
        self.on_registered = on_registered
        c = AUTH_COLORS
        width, height = 480, 670
        self.window = tk.Toplevel(parent)
        self.window.title("สมัครสมาชิก")
        self.window.geometry(f"{width}x{height}")
        self.window.resizable(False, False)
        self.window.configure(bg=c["bg_bottom"])
        self.window.transient(parent)
        self.window.grab_set()

        canvas = tk.Canvas(
            self.window, width=width, height=height,
            bg=c["bg_bottom"], highlightthickness=0, bd=0
        )
        canvas.pack(fill="both", expand=True)
        self.canvas = canvas
        draw_auth_background(canvas, width, height)

        auth_shadow(canvas, 28, 28, width - 28, height - 28, 26, "ui")
        auth_rounded_rect(
            canvas, 28, 28, width - 28, height - 28, 26,
            fill=c["card"], outline=c["card_border"], width=1, tags="ui"
        )

        # หัวข้อ
        auth_logo(canvas, 60, 58, 46)
        canvas.create_text(
            122, 62, text="สมัครสมาชิก", anchor="nw", fill=c["text"],
            font=("Tahoma", 19, "bold")
        )
        canvas.create_text(
            122, 96, text="สร้างบัญชีเพื่อเริ่มวิเคราะห์หุ้นของคุณ", anchor="nw",
            fill=c["muted"], font=("Tahoma", 9)
        )

        # ช่องกรอก
        fields = [
            ("ชื่อผู้ใช้", False),
            ("อีเมล", False),
            ("รหัสผ่าน", True),
            ("ยืนยันรหัสผ่าน", True),
        ]
        boxes = []
        field_x, field_w = 60, width - 120
        y = 142
        for label, secret in fields:
            canvas.create_text(
                field_x + 2, y, text=label, anchor="nw",
                fill=c["muted"], font=("Tahoma", 10, "bold")
            )
            box = AuthFieldBox(canvas, secret)
            box.place(field_x, y + 24, field_w, 44)
            boxes.append(box)
            y += 84

        self.username_entry = boxes[0].entry
        self.email_entry = boxes[1].entry
        self.password_entry = boxes[2].entry
        self.confirm_entry = boxes[3].entry

        # เงื่อนไขรหัสผ่าน
        hint_top = y + 2
        auth_rounded_rect(
            canvas, field_x, hint_top, field_x + field_w, hint_top + 56, 12,
            fill=c["panel"], outline=c["panel_soft"], width=1
        )
        canvas.create_text(
            field_x + 14, hint_top + 28,
            text="รหัสผ่าน: 8 ตัวขึ้นไป + A-Z + a-z + 0-9\nและห้ามมีตัวเลขเรียงกัน 4 ตัวขึ้นไป",
            anchor="w", fill="#B9C9F5", font=("Tahoma", 9)
        )

        # ปุ่ม
        auth_button(canvas, field_x, hint_top + 78, field_w, 50, "สมัครสมาชิก", "btn_register")
        auth_bind_button(canvas, "btn_register", self.register)

        self.username_entry.focus_set()
        self.window.bind("<Return>", lambda event: self.register())

    def register(self):
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip().lower()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        if not username or not email or not password or not confirm:
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณากรอกข้อมูลให้ครบทุกช่อง", parent=self.window)
            return
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            messagebox.showwarning("อีเมลไม่ถูกต้อง", "กรุณากรอกอีเมลให้ถูกต้อง", parent=self.window)
            return
        errors = validate_password(password)
        if errors:
            messagebox.showwarning(
                "รหัสผ่านไม่ผ่านเงื่อนไข",
                "รหัสผ่านต้องมี:\n• " + "\n• ".join(errors),
                parent=self.window
            )
            return
        if password != confirm:
            messagebox.showwarning("รหัสผ่านไม่ตรงกัน", "กรุณายืนยันรหัสผ่านให้ตรงกัน", parent=self.window)
            return
        password_hash, salt = hash_password(password)
        connection = sqlite3.connect(database_path())
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, password_salt) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, salt)
            )
            connection.commit()
            user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            messagebox.showwarning("สมัครสมาชิกไม่สำเร็จ", "ชื่อผู้ใช้หรืออีเมลนี้ถูกใช้งานแล้ว", parent=self.window)
            return
        finally:
            connection.close()
        messagebox.showinfo("สมัครสมาชิกสำเร็จ", "สร้างบัญชีเรียบร้อยแล้ว", parent=self.window)
        self.window.destroy()
        self.on_registered(user_id, username)

class LoginWindow:
    def __init__(self, root):
        self.root = root
        c = AUTH_COLORS
        self.root.title("รู้เรื่องหุ้น - เข้าสู่ระบบ")
        self.root.state("zoomed")
        self.root.resizable(True, True)
        self.root.configure(bg=c["bg_top"])
        ensure_auth_database()

        self.setup_styles()

        self.canvas = tk.Canvas(
            self.root, bg=c["bg_top"], highlightthickness=0, bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # สถานะอนิเมชัน
        self.tick_count = 0
        self.chart_progress = 0.0
        self.chart_box = None
        self.chart_points = 44
        self.chip_offsets = {"chip_a": 0, "chip_b": 0}
        self.animation_job = None
        self.panel_color = c["panel"]
        raw = [
            0.55 * i / (self.chart_points - 1)
            + 0.16 * math.sin(i / 4.1)
            + 0.07 * math.sin(i / 1.7 + 1.3)
            for i in range(self.chart_points)
        ]
        low, high = min(raw), max(raw)
        self.chart_values = [(v - low) / (high - low) for v in raw]

        # ช่องกรอก (สร้างครั้งเดียว วางตำแหน่งใหม่ทุกครั้งที่ขนาดหน้าต่างเปลี่ยน)
        self.username_box = AuthFieldBox(self.canvas, False)
        self.password_box = AuthFieldBox(self.canvas, True)
        self.username_entry = self.username_box.entry
        self.password_entry = self.password_box.entry
        self.password_entry.bind("<Return>", lambda event: self.login())
        self.username_entry.bind(
            "<Return>", lambda event: self.password_entry.focus_set()
        )

        self.size = (0, 0)
        self.canvas.bind("<Configure>", self.on_resize)

        auth_bind_button(self.canvas, "btn_login", self.login)
        self.canvas.tag_bind("link_register", "<Button-1>", lambda event: self.open_register())
        self.canvas.tag_bind(
            "link_register", "<Enter>",
            lambda event: (
                self.canvas.config(cursor="hand2"),
                self.canvas.itemconfigure("link_register", fill="#8BEAFB")
            )
        )
        self.canvas.tag_bind(
            "link_register", "<Leave>",
            lambda event: (
                self.canvas.config(cursor=""),
                self.canvas.itemconfigure("link_register", fill=AUTH_COLORS["cyan"])
            )
        )

        self.root.bind("<Destroy>", self.on_destroy, add="+")
        self.username_entry.focus_set()
        self.animation_job = self.root.after(60, self.animate)

    # ----------------------------------------------
    def on_destroy(self, event):
        if event.widget is self.root and self.animation_job is not None:
            try:
                self.root.after_cancel(self.animation_job)
            except tk.TclError:
                pass
            self.animation_job = None

    def on_resize(self, event):
        if event.width < 50 or event.height < 50:
            return
        if (event.width, event.height) == self.size:
            return
        self.size = (event.width, event.height)
        self.draw_layout(event.width, event.height)

    def draw_layout(self, w, h):
        c = AUTH_COLORS
        canvas = self.canvas
        draw_auth_background(canvas, w, h)
        canvas.delete("ui")
        canvas.delete("chart")

        card_w = min(1000, w - 60)
        card_h = min(600, h - 60)
        x0 = (w - card_w) / 2
        y0 = (h - card_h) / 2
        show_panel = card_w >= 820
        panel_w = int(card_w * 0.47) if show_panel else 0

        auth_shadow(canvas, x0, y0, x0 + card_w, y0 + card_h, 30, "ui")
        auth_rounded_rect(
            canvas, x0, y0, x0 + card_w, y0 + card_h, 30,
            fill=c["card"], outline=c["card_border"], width=1, tags="ui"
        )

        if show_panel:
            self.draw_left_panel(x0 + 14, y0 + 14, panel_w - 14, card_h - 28)

        # ---------- ฟอร์มฝั่งขวา ----------
        area_x = x0 + panel_w
        area_w = card_w - panel_w
        form_w = min(380, area_w - 90)
        fx = area_x + (area_w - form_w) / 2
        fy = y0 + (card_h - 430) / 2

        canvas.create_text(
            fx, fy, text="เข้าสู่ระบบ", anchor="nw", fill=c["text"],
            font=("Tahoma", 26, "bold"), tags="ui"
        )
        canvas.create_text(
            fx, fy + 46, text="ยินดีต้อนรับกลับมา กรอกข้อมูลเพื่อเข้าใช้งาน",
            anchor="nw", fill=c["muted"], font=("Tahoma", 10), tags="ui"
        )

        canvas.create_text(
            fx + 2, fy + 100, text="ชื่อผู้ใช้", anchor="nw", fill=c["muted"],
            font=("Tahoma", 10, "bold"), tags="ui"
        )
        self.username_box.place(fx, fy + 124, form_w, 48)

        canvas.create_text(
            fx + 2, fy + 192, text="รหัสผ่าน", anchor="nw", fill=c["muted"],
            font=("Tahoma", 10, "bold"), tags="ui"
        )
        self.password_box.place(fx, fy + 216, form_w, 48)

        auth_button(canvas, fx, fy + 296, form_w, 52, "เข้าสู่ระบบ", "btn_login")

        # เส้นคั่น + สมัครสมาชิก
        mid_y = fy + 380
        line_color = auth_blend(c["card"], c["card_border"], 0.9)
        canvas.create_line(fx, mid_y, fx + form_w, mid_y, fill=line_color, tags="ui")

        font = tkfont.Font(family="Tahoma", size=10)
        font_bold = tkfont.Font(family="Tahoma", size=10, weight="bold")
        text_a = "ยังไม่มีบัญชี?"
        text_b = "สมัครสมาชิก"
        total = font.measure(text_a) + 8 + font_bold.measure(text_b)
        sx = fx + (form_w - total) / 2
        canvas.create_text(
            sx, mid_y + 26, text=text_a, anchor="w", fill=c["muted"],
            font=("Tahoma", 10), tags="ui"
        )
        canvas.create_text(
            sx + font.measure(text_a) + 8, mid_y + 26, text=text_b, anchor="w",
            fill=c["cyan"], font=("Tahoma", 10, "bold"), tags=("ui", "link_register")
        )

        canvas.create_text(
            x0 + panel_w + area_w / 2, y0 + card_h - 26,
            text="กด Enter เพื่อเข้าสู่ระบบ", fill="#5A6C94",
            font=("Tahoma", 9), tags="ui"
        )

        self.draw_chart()

    def draw_left_panel(self, px, py, pw, ph):
        c = AUTH_COLORS
        canvas = self.canvas
        auth_rounded_rect(
            canvas, px, py, px + pw, py + ph, 24,
            fill=c["panel"], outline=c["panel_soft"], width=1, tags="ui"
        )
        auth_logo(canvas, px + 30, py + 30, 46)
        canvas.create_text(
            px + 92, py + 53, text="รู้เรื่องหุ้น", anchor="w", fill="#FFFFFF",
            font=("Tahoma", 19, "bold"), tags="ui"
        )

        canvas.create_text(
            px + 32, py + 112, text="ลงทุนอย่างเข้าใจ\nก่อนตัดสินใจทุกครั้ง",
            anchor="nw", fill="#FFFFFF", font=("Tahoma", 23, "bold"), tags="ui"
        )
        canvas.create_text(
            px + 32, py + 202, text="ทำเรื่องหุ้นให้เข้าใจง่าย ก่อนตัดสินใจลงทุน",
            anchor="nw", fill="#A9BAEB", font=("Tahoma", 10), tags="ui"
        )

        features = [
            ("วิเคราะห์หุ้นด้วยตัวชี้วัดพื้นฐาน", c["cyan"]),
            ("ตรวจความเสี่ยงและการกระจุกตัวของพอร์ต", c["violet"]),
            ("บันทึกกำไร–ขาดทุนบนปฏิทินซื้อขาย", c["orange"]),
        ]
        fy = py + 240
        for text, color in features:
            canvas.create_oval(
                px + 34, fy + 4, px + 44, fy + 14, fill=color, outline="", tags="ui"
            )
            canvas.create_text(
                px + 56, fy + 9, text=text, anchor="w", fill="#DCE6FF",
                font=("Tahoma", 10, "bold"), tags="ui"
            )
            fy += 28

        # พื้นที่กราฟตัวอย่าง
        cx0, cx1 = px + 32, px + pw - 32
        cy0, cy1 = py + ph - 200, py + ph - 40
        self.chart_box = (cx0, cy0, cx1, cy1)
        grid_color = auth_blend(c["panel"], c["panel_soft"], 0.8)
        for i in range(4):
            gy = cy0 + 62 + (cy1 - cy0 - 72) * i / 3
            canvas.create_line(cx0, gy, cx1, gy, fill=grid_color, dash=(2, 5), tags="ui")
        canvas.create_text(
            px + pw / 2, py + ph - 20, text="ภาพประกอบตัวอย่าง",
            fill="#6F83C0", font=("Tahoma", 8), tags="ui"
        )

        self.draw_chip(cx0 + 4, cy0 + 2, "NVDA", "+2.4%", c["green"], "chip_a")
        self.draw_chip(cx1 - 128, cy0 + 26, "AAPL", "-0.8%", c["red"], "chip_b")
        self.chip_offsets = {"chip_a": 0, "chip_b": 0}

    def draw_chip(self, x, y, symbol, change, color, tag):
        c = AUTH_COLORS
        canvas = self.canvas
        tags = ("ui", tag)
        auth_rounded_rect(
            canvas, x, y, x + 124, y + 34, 12,
            fill="#0B1744", outline=c["panel_soft"], width=1, tags=tags
        )
        canvas.create_text(
            x + 12, y + 17, text=symbol, anchor="w", fill="#FFFFFF",
            font=("Tahoma", 9, "bold"), tags=tags
        )
        canvas.create_text(
            x + 112, y + 17, text=change, anchor="e", fill=color,
            font=("Tahoma", 9, "bold"), tags=tags
        )

    def draw_chart(self):
        """วาดกราฟเส้นตัวอย่างพร้อมจุดเรืองแสง"""
        if self.chart_box is None:
            return
        c = AUTH_COLORS
        canvas = self.canvas
        canvas.delete("chart")
        cx0, cy0, cx1, cy1 = self.chart_box
        top, bottom = cy0 + 66, cy1 - 8
        count = self.chart_points
        visible = max(2, int(self.chart_progress))
        pts = []
        for i in range(visible):
            x = cx0 + (cx1 - cx0) * i / (count - 1)
            y = bottom - self.chart_values[i] * (bottom - top)
            pts.extend((x, y))
        if len(pts) < 4:
            return

        area = pts + [pts[-2], bottom, pts[0], bottom]
        canvas.create_polygon(
            area, fill=auth_blend(c["panel"], c["primary"], 0.20),
            outline="", tags="chart"
        )
        canvas.create_line(
            pts, fill=auth_blend(c["panel"], c["cyan"], 0.22),
            width=8, smooth=True, capstyle="round", joinstyle="round", tags="chart"
        )
        canvas.create_line(
            pts, fill=c["cyan"], width=2.5, smooth=True,
            capstyle="round", joinstyle="round", tags="chart"
        )
        ex, ey = pts[-2], pts[-1]
        phase = (self.tick_count % 36) / 36
        ring = 6 + phase * 14
        canvas.create_oval(
            ex - ring, ey - ring, ex + ring, ey + ring, fill="",
            outline=auth_blend(c["cyan"], c["panel"], phase), width=2, tags="chart"
        )
        canvas.create_oval(
            ex - 5, ey - 5, ex + 5, ey + 5, fill="#FFFFFF",
            outline=c["cyan"], width=2, tags="chart"
        )
        canvas.tag_raise("chip_a")
        canvas.tag_raise("chip_b")

    def animate(self):
        self.animation_job = None
        try:
            if not self.root.winfo_exists():
                return
            self.tick_count += 1
            if self.chart_progress < self.chart_points:
                self.chart_progress = min(self.chart_points, self.chart_progress + 0.8)
            self.draw_chart()
            for index, tag in enumerate(("chip_a", "chip_b")):
                offset = round(4 * math.sin(self.tick_count / 14 + index * 2.1))
                delta = offset - self.chip_offsets.get(tag, 0)
                if delta:
                    self.canvas.move(tag, 0, delta)
                    self.chip_offsets[tag] = offset
            self.animation_job = self.root.after(45, self.animate)
        except tk.TclError:
            self.animation_job = None

    def setup_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning(
                "ข้อมูลไม่ครบ",
                "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน",
                parent=self.root
            )
            return

        user = authenticate_user(username, password)
        if user is None:
            messagebox.showerror(
                "เข้าสู่ระบบไม่สำเร็จ",
                "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
                parent=self.root
            )
            return

        # ใช้หน้าต่างเดิม ล้างหน้าเข้าสู่ระบบออกทั้งหมดก่อนแสดงหน้าโปรแกรม
        root = self.root
        reset_root_window(root)
        StockApp(root, user[0], user[1])

    def open_register(self):
        RegisterWindow(self.root, self.registration_complete)

    def registration_complete(self, user_id, username):
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, username)
        self.password_entry.delete(0, tk.END)
        self.password_entry.focus_set()

# ==================================================
# START PROGRAM
# ==================================================
if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()