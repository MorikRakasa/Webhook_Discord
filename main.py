import feedparser
import requests
import json
import os

# ==========================================
# KONFIGURASI DISCORD & ROLE MENTION
# ==========================================
DISCORD_WEBHOOK_LOKER = "https://discord.com/api/webhooks/1528366238907109489/sZQE74G03TQBKUooLYT3JZyCFXz-evLndBwuKmfNOc4rlz6A_DT-VUPdvXkJFqfBaVp8"
DISCORD_WEBHOOK_MAGANG = "https://discord.com/api/webhooks/1528373679128445018/A5pcamPR5tIF2PVVIt3N38jhAcXdHJKiFicMHl-JxblLe07WnyWC5PZURHZ7xd92-pOY"

ROLE_ID_LOKER = "1506314654761353246"
ROLE_ID_MAGANG = "1506314812362199214"

# ==========================================
# KONFIGURASI AKUN & KEYWORDS
# ==========================================
ACCOUNTS_LOKER = ["lokerdotid", "lokerjogjax", "jogjalowker", "disiniloker", "magnecareer", "twitlowongan", "sobatmagang_id", "glintsid"]
ACCOUNTS_MAGANG = ["sobatmagang_id", "disiniloker", "magnecareer"]

LOKER_KEYWORDS = [kw.lower() for kw in ["#InfoLoker", "#Loker", "INFO LOKER", "#lowker", "#lowongan", "Loker Jogja", "#LokerPam", "#Lowongan", "#infocariloker", "#infoloker", "#lowongankerja", "disiniloker"]]
MAGANG_KEYWORDS = [kw.lower() for kw in ["#infoMagang", "#magangID", "#magangYuk", "#magang", "#MagangPam"]]

LOG_FILE = "posted_tweets.json"

# ==========================================
# FUNGSI MANAJEMEN LOG (PENCEGAHAN DUPLIKASI)
# ==========================================
def load_posted_tweets():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_posted_tweet(tweet_id, posted_list):
    if tweet_id not in posted_list:
        posted_list.append(tweet_id)
        if len(posted_list) > 500:
            posted_list = posted_list[-500:]
        with open(LOG_FILE, "w") as f:
            json.dump(posted_list, f)

def send_to_discord(webhook_url, text, link, category, role_id):
    role_mention = f"<@&{role_id}>"
    embed = {
        "title": f"📢 Lowongan Kategori: {category.upper()}",
        "description": text[:4000],
        "url": link,
        "color": 3447003 if category == "loker" else 15158332
    }
    payload = {
        "content": f"Info baru buat teman-teman! {role_mention}",
        "embeds": [embed]
    }
    response = requests.post(webhook_url, json=payload)
    if response.status_code in [200, 204]:
        print(f"✅ Berhasil mengirim postingan ke channel {category}")
    else:
        print(f"❌ Gagal mengirim ke Discord ({category}). Status: {response.status_code}, Respon: {response.text}")

def main():
    posted_tweets = load_posted_tweets()
    all_accounts = list(set(ACCOUNTS_LOKER + ACCOUNTS_MAGANG))
    print(f"🔍 Memulai pengecekan untuk {len(all_accounts)} akun...")

    for account in all_accounts:
        rss_url = f"https://xcancel.com/{account}/rss"
        print(f"📡 Mengambil RSS dari: {rss_url}")
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            response_rss = requests.get(rss_url, headers=headers, timeout=10)
            if response_rss.status_code != 200:
                print(f"⚠️ Gagal akses RSS {account} (Status Code: {response_rss.status_code})")
                continue
                
            feed = feedparser.parse(response_rss.content)
        except Exception as e:
            print(f"⚠️ Error saat mengambil RSS {account}: {e}")
            continue
        
        if not feed.entries:
            print(f"⚠️ Tidak ada entri RSS ditemukan untuk akun @{account}")
            continue

        latest_entries = feed.entries[:5]
        print(f"✨ Ditemukan {len(latest_entries)} entri dari @{account}")

        for entry in latest_entries:
            tweet_link = entry.get("link", "")
            
            if not tweet_link:
                continue
            
            try:
                if "/status/" in tweet_link:
                    parts = tweet_link.split('/')
                    status_index = parts.index('status')
                    tweet_id = parts[status_index + 1].replace('#m', '').split('?')[0]
                else:
                    tweet_id = entry.get("id", tweet_link).split('/')[-1].replace('#m', '').split('?')[0]
            except Exception as e:
                print(f"⚠️ Gagal ekstrak ID dari link {tweet_link}: {e}")
                continue
            
            if not tweet_id or tweet_id in posted_tweets:
                continue
                
            text = entry.get("title", "").lower()
            original_text = entry.get("title", "")
            
            is_loker = account in ACCOUNTS_LOKER or any(kw in text for kw in LOKER_KEYWORDS)
            is_magang = account in ACCOUNTS_MAGANG or any(kw in text for kw in MAGANG_KEYWORDS)
            
            sent = False
            
            if is_loker:
                send_to_discord(DISCORD_WEBHOOK_LOKER, original_text, tweet_link, "loker", ROLE_ID_LOKER)
                sent = True
                
            if is_magang:
                send_to_discord(DISCORD_WEBHOOK_MAGANG, original_text, tweet_link, "magang", ROLE_ID_MAGANG)
                sent = True
                
            if sent:
                save_posted_tweet(tweet_id, posted_tweets)

    print("🎉 Selesai memproses seluruh akun.")

if __name__ == "__main__":
    main()