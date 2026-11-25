"""Labelled multilingual corpus the built-in sentiment/emotion models are trained on at startup."""

SENTIMENT = {
    "positive": [
        "love this video so much", "amazing content, keep it up", "this is awesome and super helpful",
        "great review, very detailed and honest", "fantastic quality, totally worth the money", "best channel ever",
        "so good, I bought it after watching", "brilliant work, really enjoyed it", "perfect, exactly what I needed",
        "this made my day, thank you", "wonderful and inspiring", "really impressed with the sound and design",
        "excellent value and fast delivery", "gorgeous visuals and great editing", "I am so happy with this purchase",
        "superb video, subscribed", "👏👏 great job", "😍😍 love it", "🔥🔥 awesome", "❤️❤️ so good", "🙌 amazing",
        "bahut accha video hai bhai", "ekdum mast content, maza aa gaya", "kamaal ka product hai, paisa vasool",
        "bhai tu best hai, love it", "sahi review diya yaar, dil khush ho gaya", "bahut badiya, full support",
        "shandar video, aise hi banate raho", "lajawab quality hai", "mujhe ye bahut pasand aaya",
        "बहुत अच्छा वीडियो है", "शानदार काम, मज़ा आ गया", "बहुत बढ़िया प्रोडक्ट है, पसंद आया", "लाजवाब क्वालिटी",
        "आपका कंटेंट सबसे अच्छा है", "बहुत सुंदर, धन्यवाद", "कमाल का रिव्यू",
        "ખૂબ સરસ વીડિયો છે", "બહુ સારું કામ, મજા આવી", "અદભુત પ્રોડક્ટ છે", "તમારું કન્ટેન્ટ શ્રેષ્ઠ છે",
        "ખૂબ જ સુંદર, આભાર", "ઘણું સારું છે",
    ],
    "negative": [
        "this is terrible, total waste of money", "worst product ever, do not buy", "very disappointed with the quality",
        "awful service and nobody replies", "too expensive and not worth it", "I hate this, it broke immediately",
        "boring and misleading video", "the sound is horrible and the battery is bad", "scam, fake review",
        "so bad, regret buying", "poor quality, stopped working", "useless and overpriced", "worst experience of my life",
        "cheap build and it keeps disconnecting", "unwatchable, blurry and annoying", "👎 bad", "😡😡 terrible", "🤮 awful", "💔 disappointed",
        "bahut bekar product hai, paisa barbaad", "ekdum faltu video, time waste", "bakwas quality hai bhai",
        "ghatiya service, koi reply nahi", "bahut mehnga hai, nahi lunga", "kharab nikla, dhoka hai",
        "mujhe bilkul pasand nahi aaya", "ye to fraud hai yaar",
        "बहुत बेकार प्रोडक्ट है", "बकवास वीडियो, समय बर्बाद", "बहुत खराब सर्विस है", "बहुत महंगा है, पैसे बर्बाद",
        "घटिया क्वालिटी", "धोखा है ये",
        "ખૂબ ખરાબ પ્રોડક્ટ છે", "બકવાસ વીડિયો, સમય બગડ્યો", "બહુ ખરાબ સર્વિસ છે", "બહુ મોંઘું છે",
        "નકામું છે, પૈસા વેડફાયા", "છેતરપિંડી છે",
    ],
    "neutral": [
        "just ordered one", "watched the video", "okay noted", "saved for later", "will try and update", "seen this already",
        "posted yesterday", "comparing with another model", "it arrives next week", "I have the older version",
        "this is a video about earbuds", "first time seeing this channel", "available in two colours", "reading the comments now",
        "kal order kiya hai", "video dekh liya", "dekhte hain kya hota hai", "baad mein batata hu", "theek hai",
        "ek hafte mein aayega", "pehle wala version hai mere paas",
        "मैंने ऑर्डर किया है", "वीडियो देखा", "देखते हैं", "ठीक है", "अगले हफ्ते आएगा",
        "મેં ઓર્ડર કર્યો છે", "વીડિયો જોયો", "જોઈએ શું થાય છે", "ઠીક છે", "આવતા અઠવાડિયે આવશે",
        "😐", "🤔", "👀",
    ],
}

