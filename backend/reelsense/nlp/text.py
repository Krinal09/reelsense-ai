"""Tokenisation, stopwords and script-based language detection."""
from __future__ import annotations

import re

WORD_RE = re.compile(r"[\wऀ-ॿ઀-૿]+", re.UNICODE)
HASHTAG_RE = re.compile(r"#[\wऀ-ॿ઀-૿]+", re.UNICODE)
MENTION_RE = re.compile(r"@[\w.]+")
URL_RE = re.compile(r"(https?://\S+|www\.\S+|\b[\w-]+\.(?:com|in|net|io|me|ly|co|org)\b/?\S*|\bt\.me/\S+|\bbit\.ly/\S+)", re.I)
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF⬀-⯿←-⇿️‍]"
)
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
GUJARATI = re.compile(r"[઀-૿]")
LATIN = re.compile(r"[A-Za-z]")
OTHER_SCRIPT = re.compile(r"[Ѐ-ӿ؀-ۿঀ-৿଀-෿฀-໿぀-ヿ一-鿿가-힯]")

STOPWORDS = set("""
a an the and or but if so of to in on at by for with from as is are was were be been being am do does did done have has had
i me my we our you your yours he she it its they them their this that these those there here what which who whom when where why how
not no nor too very can could would should will just than then also only about into over out up down off again more most some any
ve re ll two day week all both each few other such own same s t don now get got really one like im ive u ur im
hai hain ho hoga hogi hota hoti tha thi the ka ki ke ko se me mein par pe ye yeh wo woh to toh bhi hi na nahi nhi aur ya
kya kyu kyun kaise kaha kahan kab kitna kitni kitne kaun ek is us in un tum tu aap hum main mai mera meri mere tera teri tere
tumhara tumhare apna lo do de diya liya raha rahi rahe gaya gayi gaye bhai yaar bro ab abhi phir jab tab agar lekin magar
है हैं हो था थी थे का की के को से में पर ये यह वो और या भी ही तो न नहीं क्या कैसे कहाँ कब कितना कितनी कौन एक इस उस मैं हम आप तुम मेरा मेरी
छे છે હતું હતી ના નો ની નું માં ને થી પર આ એ અને પણ તો નથી કે શું ક્યાં કેટલી કેટલું કેવી કોણ ક્યારે કેમ મેં હું તમે તમારું આ
""".split())

# Common Romanised-Hindi/Gujarati words used to tell Hinglish from English.
HINGLISH_MARKERS = set("""
hai hain nahi nhi bhai yaar kya kyu kaise kaha kahan kab kitna kitni kitne bahut bohot accha acha achha mast bekar faltu
ekdum kamaal zyada jyada paisa paise hisaab liya diya karo kare karna lag lagta lagti raha rahi mein mujhe tumhara tumhare
aapka aapke tera mera meri sahi theek thik wala wali waala aane aayega milega dena do abhi kal aaj kharab ghatiya jaldi
dekh dekha dekhna mat toh bas lekin par aur bhi ho hu hun hoon tha thi gaya gayi chal chalega le lo link-do ghar sab kuch
""".split())


def tokenize(text: str) -> list[str]:
    return [t for t in WORD_RE.findall((text or "").lower())]


def content_tokens(text: str) -> list[str]:
    out = []
    for t in tokenize(URL_RE.sub(" ", text or "")):
        if len(t) < 2 or t in STOPWORDS or t.isdigit():
            continue
        out.append(t)
    return out


def emoji_count(text: str) -> int:
    return len(EMOJI_RE.findall(text or ""))


def detect_language(text: str) -> tuple[str, str]:
    """Return (code, display name). Script-based, so Hindi/Gujarati are reliable;
    Latin text is split into English vs Hinglish with a Romanised-Hindi lexicon."""
    t = text or ""
    dev, guj = len(DEVANAGARI.findall(t)), len(GUJARATI.findall(t))
    lat = len(LATIN.findall(t))
    other = len(OTHER_SCRIPT.findall(t))
    if guj and guj >= dev:
        return "gu", "Gujarati"
    if dev:
        return "hi", "Hindi"
    if other and other >= lat:
        return "other", "Other"
    if lat == 0:
        return ("emoji", "Emoji") if emoji_count(t) else ("und", "Unknown")
    toks = tokenize(t)
    hits = sum(1 for w in toks if w in HINGLISH_MARKERS)
    if hits >= 2 or (hits == 1 and len(toks) <= 5 and toks and toks[0] != "link"):
        return "hinglish", "Hinglish"
    return "en", "English"
