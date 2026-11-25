"""Demo provider: realistic, clearly-labelled SAMPLE data (no Instagram access).

Comments are generated from pools of hand-written texts in English, Hindi,
Gujarati and Hinglish plus emoji-only, questions and spam. No sentiment labels
are attached – the real analysis pipeline classifies them like any other input.
Output is deterministic for a given seed so demo analyses can be re-computed.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from .base import FetchResult, ReelProvider, progress

EN_POS = [
    "This is exactly the review I was waiting for! Subscribed 🔥",
    "Sound quality looks insane for this price",
    "Best creator on my feed, never disappoints",
    "The editing and transitions are so smooth 😍",
    "Love the background music in this one, so good",
    "Honestly the most honest review I've seen, thank you!",
    "Ordered it right after watching this. Can't wait!!",
    "Your videos are always so well shot, camera work is top notch",
    "Great value for money, the battery claims actually sound real",
    "I've been following you for a year and the content keeps getting better",
    "This changed my mind, I was about to buy something worse. Thank you!",
    "Clean design, great bass, and the case is gorgeous 😍",
    "Finally someone who explains the pros AND cons properly. Respect.",
    "Amazing video, the lighting and visuals are cinematic 👏",
    "Wow, the price is unbelievable for these specs. Bought one already",
    "Super helpful comparison, loved the detailed breakdown",
    "Delivery was fast and the support team helped me instantly. Love this brand",
    "The music choice fits the vibe perfectly 🎶",
    "I'm so excited for the next part of this series!!!",
    "Just got mine today and it's even better than the video. 10/10",
    "You deserve way more views. Quality content right here",
    "Great job on the video quality, 4K looks crispy",
]
EN_NEG = [
    "Way too expensive for what you get. Not worth it",
    "Battery died in two days, complete waste of money",
    "Customer service never replied to my emails. Terrible",
    "This feels like a paid promotion, not a genuine review",
    "The build quality is cheap and the case cracked in a week 😡",
    "Audio is so bad, music in the background is too loud and drowns you out",
    "Disappointed. Delivery took a month and the product arrived damaged",
    "Another overpriced gadget. The price makes no sense",
    "Video quality is blurry and the editing is too fast, couldn't follow",
    "Honestly this content is getting boring, same thing every week",
    "Support told me warranty doesn't cover it. So frustrating!!",
    "I returned mine, the mic is awful on calls",
    "You never mention the downsides. Very one-sided video",
    "The sound cuts out constantly. Do not buy, regret it 😤",
]
EN_NEU = [
    "Just ordered one, will update after a week",
    "Watched the full video",
    "Okay, noted",
    "Reel posted yesterday, right? Seen a few reviews already",
    "Comparing this with two others at the moment",
    "I'm using the older version, haven't tried this one",
    "Saved for later",
    "Shipping to the UK takes 5 to 7 days according to the site",
]
EN_Q = [
    "Where can I buy this? Link please?",
    "What's the price in India right now?",
    "Does it work with iPhone and Android both?",
    "How long does the battery actually last?",
    "What's the name of the background track?",
    "Is there a warranty and how long is it?",
    "Does this come in black?",
    "What camera do you use for these videos?",
    "Is it better than the Pro version?",
]
HI = [
    "बहुत बढ़िया वीडियो, मज़ा आ गया!",
    "आवाज़ की क्वालिटी कमाल की है 😍",
    "आपका काम हमेशा से शानदार रहता है",
    "इतने कम दाम में इतना अच्छा प्रोडक्ट, लाजवाब!",
    "दाम बहुत ज़्यादा है, इतने में नहीं खरीदूंगा",
    "बैटरी बिल्कुल बेकार निकली, पैसे बर्बाद",
    "सर्विस बहुत खराब है, कोई जवाब ही नहीं देता",
    "मैंने कल ही ऑर्डर किया है, देखते हैं",
    "वीडियो देखा, ठीक है",
    "रिव्यू बहुत अच्छा था, सब कुछ साफ़ समझ आया",
    "ये कहाँ से मिलेगा? लिंक दीजिए",
    "इसकी कीमत कितनी है?",
    "बैकग्राउंड म्यूज़िक बहुत अच्छा लगा 🎶",
    "वीडियो की क्वालिटी धुंधली है, ठीक से दिखता नहीं",
]
GU = [
    "ખૂબ સરસ વીડિયો! મજા આવી ગઈ 👏",
    "અવાજની ક્વોલિટી ઘણી સારી છે",
    "તમારું કામ હંમેશા શ્રેષ્ઠ હોય છે",
    "આ પ્રોડક્ટ ખરેખર લાજવાબ છે",
    "કિંમત બહુ વધારે છે, પોસાય નહીં",
    "બેટરી એકદમ ખરાબ છે, પૈસા વેડફાઈ ગયા",
    "સર્વિસ બહુ ખરાબ છે, કોઈ જવાબ આપતું નથી",
    "મેં હમણાં જ ઓર્ડર કર્યો છે, જોઈએ શું થાય છે",
    "વીડિયો જોયો, ઠીક છે",
    "આ ક્યાંથી મળશે? લિંક આપો",
    "આની કિંમત કેટલી છે?",
    "સંગીત બહુ સરસ છે, મજા પડી ગઈ ❤️",
]
HINGLISH = [
    "Bhai ekdum mast review hai, sound quality op lag rahi hai 🔥",
    "Yaar tumhara content hamesha best hota hai",
    "Price ke hisaab se bahut accha product hai",
    "Editing aur music dono kamaal ke hain 😍",
    "Ye wala le hi leta hu ab, full paisa vasool",
    "Itna clean video, love it bhai ❤️",
    "Bhai tune sahi review diya, dil jeet liya",
    "Mast video hai, next part kab aayega?",
    "Price bahut zyada hai yaar, itne mein nahi aayega",
    "Battery life bekar hai, 2 din mein hi dead",
    "Customer service ek number ki faltu hai, koi reply nahi karta",
    "Paid promotion lag raha hai, review genuine nahi lagta",
    "Build quality ghatiya hai, ek hafte mein kharab ho gaya 😡",
    "Video ki quality thodi kharab hai, blur aa raha hai",
    "Kal order kiya hai, aane do phir batata hu",
    "Video dekh liya, theek hai",
    "Bhai ye kaha se milega? Link do",
    "Iski price kitni hai?",
    "Kya ye iPhone ke saath chalega?",
    "Warranty kitni hai bhai?",
    "Background music ka naam kya hai? Bahut accha hai",
    "Delivery kitne din mein hoti hai?",
]
EMOJI = ["🔥🔥🔥", "😍😍😍", "👏👏👏", "😂😂😂", "💔", "😡😡", "❤️❤️❤️", "🙌🙌", "👎", "🤮", "🔥😍", "😭😭"]
SPAM = [
    "Follow me for follow back 🔥🔥 @growth_hub_official",
    "Earn $500/day from home, DM me now!!! bit.ly/easy-cash",
    "Check my profile for free giveaway 🎁 click link in bio",
    "Buy cheap followers 10k only $5 t.me/boostgram",
    "WIN iPhone 15 free!!! visit www.free-prizes-now.com",
    "Promote your page, DM for sponsorship collab",
    "Nice pic! Check out my page for daily crypto signals 💰💰 @cryptokingdaily",
    "Hot singles in your area click here http://dating-now.example",
]
SPAM_DUP = ["Follow me for follow back 🔥🔥 @growth_hub_official"] * 2 + [
    "Earn $500/day from home, DM me now!!! bit.ly/easy-cash"
]
REPLIES = [
    "Thank you so much! ❤️", "Glad you liked it!", "Link is in my bio 🙌",
    "Great question, answering in the next video!", "Appreciate the honest feedback.",
    "Agree!", "Same here", "Check the pinned comment for details",
]
FIRST = ["aarav", "diya", "kabir", "meera", "rohan", "isha", "vivaan", "anaya", "neel", "tara",
         "jay", "riya", "dev", "kiara", "om", "sana", "yash", "pooja", "arjun", "nisha",
         "mihir", "hetal", "krish", "zoya", "dhruv", "simran", "parth", "ritu"]
SUFFIX = ["_", ".", "", "_official", "07", "_vlogs", "_x", "98", ".in", "_21"]


def _thumb(title: str) -> str:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='540' height='960' viewBox='0 0 540 960'>"
        "<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
        "<stop offset='0' stop-color='#6366f1'/><stop offset='.55' stop-color='#a855f7'/>"
        "<stop offset='1' stop-color='#ec4899'/></linearGradient></defs>"
        "<rect width='540' height='960' fill='url(#g)'/>"
        "<circle cx='270' cy='440' r='86' fill='white' fill-opacity='.2'/>"
        "<path d='M246 396 L246 484 L322 440 Z' fill='white'/>"
        f"<text x='270' y='640' font-family='Arial' font-size='34' font-weight='700' text-anchor='middle' fill='white'>{title}</text>"
        "<text x='270' y='690' font-family='Arial' font-size='22' text-anchor='middle' fill='white' fill-opacity='.8'>SAMPLE REEL</text>"
        "</svg>"
    )
    return "data:image/svg+xml;utf8," + quote(svg)


def build_demo(seed: int = 7, now: datetime | None = None) -> tuple[dict, list[dict]]:
    rnd = random.Random(seed)
    now = now or datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc) if seed == 7 else (now or datetime.now(timezone.utc))
    published = now - timedelta(days=9)

    pool: list[str] = []
    pool += EN_POS + EN_NEG + EN_NEU + EN_Q + HI + GU + HINGLISH + EMOJI + SPAM + SPAM_DUP
    # a few organic repeats (people really do write the same thing)
    pool += ["Subscribed! #techreview content is unmatched 🔥", "Need a part 2 on this #aurorabuds #earbuds", "Most honest one yet #honestreview",
             "Bhai ye #aurorabuds ka review mast hai", "Comparing with my old pair #earbuds #gadgets", "Loved it #techreview"]
    pool += ["Where can I buy this? Link please?", "Link please", "🔥🔥🔥", "Price?", "Love this 😍"]
    pool += rnd.sample(EN_POS + HINGLISH[:8], 6) + rnd.sample(EN_NEG, 3)
    rnd.shuffle(pool)

    users: set[str] = set()

    def username() -> str:
        for _ in range(50):
            u = rnd.choice(FIRST) + rnd.choice(SUFFIX) + rnd.choice(FIRST)[:3]
            if u not in users:
                users.add(u)
                return u
        return f"user{rnd.randint(1000, 9999)}"

    comments = []
    for i, text in enumerate(pool):
        hours = min(9 * 24 - 1, rnd.expovariate(1 / 30))
        ts = published + timedelta(hours=1 + hours)
        likes = int(min(900, rnd.paretovariate(1.15) * 1.4 - 1))
        n_rep = rnd.choice([0, 0, 0, 0, 1, 1, 2, 3])
        reps = [
            {
                "id": f"demo_r_{i}_{k}",
                "username": "techwithtara_demo" if rnd.random() < 0.4 else username(),
                "text": rnd.choice(REPLIES),
                "timestamp": (ts + timedelta(minutes=rnd.randint(3, 600))).isoformat(),
                "likes": rnd.randint(0, 12),
            }
            for k in range(n_rep)
        ]
        comments.append({
            "id": f"demo_c_{seed}_{i:04d}", "username": username(), "text": text,
            "timestamp": ts.isoformat(), "likes": likes, "reply_count": len(reps), "replies": reps,
        })
    comments.sort(key=lambda c: c["timestamp"], reverse=True)

    reel = {
        "url": "https://www.instagram.com/reel/DEMO_sample/",
        "id": f"demo_reel_{seed}",
        "shortcode": "DEMO_sample",
        "username": "techwithtara_demo",
        "caption": "Honest review: Aurora Buds Pro 🎧 sound, battery, price & my real verdict. "
                   "#earbuds #techreview #honestreview #gadgets #aurorabuds",
        "thumbnail": _thumb("Aurora Buds Pro review"),
        "published_at": published.isoformat(),
        "views": 184320,
        "likes": 12847,
        "comments_count": 1284,   # the Reel's total; we only 'have' a sample of it
        "duration_seconds": 27.4,
    }
    return reel, comments


class MockProvider(ReelProvider):
    name = "demo-sample-data"
    is_demo = True

    def __init__(self, seed: int = 7):
        self.seed = seed

    def fetch(self, url: str, max_comments: int):
        yield progress("metadata", 8, "Loading sample Reel metadata (demo data)…")
        reel, comments = build_demo(self.seed)
        yield progress("comments", 30, f"Loaded {len(comments)} sample comments…")
        return reel, comments[:max_comments], [
            "Demo mode: all Reel metadata and comments are generated SAMPLE data, not from Instagram."
        ]
