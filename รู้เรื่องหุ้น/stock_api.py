import csv
import io
import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FINNHUB_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"

# ข้อมูลสำรองใช้เมื่อ Finnhub ไม่ส่งชื่อบริษัท/อุตสาหกรรมกลับมา
FALLBACK_STOCKS = {
    "AAPL": {"company_name": "Apple Inc.", "industry": "Technology"},
    "AMD": {"company_name": "Advanced Micro Devices, Inc.", "industry": "Semiconductors"},
    "AMZN": {"company_name": "Amazon.com, Inc.", "industry": "Retail"},
    "AVGO": {"company_name": "Broadcom Inc.", "industry": "Semiconductors"},
    "GOOGL": {"company_name": "Alphabet Inc.", "industry": "Media"},
    "GOOG": {"company_name": "Alphabet Inc.", "industry": "Media"},
    "META": {"company_name": "Meta Platforms, Inc.", "industry": "Media"},
    "MSFT": {"company_name": "Microsoft Corporation", "industry": "Technology"},
    "MU": {"company_name": "Micron Technology, Inc.", "industry": "Semiconductors"},
    "NBIS": {"company_name": "Nebius Group N.V.", "industry": "Technology"},
    "NVDA": {"company_name": "NVIDIA Corporation", "industry": "Semiconductors"},
    "RKLB": {"company_name": "Rocket Lab Corporation", "industry": "Aerospace & Defense"},
    "SMCI": {"company_name": "Super Micro Computer, Inc.", "industry": "Technology"},
    "TSLA": {"company_name": "Tesla, Inc.", "industry": "Automobiles"},
    "TSM": {"company_name": "Taiwan Semiconductor Manufacturing Company Limited", "industry": "Semiconductors"},
    "VRT": {"company_name": "Vertiv Holdings Co.", "industry": "Electrical Equipment"},
    "ARM": {"company_name": "Arm Holdings plc", "industry": "Semiconductors"},
    "ASML": {"company_name": "ASML Holding N.V.", "industry": "Semiconductors"},
    "INTC": {"company_name": "Intel Corporation", "industry": "Semiconductors"},
    "CRWD": {"company_name": "CrowdStrike Holdings, Inc.", "industry": "Technology"},
    "COIN": {"company_name": "Coinbase Global, Inc.", "industry": "Financial Services"},
    "HOOD": {"company_name": "Robinhood Markets, Inc.", "industry": "Financial Services"},
    "MSTR": {"company_name": "Strategy Inc.", "industry": "Technology"},
    "COST": {"company_name": "Costco Wholesale Corporation", "industry": "Retail"},
    "WMT": {"company_name": "Walmart Inc.", "industry": "Retail"},
    "JPM": {"company_name": "JPMorgan Chase & Co.", "industry": "Banking"},
    "BAC": {"company_name": "Bank of America Corporation", "industry": "Banking"},
    "V": {"company_name": "Visa Inc.", "industry": "Financial Services"},
    "MA": {"company_name": "Mastercard Incorporated", "industry": "Financial Services"},
}


def _safe_error_message(response=None, error=None):
    """สร้างข้อความ error ที่ไม่เปิดเผย API key"""
    if response is not None:
        status = response.status_code

        if status == 401:
            return "Finnhub ปฏิเสธ API key (HTTP 401)"
        if status == 403:
            return "Finnhub ไม่อนุญาตการเรียก API นี้ (HTTP 403)"
        if status == 429:
            return "Finnhub จำกัดจำนวนการเรียก API (HTTP 429)"
        if status >= 500:
            return f"Finnhub ขัดข้องชั่วคราว (HTTP {status})"

        return f"Finnhub ตอบกลับ HTTP {status}"

    if error is not None:
        return str(error)

    return "ไม่สามารถเชื่อมต่อ Finnhub ได้"


def _finnhub_get(path, params, timeout=4):
    """
    เรียก Finnhub เพียงครั้งเดียว

    ไม่ retry เมื่อ timeout เพราะการ retry ทำให้ผู้ใช้ต้องรอนาน
    และถ้า Finnhub ปลายทางไม่ตอบ การยิงซ้ำไม่ได้ช่วยแก้ปัญหา
    """
    if not API_KEY:
        return None, "ไม่พบ FINNHUB_API_KEY ในไฟล์ .env"

    request_params = dict(params)
    request_params["token"] = API_KEY
    url = f"{BASE_URL}{path}"

    try:
        response = requests.get(
            url,
            params=request_params,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json(), None

    except requests.exceptions.RequestException as error:
        response_obj = locals().get("response")
        return None, _safe_error_message(response_obj, error)


def _request_public(url, params=None, timeout=8):
    """เรียก public data source โดยไม่ส่ง Finnhub API key"""
    try:
        response = requests.get(
            url,
            params=params or {},
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/153 Safari/537.36"
            },
        )
        response.raise_for_status()
        return response, None

    except requests.exceptions.RequestException as error:
        return None, str(error)