EMOTION = {
    "Happy": [
        "so happy with this", "this made me smile", "love it, thank you", "feeling great about this purchase", "what a lovely video",
        "bahut khush hu bhai", "dil khush ho gaya", "मुझे बहुत खुशी हुई", "बहुत अच्छा लगा", "ખૂબ ખુશ છું", "મજા આવી", "😊😊", "❤️❤️",
    ],
    "Excited": [
        "can't wait for the next one!!", "omg this is amazing!!!", "so excited to try this", "wow!!! incredible", "just ordered, so hyped",
        "bhai next part kab aayega, wait nahi ho raha", "wow kya baat hai!!", "अगला वीडियो कब आएगा?? बेसब्र हूँ", "वाह वाह, कमाल!!", "હવે રાહ નથી જોવાતી!!", "વાહ શું વાત છે!!",
        "🔥🔥🔥", "🤩🤩", "🙌🙌",
    ],
    "Angry": [
        "this is a scam, I'm furious", "disgusting service, I hate this company", "stop lying to people", "absolutely outrageous behaviour",
        "ye fraud hai, bahut gussa aa raha hai", "dhoka diya in logon ne", "बहुत गुस्सा आ रहा है, धोखा है", "शर्म आनी चाहिए", "બહુ ગુસ્સો આવે છે, છેતરપિંડી છે", "શરમ આવવી જોઈએ",
        "😡😡", "🤬",
    ],
    "Sad": [
        "so sad, I really wanted this to work", "heartbreaking, it broke after a week", "feeling let down", "I'm disappointed and upset",
        "dukh hua ye dekh kar", "bahut bura laga yaar", "बहुत दुख हुआ", "मन उदास हो गया", "બહુ દુઃખ થયું", "ખૂબ ખરાબ લાગ્યું",
        "😢😢", "💔", "😭",
    ],
    "Frustrated": [
        "still no reply from support, so frustrating", "it keeps disconnecting, so annoying", "tried everything and nothing works", "waited a month, ridiculous delays",
        "baar baar kharab ho raha hai, pareshan hu", "koi reply hi nahi deta, bahut irritating hai", "परेशान हो गया हूँ, कुछ काम नहीं करता", "कोई जवाब नहीं देता, बहुत झंझट है", "બહુ હેરાન થઈ ગયો છું", "કોઈ જવાબ નથી આપતું, કંટાળી ગયો",
        "😤😤", "🙄",
    ],
    "Neutral": [
        "just ordered one", "watched the video", "okay noted", "saved for later", "comparing with another model", "where can I buy it?",
        "kal order kiya hai", "video dekh liya", "link do", "मैंने वीडियो देखा", "ठीक है", "કિંમત કેટલી છે?", "વીડિયો જોયો", "🤔", "👀",
    ],
}


