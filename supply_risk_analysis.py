#1. KOTRA 뉴스 데이터 수집
import requests
import pandas as pd

url = "KOTRA_API_URL"

params = {
    "pageNo": 1,
    "pagePerCnt": 100,
    "SITE_NO": 3,
    "MENU_ID": 1360
}

response = requests.get(url, params=params)

data = response.json()

items = data["data"]

df = pd.DataFrame(items)

df.head()

#2. 공급망 관련 뉴스만 필터링
supply_keywords = [
    "희토류",
    "원자재",
    "반도체",
    "배터리",
    "리튬",
    "철강",
    "에너지",
    "석유",
    "가스",
    "공급망",
    "수출",
    "관세"
]


def check_supply(text):

    for keyword in supply_keywords:
        if keyword in text:
            return True
        
    return False



df["is_supply"] = (
    df["NTT_SJ"] + 
    df["SMMAR_CN"]
).apply(check_supply)


supply_df = df[
    df["is_supply"] == True
]

#3. 위험 키워드 기반 Risk Engine (중요)
def classify_risk(text):

    regulation = [
        "규제",
        "제재",
        "수출통제",
        "관세",
        "금지"
    ]


    price = [
        "가격",
        "급등",
        "상승",
        "원가"
    ]


    supply = [
        "공급",
        "부족",
        "차질",
        "수급",
        "물류",
        "의존"
    ]



    if any(x in text for x in regulation):
        return "규제위험"

    elif any(x in text for x in price):
        return "가격위험"

    elif any(x in text for x in supply):
        return "공급위험"

    else:
        return "기타"



supply_df["risk_type"] = (
    supply_df["NTT_SJ"]
    +
    supply_df["SMMAR_CN"]
).apply(classify_risk)

#4. Risk Score 만드는 부분
risk_weight = {
    "규제위험": 80,
    "공급위험": 70,
    "가격위험": 60,
    "기타": 30
}


supply_df["risk_score"] = (
    supply_df["risk_type"]
    .map(risk_weight)
)



def risk_level(score):

    if score >= 70:
        return "🔴 위험"

    elif score >= 50:
        return "🟡 주의"

    else:
        return "🟢 관심"



supply_df["risk_level"] = (
    supply_df["risk_score"]
    .apply(risk_level)
)

#5. AWS 업로드 파일 생성 (csv)정리
final_df = supply_df[
[
"OTHBC_DT_NM",
"NAT",
"NTT_SJ",
"SMMAR_CN",
"risk_type",
"risk_score",
"risk_level"
]
]


final_df.columns = [
"date",
"country",
"title",
"summary",
"risk_type",
"risk_score",
"risk_level"
]


final_df.to_csv(
    "kotra_supply_data_final.csv",
    index=False,
    encoding="utf-8-sig"
)