def _get_stooq_symbol(symbol):
    """แปลง ticker หุ้นสหรัฐเป็นรูปแบบที่ Stooq ใช้"""
    return f"{symbol.lower()}.us"


def get_stooq_quote(symbol):
    """
    Fallback หลักสำหรับราคา

    Stooq เป็น public quote source ที่ไม่ต้องใช้ API key
    และไม่พึ่ง Yahoo Finance ที่กำลังตอบ HTTP 429 ในเครื่องนี้
    """
    stooq_symbol = _get_stooq_symbol(symbol)
    url = "https://stooq.com/q/l/"
    params = {
        "s": stooq_symbol,
        "f": "sd2t2ohlcv",
        "h": "",
        "e": "csv",
    }

    response, error_message = _request_public(url, params=params, timeout=8)

    if response is None:
        return None, f"Stooq: {error_message}"

    try:
        rows = list(csv.DictReader(io.StringIO(response.text)))

        if not rows:
            return None, "Stooq ไม่ส่งข้อมูลกลับมา"

        row = rows[0]
        close_value = row.get("CLOSE")

        if not close_value or close_value.upper() in {"N/D", "NA"}:
            return None, f"Stooq ไม่พบราคาของ {symbol}"

        current_price = float(close_value)

        def number(field):
            value = row.get(field)
            if value in (None, "", "N/D", "NA"):
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        return {
            "c": current_price,
            "d": None,
            "dp": None,
            "h": number("HIGH"),
            "l": number("LOW"),
            "o": number("OPEN"),
            "pc": None,
            "_source": "Stooq",
        }, None

    except (ValueError, TypeError, KeyError, IndexError) as error:
        return None, f"รูปแบบข้อมูล Stooq ไม่ถูกต้อง: {error}"


def get_stooq_previous_close(symbol):
    """
    พยายามหา close ของวันซื้อขายก่อนหน้าเพื่อคำนวณ change/change%.

    ถ้าหาไม่ได้จะคืน None โดยไม่ทำให้การดึงราคาปัจจุบันล้มเหลว
    """
    stooq_symbol = _get_stooq_symbol(symbol)

    today = datetime.now().date()
    start_date = today - timedelta(days=10)

    url = "https://stooq.com/q/d/l/"
    params = {
        "s": stooq_symbol,
        "d1": start_date.strftime("%Y%m%d"),
        "d2": today.strftime("%Y%m%d"),
        "i": "d",
    }

    response, _ = _request_public(url, params=params, timeout=8)

    if response is None:
        return None

    try:
        rows = list(csv.DictReader(io.StringIO(response.text)))

        closes = []
        for row in rows:
            close_value = row.get("Close")
            if close_value in (None, "", "N/D", "NA"):
                continue

            try:
                closes.append(float(close_value))
            except (TypeError, ValueError):
                continue

        if len(closes) >= 2:
            return closes[-2]

    except (ValueError, TypeError, KeyError, IndexError):
        pass

    return None


