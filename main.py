import os
import requests
from supabase import create_client

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def search_naver(target):
    url = f"https://openapi.naver.com/v1/search/{target}.json?query=서울+법인택시+구직&display=10&sort=date"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    res = requests.get(url, headers=headers)
    return res.json().get("items", []) if res.status_code == 200 else []

def send_slack(source_name, title, link):
    payload = {
        "text": f"🚖 *신규 서울 법인택시 문의글 [{source_name}]*\n• *제목*: {title}\n• *링크*: {link}"
    }
    requests.post(SLACK_WEBHOOK_URL, json=payload)

def main():
    targets = [("지식iN", "kin"), ("네이버카페", "cafearticle")]
    
    for source_name, target_key in targets:
        items = search_naver(target_key)
        for item in items:
            clean_title = item["title"].replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&lt;", '<').replace("&gt;", '>')
            link = item["link"]
            
            existing = supabase.table("inquiries").select("id").eq("link", link).execute()
            if not existing.data:
                supabase.table("inquiries").insert({
                    "title": clean_title,
                    "link": link,
                    "location": "서울",
                    "source": f"네이버 {source_name}"
                }).execute()
                
                send_slack(source_name, clean_title, link)

if __name__ == "__main__":
    main()
