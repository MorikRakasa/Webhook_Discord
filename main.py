import feedparser
import requests
import json
import os

# ==========================================
# KONFIGURASI DISCORD & ROLE MENTION
# ==========================================
DISCORD_WEBHOOK_LOKER = "https://discord.com/api/webhooks/1528366238907109489/sZQE74G03TQBKUooLYT3JZyCFXz-evLndBwuKmfNOc4rlz6A_DT-VUPdvXkJFqfBaVp8"
DISCORD_WEBHOOK_MAGANG = "https://discord.com/api/webhooks/1528373679128445018/A5pcamPR5tIF2PVVIt3N38jhAcXdHJKiFicMHl-JxblLe07WnyWC5PZURHZ7xd92-pOY"

# ID Role Discord untuk masing-masing kategori
ROLE_ID_LOKER = "1506314812362199214"
ROLE_ID_MAGANG = "1506314654761353246"

# ==========================================
# KONFIGURASI AKUN & KEYWORDS
# ==========================================
ACCOUNTS_LOKER = ["lokerdotid", "lokerjogjax", "jogjalowker", "disiniloker", "magnecareer", "twitlowongan", "sobatmagang_id"]
ACCOUNTS_MAGANG = ["sobatmagang_id", "disiniloker", "magnecareer"]

LOKER_KEYWORDS = [kw.lower() for kw in ["#InfoLoker", "#Loker", "INFO LOKER", "#lowker", "#lowongan", "Loker Jogja", "#LokerPam", "#Lowongan"]]
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
        with open(LOG_FILE, "w") as f:
            json.dump(posted_list, f)

# ==========================================
# FUNGSI PENGIRIMAN DISCORD + MENTION ROLE
# ==========================================
def send_to_discord(webhook_url, text, link, category, role_id):
    """
    Mengirimkan pesan ke Discord menggunakan Webhook.
    - 'content' digunakan untuk mentag role agar mendatangkan notifikasi.
    - 'embeds' digunakan untuk merapikan informasi postingan.
    """
    role_mention = f"<@&{role_id}>"
    
    embed = {
        "title": f"📢 Lowongan Kategori: {category.upper()}",
        "description": text,
        "url": link,
        "color": 3447003 if category == "loker" else 15158332 # Biru untuk Loker, Merah untuk Magang
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

# ==========================================
# FUNGSI UTAMA (SCRAPING & ROUTING)
# ==========================================
def main():
    posted_tweets = load_posted_tweets()
    all_accounts = list(set(ACCOUNTS_LOKER + ACCOUNTS_MAGANG))
    
    for account in all_accounts:
        rss_url = f"https://xcancel.com/{account}/rss"
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries:
            tweet_link = entry.link
            
            # Ekstraksi Tweet ID secara aman dari URL Xcancel
            try:
                tweet_id = tweet_link.split('/')[-1].replace('#m', '')
            except Exception:
                continue
            
            if not tweet_id or tweet_id in posted_tweets:
                continue
                
            text = entry.title.lower()
            original_text = entry.title
            
            # Evaluasi Kategori
            is_loker = account in ACCOUNTS_LOKER or any(kw in text for kw in LOKER_KEYWORDS)
            is_magang = account in ACCOUNTS_MAGANG or any(kw in text for kw in MAGANG_KEYWORDS)
            
            sent = False
            
            # Routing ke Loker
            if is_loker:
                send_to_discord(DISCORD_WEBHOOK_LOKER, original_text, tweet_link, "loker", ROLE_ID_LOKER)
                sent = True
                
            # Routing ke Magang
            if is_magang:
                send_to_discord(DISCORD_WEBHOOK_MAGANG, original_text, tweet_link, "magang", ROLE_ID_MAGANG)
                sent = True
                
            # Catat ID jika berhasil terkirim ke salah satu / kedua channel
            if sent:
                save_posted_tweet(tweet_id, posted_tweets)

if __name__ == "__main__":
    main()