# ---- extra hard cases: negation, questions (neutral), pricing/service complaints per language ----
SENTIMENT["positive"] += [
    "never disappoints, always great", "this channel never lets me down", "you never fail to impress", "not bad at all, actually really good",
    "worth every penny", "great price for the quality", "so smooth and clean", "the transitions are beautiful", "amazing sound and the bass is deep",
    "loved the music choice", "very helpful comparison, thanks", "fast delivery and the support was kind", "crisp video and perfect lighting",
    "can't wait for the next part, this series is great", "honest and genuine review, respect", "you deserve more subscribers",
    "kabhi disappoint nahi karta ye channel", "bahut sahi price hai, le lunga", "music aur editing dono top class", "tumhara video hamesha mast hota hai",
    "ye price me best option hai", "delivery fast thi, service bhi achhi", "bhai tune ekdum clear explain kiya", "next part ka wait hai, bahut badiya series",
    "इतने कम दाम में बहुत अच्छा है", "म्यूज़िक बहुत प्यारा है", "आपने बहुत अच्छे से समझाया", "सर्विस बहुत अच्छी थी, तुरंत जवाब मिला", "वीडियो की क्वालिटी एकदम साफ़ है",
    "આ ભાવમાં ખૂબ સારું છે", "સંગીત ખૂબ સરસ છે", "તમે ખૂબ સારી રીતે સમજાવ્યું", "સર્વિસ ઘણી સારી હતી", "વીડિયો ક્વોલિટી એકદમ સાફ છે",
    "😍🔥 love it", "👏 superb", "❤️🔥", "🙌🙌🙌", "😂😂 hilarious, love it",
]
SENTIMENT["negative"] += [
    "boring content, same thing every week", "the content is getting repetitive and dull", "price is way too high for this", "not worth the price at all",
    "support never helped, so frustrating", "warranty denied, terrible support", "delivery took forever and arrived broken", "the video is blurry and hard to watch",
    "music is too loud, can't hear you", "this looks like a paid promotion", "one-sided review, hides the downsides", "mic is awful and the sound cuts out",
    "I regret buying this, returned it", "so overpriced, makes no sense", "very disappointed, would not recommend",
    "price bahut zyada hai, nahi aayega budget me", "content ab boring hota ja raha hai", "support ne koi help nahi ki, bakwas", "video blur hai kuch dikhta nahi",
    "paid promotion lagta hai, genuine nahi", "bahut mehnga hai ye, paisa vasool nahi", "music bahut tez hai, awaaz nahi aati",
    "दाम बहुत ज़्यादा है, नहीं खरीदूंगा", "बहुत महंगा है, बजट में नहीं", "कंटेंट बोरिंग हो गया है", "वीडियो धुंधली है, कुछ दिखता नहीं", "सपोर्ट ने कोई मदद नहीं की", "ये पेड प्रमोशन लगता है",
    "કિંમત બહુ વધારે છે, પોસાય નહીં", "ખૂબ મોંઘું છે, બજેટમાં નથી", "કન્ટેન્ટ કંટાળાજનક થઈ ગયું છે", "વીડિયો ધુંધળો છે, કંઈ દેખાતું નથી", "સપોર્ટે કોઈ મદદ ન કરી",
    "😡 so annoyed", "👎👎", "🤮🤮 awful", "😤 not happy",
]
SENTIMENT["neutral"] += [
    "where can I buy this?", "what is the price?", "link please", "does it work with android?", "how long is the warranty?", "which colours are available?",
    "what camera do you use?", "what is the name of the song?", "is it available in india?", "how many hours is the battery?", "does it come in black?",
    "how do I order this?", "what's the difference between the two models?", "when is the next video?", "can you review the other model too?",
    "ye kaha se milega?", "iski price kitni hai?", "link do bhai", "kya ye android pe chalega?", "warranty kitni hai?", "kitne din me delivery hogi?",
    "song ka naam kya hai?", "ye kis colour me aata hai?", "kaun sa model lena chahiye?", "price kya hai?",
    "ये कहाँ से मिलेगा?", "इसकी कीमत क्या है?", "लिंक दीजिए", "क्या ये एंड्रॉयड पर चलेगा?", "वारंटी कितनी है?", "डिलीवरी में कितने दिन लगेंगे?", "गाने का नाम क्या है?",
    "આ ક્યાંથી મળશે?", "આની કિંમત કેટલી છે?", "લિંક આપો", "શું આ એન્ડ્રોઇડ પર ચાલશે?", "વોરંટી કેટલી છે?", "ડિલિવરી કેટલા દિવસમાં થશે?", "ગીતનું નામ શું છે?",
    "price?", "link?", "👀👀", "😐😐", "🤔🤔",
    "ordered it, will share feedback later", "will compare with another one first", "bought one, waiting for delivery", "I use the older version", "shared with a friend",
]
EMOTION["Neutral"] += [
    "where can I buy this?", "what is the price?", "does it work with android?", "how long is the warranty?", "ye kaha se milega?", "iski price kitni hai?",
    "ये कहाँ से मिलेगा?", "इसकी कीमत क्या है?", "આની કિંમત કેટલી છે?", "આ ક્યાંથી મળશે?", "ordered it, will share feedback later", "bought one, waiting for delivery",
]
EMOTION["Frustrated"] += [
    "support told me warranty doesn't cover it, so frustrating", "this content is getting boring and repetitive", "price is ridiculous for what you get",
    "delivery took a month, so annoying", "dam bahut zyada hai, pareshani hai", "ज़्यादा दाम है, बहुत परेशानी है", "બહુ મોંઘું છે, હેરાન થઈ ગયો",
]
EMOTION["Happy"] += [
    "great value, very happy", "love the music choice", "the editing is so smooth", "thanks for the honest review", "bahut accha laga music", "संगीत बहुत अच्छा लगा", "સંગીત બહુ ગમ્યું",
]
EMOTION["Excited"] += [
    "ordered it right now, can't wait!!", "can't wait for the next part!!!", "next part kab aayega, excited hu!!", "wow this is insane!!", "अगला पार्ट कब आएगा?? बहुत एक्साइटेड हूँ",
]
