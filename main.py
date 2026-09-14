import os
import requests
from supabase import create_client

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def search_naver(target, keyword):
    url = f"https://openapi.naver.com/v1/search/{target}.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": keyword,
        "display": 10,
        "sort": "date"
    }
    res = requests.get(url, headers=headers, params=params)
    return res.json().get("items", []) if res.status_code == 200 else []

def send_slack(source_name, title, link, keyword):
    payload = {
        "text": f"🚖 *신규 택시 문의글 [{source_name} / 키워드: {keyword}]*\n• *제목*: {title}\n• *링크*: {link}"
    }
    requests.post(SLACK_WEBHOOK_URL, json=payload)

def main():
    targets = [("지식iN", "kin"), ("네이버카페", "cafearticle")]
    
    # 25개 자치구 목록
    districts = [
        "종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구", "성북구", 
        "강북구", "도봉구", "노원구", "은평구", "서대문구", "마포구", "양천구", "강서구", 
        "구로구", "금천구", "영등포구", "동작구", "관악구", "서초구", "강남구", "송파구", "강동구"
    ]
    
    # 기본 모니터링 키워드
    keywords = [
        # 기본 및 입문/근무형태 키워드
        "서울법인택시", "서울법인", "법인입문", "법인택시 입문", "서울 택시 구직", "법인택시 구직",
        "도급 택시", "도급제 택시", "리스제 택시", "일차 택시"
    ]
    
    # 각 구별 (택시 / 법인택시 / 법인) 조합 키워드 자동 생성하여 추가
    for gu in districts:
        keywords.append(f"{gu} 택시")
        keywords.append(f"{gu} 법인택시")
        keywords.append(f"{gu} 법인")

    for source_name, target_key in targets:
        for keyword in keywords:
            items = search_naver(target_key, keyword)
            for item in items:
                clean_title = item["title"].replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&lt;", '<').replace("&gt;", '>')
                link = item["link"]
                
                # DB 중복 체크 후 저장 및 슬랙 발송
                existing = supabase.table("inquiries").select("id").eq("link", link).execute()
                if not existing.data:
                    supabase.table("inquiries").insert({
                        "title": clean_title,
                        "link": link,
                        "location": "서울",
                        "source": f"네이버 {source_name}"
                    }).execute()
                    
                    send_slack(source_name, clean_title, link, keyword)

if __name__ == "__main__":
    main()
