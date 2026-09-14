import os
import requests
from supabase import create_client

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def search_naver():
    url = "https://openapi.naver.com/v1/search/kin.json?query=서울+법인택시+구직&display=10&sort=date"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    res = requests.get(url, headers=headers)
    return res.json().get("items", []) if res.status_code == 200 else []

def send_slack(title, link):
    payload = {
        "text": f"🚖 *신규 서울 법인택시 문의글*\n• *제목*: {title}\n• *링크*: {link}"
    }
    requests.post(SLACK_WEBHOOK_URL, json=payload)

def main():
    items = search_naver()
    for item in items:
        clean_title = item["title"].replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
        link = item["link"]
        
        # 중복 체크 후 저장
        existing = supabase.table("inquiries").select("id").eq("link", link).execute()
        if not existing.data:
            supabase.table("inquiries").insert({
                "title": clean_title,
                "link": link,
                "location": "서울",
                "source": "네이버 지식iN"
            }).execute()
            
            send_slack(clean_title, link)

if __name__ == "__main__":
    main()
