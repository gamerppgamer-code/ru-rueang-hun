def analyze_risk(data):
    
    roe = data["metric"]["roeTTM"]
    roa = data["metric"]["roaTTM"]
    margin = data["metric"]["netProfitMarginTTM"]
    pe = data["metric"]["peBasicExclExtraTTM"]

    risks = []
    risk_score = 0

    # ความเสี่ยงด้าน ROE
    if roe < 0:
        risks.append({
            "title": "ความเสี่ยงด้านผลตอบแทนผู้ถือหุ้น",
            "detail": "ROE ติดลบ บริษัทสร้างผลตอบแทนต่อส่วนของผู้ถือหุ้นได้ไม่ดี"
        })
        risk_score += 1

    elif roe < 15:
        risks.append({
            "title": "ความเสี่ยงด้านผลตอบแทนผู้ถือหุ้น",
            "detail": "ROE อยู่ในระดับไม่สูงมาก"
        })
        risk_score += 1

    # ความเสี่ยงด้าน ROA
    if roa < 0:
        risks.append({
            "title": "ความเสี่ยงด้านการใช้สินทรัพย์",
            "detail": "ROA ติดลบ บริษัทใช้สินทรัพย์สร้างผลตอบแทนได้ไม่ดี"
        })
        risk_score += 1

    elif roa < 5:
        risks.append({
            "title": "ความเสี่ยงด้านการใช้สินทรัพย์",
            "detail": "ROA อยู่ในระดับไม่สูงมาก"
        })
        risk_score += 1

    # ความเสี่ยงด้านกำไร
    if margin < 0:
        risks.append({
            "title": "ความเสี่ยงด้านความสามารถทำกำไร",
            "detail": "Net Profit Margin ติดลบ บริษัทกำลังขาดทุน"
        })
        risk_score += 1

    elif margin < 10:
        risks.append({
            "title": "ความเสี่ยงด้านความสามารถทำกำไร",
            "detail": "Net Profit Margin อยู่ในระดับไม่สูงมาก"
        })
        risk_score += 1

    # ความเสี่ยงด้านมูลค่าหุ้น
    if pe > 40:
        risks.append({
            "title": "ความเสี่ยงด้านมูลค่าหุ้น",
            "detail": "P/E สูง อาจมีความเสี่ยงหากผลประกอบการเติบโตไม่เป็นไปตามที่ตลาดคาดหวัง"
        })
        risk_score += 1

    elif pe > 20:
        risks.append({
            "title": "ความเสี่ยงด้านมูลค่าหุ้น",
            "detail": "P/E ค่อนข้างสูง ราคาหุ้นอาจมีความคาดหวังการเติบโตอยู่พอสมควร"
        })
        risk_score += 1

    elif pe <= 0:
        risks.append({
            "title": "ความเสี่ยงด้านมูลค่าหุ้น",
            "detail": "P/E ไม่เหมาะสำหรับใช้ประเมินหุ้นตัวนี้"
        })
        risk_score += 1

    # สรุประดับความเสี่ยง
    if risk_score == 0:
        risk_level = "ต่ำ"

    elif risk_score <= 2:
        risk_level = "ปานกลาง"

    else:
        risk_level = "สูง"

    return risks, risk_score, risk_level