def get_yahoo_quote(symbol):
    """
    Fallback สำรองสุดท้าย

    Yahoo ถูกวางหลัง Stooq เพราะ endpoint นี้กำลังตอบ HTTP 429
    จึงไม่ควรเป็น fallback ตัวแรก
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        "range": "1d",
        "interval": "1d",
    }

    response, error_message = _request_public(url, params=params, timeout=8)

    if response is None:
        return None, error_message

    try:
        data = response.json()
        result = data.get("chart", {}).get("result")

        if not result:
            return None, "Yahoo Finance ไม่พบข้อมูลหุ้นนี้"

        meta = result[0].get("meta", {}) or {}
        quote = (result[0].get("indicators", {}).get("quote") or [{}])[0]

        current_price = meta.get("regularMarketPrice")

        if current_price is None:
            closes = quote.get("close") or []
            valid_closes = [value for value in closes if value is not None]
            current_price = valid_closes[-1] if valid_closes else None

        if current_price is None:
            return None, "Yahoo Finance ไม่มีราคาปัจจุบัน"

        previous_close = (
            meta.get("chartPreviousClose")
            or meta.get("previousClose")
        )

        change = None
        change_percent = None

        if previous_close not in (None, 0):
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100

        return {
            "c": current_price,
            "d": change,
            "dp": change_percent,
            "h": meta.get("regularMarketDayHigh"),
            "l": meta.get("regularMarketDayLow"),
            "o": meta.get("regularMarketOpen"),
            "pc": previous_close,
            "_source": "Yahoo Finance",
        }, None

    except (ValueError, TypeError, KeyError, IndexError) as error:
        return None, f"รูปแบบข้อมูล Yahoo Finance ไม่ถูกต้อง: {error}"


# ==================================================
# RISK MARKET DATA : beta / volatility / max drawdown
# ใช้ราคาปิดรายวันย้อนหลังจาก Stooq (ไม่ต้องใช้ API key)
# สำรองด้วย Yahoo Finance และใช้ beta จาก Finnhub ก่อนเสมอ
# หมายเหตุ: Finnhub /stock/candle ต้องใช้แผนเสียเงินสำหรับหุ้นสหรัฐ
# จึงไม่ใช้เป็นแหล่งราคาย้อนหลัง
# ==================================================
TRADING_DAYS_PER_YEAR = 252
MIN_HISTORY_POINTS = 60
BENCHMARK_SYMBOL = "SPY"
_BENCHMARK_CACHE = {"time": None, "history": None}
_BENCHMARK_TTL = timedelta(hours=6)


def get_stooq_history(symbol, days=380):
    """ราคาปิดรายวันย้อนหลังจาก Stooq: คืน (list[(date, close)], error)"""
    today = datetime.now().date()
    params = {
        "s": _get_stooq_symbol(symbol),
        "d1": (today - timedelta(days=days)).strftime("%Y%m%d"),
        "d2": today.strftime("%Y%m%d"),
        "i": "d",
    }

    response, error_message = _request_public(
        "https://stooq.com/q/d/l/", params=params, timeout=10
    )

    if response is None:
        return None, f"Stooq: {error_message}"

    try:
        history = []
        for row in csv.DictReader(io.StringIO(response.text)):
            date_text = row.get("Date")
            close_value = row.get("Close")

            if not date_text or close_value in (None, "", "N/D", "NA"):
                continue

            try:
                close_price = float(close_value)
            except (TypeError, ValueError):
                continue

            if close_price > 0:
                history.append((date_text, close_price))

        history.sort(key=lambda item: item[0])

        if len(history) < MIN_HISTORY_POINTS:
            return None, f"Stooq มีข้อมูลย้อนหลังของ {symbol} ไม่เพียงพอ"

        return history, None

    except (ValueError, TypeError, KeyError) as error:
        return None, f"รูปแบบข้อมูลย้อนหลัง Stooq ไม่ถูกต้อง: {error}"


def get_yahoo_history(symbol):
    """ราคาปิดรายวันย้อนหลัง 1 ปีจาก Yahoo Finance (fallback)"""
    response, error_message = _request_public(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"range": "1y", "interval": "1d"},
        timeout=10,
    )

    if response is None:
        return None, f"Yahoo Finance: {error_message}"

    try:
        result = response.json().get("chart", {}).get("result")

        if not result:
            return None, "Yahoo Finance ไม่พบข้อมูลย้อนหลัง"

        timestamps = result[0].get("timestamp") or []
        closes = (
            (result[0].get("indicators", {}).get("quote") or [{}])[0]
            .get("close") or []
        )

        history = []
        for stamp, close_price in zip(timestamps, closes):
            if close_price is None or close_price <= 0:
                continue
            date_text = datetime.utcfromtimestamp(stamp).strftime("%Y-%m-%d")
            history.append((date_text, float(close_price)))

        if len(history) < MIN_HISTORY_POINTS:
            return None, "Yahoo Finance มีข้อมูลย้อนหลังไม่เพียงพอ"

        return history, None

    except (ValueError, TypeError, KeyError, IndexError) as error:
        return None, f"รูปแบบข้อมูลย้อนหลัง Yahoo ไม่ถูกต้อง: {error}"


def get_price_history(symbol):
    """คืน (history, source, error) โดยลอง Stooq ก่อนแล้วค่อย Yahoo"""
    symbol = symbol.upper().strip()

    history, stooq_error = get_stooq_history(symbol)
    if history is not None:
        return history, "Stooq", None

    history, yahoo_error = get_yahoo_history(symbol)
    if history is not None:
        return history, "Yahoo Finance", None

    return None, None, f"{stooq_error}; {yahoo_error}"


def _daily_returns(history):
    """ผลตอบแทนรายวันแบบ {วันที่: return}"""
    returns = {}
    for index in range(1, len(history)):
        previous = history[index - 1][1]
        if previous > 0:
            returns[history[index][0]] = history[index][1] / previous - 1.0
    return returns


def calc_volatility(history):
    """ความผันผวนต่อปี (%) = ส่วนเบี่ยงเบนมาตรฐานของผลตอบแทนรายวัน x sqrt(252)"""
    values = list(_daily_returns(history).values())

    if len(values) < MIN_HISTORY_POINTS - 1:
        return None

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return (variance ** 0.5) * (TRADING_DAYS_PER_YEAR ** 0.5) * 100.0


def calc_max_drawdown(history):
    """การลดลงสูงสุดจากจุดสูงสุดก่อนหน้า (%) คืนเป็นค่าบวก เช่น 35.2"""
    if len(history) < MIN_HISTORY_POINTS:
        return None

    peak = history[0][1]
    worst = 0.0

    for _, close_price in history:
        peak = max(peak, close_price)
        drawdown = (peak - close_price) / peak
        worst = max(worst, drawdown)

    return worst * 100.0


def calc_beta(history, benchmark_history):
    """beta เทียบ benchmark จากผลตอบแทนรายวันที่วันที่ตรงกัน"""
    if not history or not benchmark_history:
        return None

    stock_returns = _daily_returns(history)
    bench_returns = _daily_returns(benchmark_history)
    dates = sorted(set(stock_returns) & set(bench_returns))

    if len(dates) < MIN_HISTORY_POINTS - 1:
        return None

    x = [bench_returns[d] for d in dates]
    y = [stock_returns[d] for d in dates]
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)

    variance = sum((a - mean_x) ** 2 for a in x)
    if variance == 0:
        return None

    covariance = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    return covariance / variance


def get_benchmark_history():
    """ราคาย้อนหลังของ SPY (แคช 6 ชั่วโมง) ใช้คำนวณ beta เมื่อ Finnhub ไม่มี"""
    now = datetime.now()

    if (
        _BENCHMARK_CACHE["history"] is not None
        and _BENCHMARK_CACHE["time"] is not None
        and now - _BENCHMARK_CACHE["time"] < _BENCHMARK_TTL
    ):
        return _BENCHMARK_CACHE["history"]

    history, _, _ = get_price_history(BENCHMARK_SYMBOL)

    if history is not None:
        _BENCHMARK_CACHE["history"] = history
        _BENCHMARK_CACHE["time"] = now

    return history


def _valid_beta(value):
    try:
        beta = float(value)
    except (TypeError, ValueError):
        return None

    # beta นอกช่วงนี้มักเป็นข้อมูลผิดปกติ
    if beta != beta or beta < -1.0 or beta > 5.0:
        return None

    return beta


def get_risk_market_data(symbol):
    """
    ข้อมูลตลาดจริงของหุ้น 1 ตัวสำหรับวิเคราะห์ความเสี่ยงพอร์ต
    คืน dict: beta, beta_source, volatility, max_drawdown, history_days, error
    ฟังก์ชันนี้เรียกเครือข่ายหลายครั้ง ต้องเรียกจาก thread แยกเท่านั้น
    """
    symbol = symbol.upper().strip()

    result = {
        "symbol": symbol,
        "beta": None,
        "beta_source": None,
        "volatility": None,
        "max_drawdown": None,
        "history_days": 0,
        "price_source": None,
        "error": None,
    }

    # 1) beta จาก Finnhub (ข้อมูลสำเร็จรูป)
    metrics = get_stock_metrics(symbol) or {}
    finnhub_beta = _valid_beta(metrics.get("beta"))

    if finnhub_beta is not None:
        result["beta"] = finnhub_beta
        result["beta_source"] = "Finnhub"

    # 2) ราคาย้อนหลัง -> volatility / drawdown (และ beta ถ้า Finnhub ไม่มี)
    history, source, error = get_price_history(symbol)

    if history is None:
        result["error"] = error
        return result

    result["price_source"] = source
    result["history_days"] = len(history)
    result["volatility"] = calc_volatility(history)
    result["max_drawdown"] = calc_max_drawdown(history)

    if result["beta"] is None:
        computed = _valid_beta(calc_beta(history, get_benchmark_history()))

        if computed is not None:
            result["beta"] = computed
            result["beta_source"] = f"คำนวณเทียบ {BENCHMARK_SYMBOL}"

    return result


def get_stock_quote(symbol):
    symbol = symbol.upper().strip()

    # 1. Finnhub: แหล่งข้อมูลหลัก
    data, error_message = _finnhub_get(
        "/quote",
        {"symbol": symbol},
        timeout=4,
    )

    if data is not None:
        current_price = data.get("c")

        if current_price is not None and current_price != 0:
            data["_source"] = "Finnhub"
            return data

        # Finnhub ตอบกลับสำเร็จ แต่ไม่มีราคาสำหรับ Symbol นี้
        # แปลว่าไม่พบหุ้น ไม่ใช่ปัญหาการเชื่อมต่อ
        return None

    # 2. Stooq: fallback หลัก
    stooq_data, stooq_error = get_stooq_quote(symbol)

    if stooq_data is not None:
        previous_close = get_stooq_previous_close(symbol)

        if previous_close not in (None, 0):
            current_price = stooq_data["c"]
            change = current_price - previous_close
            stooq_data["d"] = change
            stooq_data["dp"] = (change / previous_close) * 100
            stooq_data["pc"] = previous_close

        return stooq_data

    # 3. Yahoo: fallback สุดท้าย
    yahoo_data, yahoo_error = get_yahoo_quote(symbol)

    if yahoo_data is not None:
        return yahoo_data

    print(f"Quote API ใช้งานไม่ได้สำหรับ {symbol}: {error_message}")
    print(f"Stooq fallback: {stooq_error or 'ไม่สามารถดึงข้อมูลได้'}")

    if yahoo_error:
        print(f"Yahoo Finance fallback: {yahoo_error}")

    return {
        "_api_error": True,
        "_error_message": (
            f"Finnhub: {error_message}; "
            f"Stooq: {stooq_error or 'ไม่สามารถดึงข้อมูลได้'}; "
            f"Yahoo Finance: {yahoo_error or 'ไม่สามารถดึงข้อมูลได้'}"
        ),
    }


def get_company_profile(symbol):
    data, error_message = _finnhub_get(
        "/stock/profile2",
        {"symbol": symbol.upper()},
        timeout=4,
    )

    if data is not None:
        return data

    print(f"Profile API ใช้งานไม่ได้สำหรับ {symbol}: {error_message}")
    return {}


def get_stock_metrics(symbol):
    data, error_message = _finnhub_get(
        "/stock/metric",
        {
            "symbol": symbol.upper(),
            "metric": "all",
        },
        timeout=4,
    )

    if data is not None:
        return data.get("metric", {})

    print(f"Metrics API ใช้งานไม่ได้สำหรับ {symbol}: {error_message}")
    return {}


def get_stock_data(symbol):
    symbol = symbol.upper().strip()

    quote = get_stock_quote(symbol)

    if isinstance(quote, dict) and quote.get("_api_error"):
        return {
            "symbol": symbol,
            "_api_error": True,
            "_error_message": quote.get(
                "_error_message",
                "ไม่สามารถเชื่อมต่อข้อมูลราคาได้",
            ),
        }

    if quote is None:
        return None

    fallback = FALLBACK_STOCKS.get(symbol, {})

    # ถ้า quote มาจาก Finnhub ให้พยายามดึงข้อมูลเสริมจาก Finnhub
    # แต่ถ้า quote มาจาก fallback ให้หยุดตรงนี้เพื่อไม่ให้โปรแกรม
    # เสียเวลา timeout ซ้ำกับ Profile/Metrics
    source = quote.get("_source")

    if source == "Finnhub":
        profile = get_company_profile(symbol) or {}
        metrics = get_stock_metrics(symbol) or {}
    else:
        profile = {}
        metrics = {}

    return {
        "symbol": symbol,
        "price": quote.get("c"),
        "change": quote.get("d"),
        "change_percent": quote.get("dp"),
        "high": quote.get("h"),
        "low": quote.get("l"),
        "open": quote.get("o"),
        "previous_close": quote.get("pc"),
        "company_name": profile.get("name")
        or fallback.get("company_name")
        or symbol,
        "industry": profile.get("finnhubIndustry")
        or fallback.get("industry")
        or "ไม่ระบุ",
        "country": profile.get("country"),
        "exchange": profile.get("exchange"),
        "market_cap": profile.get("marketCapitalization"),
        "website": profile.get("weburl"),
        "pe": metrics.get("peTTM"),
        "roe": metrics.get("roeTTM"),
        "roa": metrics.get("roaTTM"),
        "net_margin": metrics.get("netProfitMarginTTM"),
        "_source": source,
    }