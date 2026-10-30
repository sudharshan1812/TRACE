"""
TRACE Synthetic Dataset Generator — Indian Dark Net & Encrypted Platform Drug Intelligence
========================================================================================
Generates a highly diverse, realistic, and balanced synthetic dataset for training and
benchmarking the Slang Engine NLP classifier / threat detection model.

Features:
- Multi-lingual / Code-switched text (Hinglish, Punjabi Romanized, Hindi Romanized, English)
- Specific drug classes (Cannabis, Charas, Cocaine/Chitta, Meth/Ice, MDMA, Heroin, Opioids, LSD, Pharma)
- Realistic trade dynamics (Dead drops, stealth courier, Speedpost, USDT/TRC20, XMR, BTC, UPI mules)
- Obfuscation techniques (Leetspeak, emoji code words, zero-width spaces, deliberate typos)
- Rich Benign & Hard-Negative samples (Indian wholesale trade, legitimate pharma, food/beverage slang)
- Rich metadata labeling (label, category, substances, location, platform, risk_level, obfuscation)
- Outputs to CSV, JSON, and JSONL formats
"""

import os
import json
import random
import argparse
import hashlib
from typing import List, Dict, Tuple, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEXICON_PATH = os.path.join(BASE_DIR, "data", "slang_lexicon.json")

SUBSTANCE_TEMPLATES = {
    "cannabis": {
        "slang_terms": [
            "ganja", "weed", "maal", "green maal", "desi maal", "shillong", "idukki gold",
            "mysore mango", "kush", "hydro", "flower", "blunt", "joint", "420", "phukka",
            "baba", "patti", "stuff", "greens", "og kush", "purple haze", "buds", "dabs"
        ],
        "punjabi_slang": ["sulfa", "sheela", "phook", "sigs", "bhaang"],
        "emojis": ["🌿", "🍃", "🌸", "🍁", "🔥", "💨", "🥦"],
        "price_ranges": ["₹400/pudi", "₹800/10g", "₹1500/tole", "₹2500/50g", "₹3500/ounce", "₹2000/g for cali"]
    },
    "charas_hashish": {
        "slang_terms": [
            "charas", "malana cream", "tosh", "kasol", "cream", "batti", "rub", "kali",
            "black hash", "atta", "chocolate", "slate", "manali cream", "super cream"
        ],
        "punjabi_slang": ["sulfa", "kali patti", "batti", "malana"],
        "emojis": ["🍫", "🟫", "🏔️", "🔥", "✨"],
        "price_ranges": ["₹2000/tola", "₹3500/tola", "₹5000/batti", "₹12000/50g", "₹25000/100g"]
    },
    "cocaine": {
        "slang_terms": [
            "coke", "chitta", "snow", "blow", "safed powder", "white maal", "safed",
            "line", "charlie", "flake", "perico", "yayo", "nose candy", "pure 777", "a-1 pure"
        ],
        "punjabi_slang": ["chitta maal", "safed", "white", "powder"],
        "emojis": ["❄️", "⛄", "⛷️", "🧂", "💎", "⚡"],
        "price_ranges": ["₹4000/g", "₹6500/g", "₹8000/g (colombian 90%)", "₹25000/5g", "₹45000/10g"]
    },
    "methamphetamine": {
        "slang_terms": [
            "ice", "crystal", "crystal meth", "meth", "tukdi", "tukda", "shard", "glass",
            "tina", "speed", "clear", "pure crystal", "shatter", "crank"
        ],
        "punjabi_slang": ["ice", "tukdi", "chitta crystal"],
        "emojis": ["🧊", "💎", "⚡", "🔬", "💨"],
        "price_ranges": ["₹3000/g", "₹5000/g", "₹13500/5g", "₹24000/10g", "₹100k/bulk 50g"]
    },
    "mdma": {
        "slang_terms": [
            "mdma", "molly", "ecstasy", "extacy", "party pill", "goli", "tikki", "mandy",
            "disco biscuits", "xtc", "pingers", "rolls", "punisher", "tesla 300mg", "mercedes"
        ],
        "punjabi_slang": ["party goli", "tikki", "rolls"],
        "emojis": ["💊", "🥳", "✨", "🚀", "⚡", "🍬", "🎉"],
        "price_ranges": ["₹1200/pill", "₹1800/piece", "₹3500/g crystal", "₹7000/5 pills", "₹12000/10 pills"]
    },
    "heroin_opioid": {
        "slang_terms": [
            "brown sugar", "smack", "chitta", "heroin", "dope", "junk", "china white",
            "afeem", "amal", "posta", "doda", "bhuki", "kalla", "black gold", "ras"
        ],
        "punjabi_slang": ["chitta", "doda", "bhuki", "afeem da paani", "amal"],
        "emojis": ["💉", "🟤", "🥀", "💀", "⏳"],
        "price_ranges": ["₹1500/pudi", "₹3000/g", "₹6000/2g", "₹14000/5g", "₹25000/10g"]
    },
    "lsd_psychedelics": {
        "slang_terms": [
            "acid", "lsd", "blotter", "tabs", "trip", "gel tab", "microdot", "california sunshine",
            "shrooms", "magic mushrooms", "kodai mush", "kodaikanal shrooms", "dmt", "changa"
        ],
        "punjabi_slang": ["trip", "blotter", "stamp"],
        "emojis": ["🍄", "👅", "🌈", "🚀", "🌌", "🎨", "👁️"],
        "price_ranges": ["₹1200/tab", "₹2000/gel tab 250ug", "₹5000/strip (5 tabs)", "₹3000/packet shrooms", "₹8000/sheet"]
    },
    "pharmaceutical_abuse": {
        "slang_terms": [
            "xanax", "alprazolam", "percs", "oxycodone", "tramadol", "codeine", "corex",
            "phensedyl", "toseina", "lean", "purple drank", "buprenorphine", "norphin",
            "nasha ki goli", "downers", "k-pin", "valium", "d10"
        ],
        "punjabi_slang": ["nasha goli", "tika", "corex bottle", "pharma"],
        "emojis": ["💊", "🧪", "🟣", "🍼", "💤"],
        "price_ranges": ["₹500/strip", "₹1200/bottle", "₹2500/box 10 strips", "₹4000/lean pint"]
    },
    "synthetic_mephedrone": {
        "slang_terms": [
            "meow meow", "m-cat", "drone", "mephedrone", "2cb", "galaxy gas", "bath salts",
            "flakka", "naya maal", "chemical"
        ],
        "punjabi_slang": ["chemical", "naya powder"],
        "emojis": ["🐱", "🧪", "💥", "⚡"],
        "price_ranges": ["₹2000/g", "₹4500/2g", "₹9000/5g", "₹16000/10g"]
    }
}

LOCATIONS = [
    "Chandigarh", "Mohali", "Panchkula", "Tricity", "Ludhiana", "Amritsar", "Jalandhar",
    "Delhi NCR", "Noida", "Gurgaon", "Mumbai", "Pune", "Bangalore", "Goa (Anjuna/Calangute)",
    "Himachal (Kasol/Manali)", "Kodaikanal", "Hyderabad", "Kolkata", "Pan-India"
]

DELIVERY_METHODS = [
    "Same day dead drop", "Discreet vacuum sealed parcel", "Speedpost tracked",
    "DTDC stealth packing", "Hand-to-hand local drop", "Self pickup at spot",
    "Hidden stash coordinates provided after payment", "Courier with decoy packaging",
    "Rider hand delivery"
]

PAYMENT_METHODS = [
    "USDT (TRC-20 only)", "BTC / Bitcoin", "Monero (XMR) for 100% untraceable",
    "UPI via mule QR (expires in 10 mins)", "Cash on delivery (trusted buyers only)",
    "Escrow supported on darknet market", "Prepaid crypto only"
]

CONTACT_METHODS = [
    "DM on Telegram: @{handle}", "Contact on Signal: +91-XXXXXXXXXX",
    "Session ID: {session_id}", "Wickr: {wickr_id}", "ProtonMail: {mail}",
    "Darknet Market vendor: {vendor_name} (.onion)", "DM fast on Discord: {handle}#0420"
]

VENDOR_HANDLES = [
    "TricityPlug420", "IceKing_PB", "GreenMagicIndia", "KasolConnect", "ChdCokeSupply",
    "PureDesiMaal", "DarkCure99", "SnowDrop_DL", "PharmaCareDirect", "AcidVisions",
    "GhostVendorX", "HydraDesi", "SpeedyCourier420", "DopeMonk", "MalanaShaman"
]

LISTING_STRUCTURES_HINGLISH = [
    "{emojis} {substance_upper} AVAILABLE IN {location_upper} {emojis}\n"
    "• High purity tested batch {quality_tag}\n"
    "• Rates: {rates}\n"
    "• Delivery: {delivery}\n"
    "• Payment: {payment}\n"
    "{contact}\n"
    "Bhai maal fresh hai, koi faltu timepass mat karna. Genuine buyers DM karo. 🔒",

    "Fresh stock aa gaya hai bro! {emojis}\n"
    "Substance: {substance_name}\n"
    "Location: {location} & Pan India delivery available.\n"
    "Price: {rates}\n"
    "Packaging: 100% discreet packing with stealth guarantee.\n"
    "Pay via {payment}.\n"
    "{contact} 📲 Jaldi order place karo stock limited hai!",

    "{emojis} {location} LOCAL & PAN INDIA {emojis}\n"
    "Maal: {substance_name} ({slang_alias})\n"
    "Rate: {rates}\n"
    "Delivery mode: {delivery}\n"
    "Crypto (USDT/BTC) only. Dead drop available in {location} sectors.\n"
    "Ping me: {contact} ⚡",

    "New batch arrived 🔥 {substance_name} top notch quality 🧪\n"
    "Direct source from {origin}. Lab tested, no cut.\n"
    "Menu:\n- 1 unit: {rate_small}\n- Bulk: {rate_bulk}\n"
    "Drop available in {location}. Stealth courier pan India 📦\n"
    "{contact}\n"
    "Strictly escrow / {payment}."
]

BUYER_INQUIRY_HINGLISH = [
    "Bhai {location} mein {slang_alias} milega kya? Urgent chahiye aaj shaam ko.",
    "Bhaiya {substance_name} ka kya rate chal raha hai? 5g ka bulk discount milega?",
    "Bro {slang_alias} available hai {location} mein? Cash on delivery de doge ya sirf crypto?",
    "Maal fresh hai kya bhai? Last time wala {slang_alias} bohot weak tha, is bar pure chahiye.",
    "Kya scene hai bhai? {substance_name} ka packet ready hai kya? Location drop kahan karoge?",
    "Bhai {location} me score karna hai {slang_alias}. Any trusted plug active rn?",
    "Tricity / {location} me koi clean {substance_name} supply de sakta hai? DM me fast."
]

DEALER_BROADCAST_PUNJABI = [
    "Veerji {location} vich {substance_name} da fresh stock aa gya ae {emojis}. Rate bilkul genuine. "
    "Delivery hand to hand ya dead drop. Payment {payment}. DM karo @{handle}",

    "Chitta / {substance_name} available in {location}. Pure maal bina milawat da. "
    "1g da rate {rate_small}. Vadda order taan discount mil jauga. Jaldi rabta karo {contact}",

    "Maal ready ae bhai. {slang_alias} pure quality tested. Delivery {delivery}. "
    "No timepassers, rabta karo {contact} te."
]

DARKNET_FORUM_ENGLISH = [
    "[VENDOR LISTING] High Purity {substance_upper} - Domestic India to India {emojis}\n"
    "Purity: >92% Lab Tested (Gas Chromatography verified).\n"
    "Origin: Direct imported / Pure extraction.\n"
    "Pricing:\n- Sample: {rate_small}\n- Wholesale: {rate_bulk}\n"
    "Shipping: Vacuum sealed + Mylar moisture barrier + Decoy electronics box.\n"
    "Payment: Monero (XMR) / Bitcoin (BTC) Escrow supported on Archetyp/TorMarket.\n"
    "PGP Key attached below. Auto-finalize early only with 10+ reviews.",

    "Domestic India Postal Drop: {substance_name} ({slang_alias})\n"
    "Dispatch within 24h via Speedpost / Private Courier.\n"
    "Tracking provided via encrypted Note.\n"
    "Price: {rates}\n"
    "PGP Comms required. Contact: {contact}"
]

OBFUSCATED_PATTERNS = [
    "{emojis} {obf_substance} available in {location}. Ping @{handle} for menu. Fast discreet drop 📦🔒",
    "G@nj@ / Ch1tt@ / M.D.M.@ ready in stock. Rates: {rates}. Delivery {delivery}. Crypto only.",
    "Wh1te sn0w ❄️ and gre3n m44l 🌿 in {location}. DM for rates. No calls, telegram only: @{handle}",
    "K.u.s.h / H.a.z.e / M.o.l.l.y available. Drop in {location}. DM {contact}"
]

# ── Combinatorial Benign Slots & Templates ───────────────────────────────────

COMMERCE_ITEMS = ["cotton fabric", "denim jeans", "spices and dry fruits", "sarees", "plastic granules", "cement bags", "tea leaves", "spare parts", "electronic adapters", "cardboard boxes"]
COMMERCE_CITIES = ["Surat", "Ludhiana", "Ahmedabad", "Delhi", "Chandigarh", "Jaipur", "Mumbai", "Kanpur", "Kolkata", "Tirupur"]
COMMERCE_ACTIONS = ["ready for dispatch", "stock aa gaya hai", "ka packet dispatch kar diya", "ka bulk order ready hai", "ka sample bhej diya"]

FOOD_DRINKS = ["Coke 2L bottle", "cold drinks", "Diet Coke can", "ice cream tub", "ice cubes", "thandai bottle", "fruit juice", "lemonade"]
FOOD_ACTIONS = ["fridge me rakh do", "market se le aana party ke liye", "swiggy se order kar do", "thanda karne ke liye daal do", "khareed ke le aao"]

PHARMA_GENERIC = ["Paracetamol 650mg", "Pantoprazole 40mg", "Cetirizine 10mg", "Vitamin C chewable", "Amoxicillin 500mg", "Eye drops", "Antacid gel", "Cough lozenges", "Digene syrup"]
PHARMA_DOCTOR = ["Dr. Sharma", "Dr. Verma", "Max Hospital clinic", "Fortis OPD", "Apollo Pharmacy", "local clinic doctor"]

CHAT_SUBJECTS = ["project presentation", "machine learning assignment", "semester exam", "cricket match", "football tournament", "weekend movie plan", "flight booking", "hostel rent", "gym workout schedule"]
CHAT_FRIENDS = ["Bhai", "Bro", "Rahul", "Aman", "Rohan", "Simran", "Vikas", "Sir", "Team"]

def generate_negative_sample() -> Dict[str, Any]:
    """Generates a highly diverse benign negative / hard negative sample."""
    neg_type = random.choice(["hard_commerce", "hard_food_colloquial", "hard_pharma_legit", "general_chat", "news_weather"])
    platform = random.choice(["telegram", "discord", "whatsapp", "sms", "general_web"])

    if neg_type == "hard_commerce":
        city = random.choice(COMMERCE_CITIES)
        item = random.choice(COMMERCE_ITEMS)
        action = random.choice(COMMERCE_ACTIONS)
        qty = random.choice(["500 pieces", "10 bori", "20 packets", "100kg", "5 boxes", "wholesale lot"])
        price = random.choice(["₹45/meter", "₹120/piece", "₹450/box", "₹1200/lot", "rate negotiable"])
        
        templates = [
            f"Wholesale Market {city}: {item.capitalize()} {action}. Quantity: {qty}. Rate: {price}. Transport all India bilti ready.",
            f"Bhaiya {city} factory se {item} ka maal dispatch ho gaya hai. Tracking bilti number WhatsApp pe share kar diya hai.",
            f"Urgent requirement: Need {qty} of {item} in {city}. Rate quote karo per unit. Payment immediate RTGS/NEFT.",
            f"Fresh stock arrived: {item.capitalize()} ({qty}) available at {city} godown. Pure export quality fabric/goods."
        ]
        text = random.choice(templates)
        category = "hard_negative_commerce"
        language = "hinglish"

    elif neg_type == "hard_food_colloquial":
        item = random.choice(FOOD_DRINKS)
        action = random.choice(FOOD_ACTIONS)
        place = random.choice(["Sector 17", "hostel room", "office pantry", "home", "party venue", "cafe"])
        templates = [
            f"Bhai sham ko {place} pe milte hain, aate waqt 2 {item} {action}.",
            f"Garmi bohot jyada hai, fridge me {item} check karo aur thanda paani bana lo.",
            f"Holi celebration and party menu: Sweets, snacks, {item} and dinner buffet organized at {place}.",
            f"Bhai order summary: Pizza, burger aur 2 {item} place kar diya hai Zomato pe."
        ]
        text = random.choice(templates)
        category = "hard_negative_colloquial"
        language = "hinglish"

    elif neg_type == "hard_pharma_legit":
        med = random.choice(PHARMA_GENERIC)
        doc = random.choice(PHARMA_DOCTOR)
        templates = [
            f"{doc} prescription note: Take 1 tablet of {med} twice daily after meals for 5 days. Drink plenty of water.",
            f"Order Confirmed - {doc}: Your medicine order containing {med} is out for delivery. OTP for delivery is {random.randint(1000, 9999)}.",
            f"Is it necessary to have a prescription for purchasing {med} from the local chemist shop in Chandigarh?",
            f"Health Advice: Please do not self-medicate with {med}. Consult {doc} if symptoms persist beyond 48 hours."
        ]
        text = random.choice(templates)
        category = "hard_negative_pharma"
        language = "english"

    elif neg_type == "news_weather":
        loc = random.choice(LOCATIONS)
        temp = random.randint(18, 42)
        templates = [
            f"{loc} Weather Alert: Temperature recorded at {temp}°C with clear skies and moderate humidity.",
            f"Traffic advisory for {loc}: Road maintenance ongoing near main market circle. Commuters advised to take alternate route.",
            f"IPL Screening tonight at {loc} sports arena. Free entry before 7 PM for college students."
        ]
        text = random.choice(templates)
        category = "benign_news_weather"
        language = "english"

    else:
        friend = random.choice(CHAT_FRIENDS)
        topic = random.choice(CHAT_SUBJECTS)
        time_slot = random.choice(["10:00 AM", "3:30 PM", "kal subah", "aaj sham ko", "weekend pe"])
        templates = [
            f"{friend}, {topic} ka final update kab tak ready hoga? Meeting {time_slot} scheduled hai.",
            f"Hey {friend}, did you submit the {topic} on the portal? Please send me the reference link.",
            f"{friend} sun, {time_slot} chalte hain chai aur snacks ke liye, fresh ho jayenge.",
            f"Please review the attached pull request for {topic} before {time_slot} deployment."
        ]
        text = random.choice(templates)
        category = "benign_general"
        language = random.choice(["hinglish", "english"])

    sample_id = hashlib.md5(text.encode()).hexdigest()[:12]

    return {
        "id": f"trace_neg_{sample_id}",
        "text": text.strip(),
        "label": 0,
        "category": category,
        "substances": [],
        "platform": platform,
        "language": language,
        "risk_level": "SAFE",
        "is_obfuscated": False,
        "location": "None",
        "sample_type": "benign"
    }

LEET_REPLACEMENTS = {
    'a': ['@', '4', 'a'],
    'e': ['3', 'e'],
    'i': ['1', '!', 'i'],
    'o': ['0', 'o'],
    's': ['$', '5', 's'],
    't': ['7', 't']
}

def obfuscate_word(word: str) -> str:
    if random.random() < 0.5:
        return ".".join(list(word))
    else:
        out = []
        for ch in word.lower():
            if ch in LEET_REPLACEMENTS and random.random() < 0.6:
                out.append(random.choice(LEET_REPLACEMENTS[ch]))
            else:
                out.append(ch)
        return "".join(out)

def generate_positive_sample() -> Dict[str, Any]:
    substance_cat = random.choice(list(SUBSTANCE_TEMPLATES.keys()))
    sub_data = SUBSTANCE_TEMPLATES[substance_cat]

    slang_alias = random.choice(sub_data["slang_terms"])
    punjabi_alias = random.choice(sub_data.get("punjabi_slang", sub_data["slang_terms"]))
    emojis = "".join(random.sample(sub_data["emojis"], k=min(len(sub_data["emojis"]), random.randint(1, 3))))
    location = random.choice(LOCATIONS)
    delivery = random.choice(DELIVERY_METHODS)
    payment = random.choice(PAYMENT_METHODS)
    handle = random.choice(VENDOR_HANDLES)
    session_id = hashlib.sha256(str(random.random()).encode()).hexdigest()[:16]
    wickr_id = f"wckr_{handle.lower()}"
    mail = f"{handle.lower()}@proton.me"

    contact_tmpl = random.choice(CONTACT_METHODS)
    contact = contact_tmpl.format(
        handle=handle, session_id=session_id, wickr_id=wickr_id, mail=mail, vendor_name=handle
    )

    rates = random.choice(sub_data["price_ranges"])
    rate_small = rates.split(",")[0] if "," in rates else rates
    rate_bulk = "Bulk 10x available at 30% discount on escrow"

    archetypes = ["hinglish_listing", "buyer_inquiry", "punjabi_broadcast", "darknet_forum", "obfuscated"]
    archetype = random.choice(archetypes)

    is_obfuscated = False
    language = "hinglish"

    if archetype == "hinglish_listing":
        tmpl = random.choice(LISTING_STRUCTURES_HINGLISH)
        text = tmpl.format(
            emojis=emojis,
            substance_upper=slang_alias.upper(),
            substance_name=slang_alias.capitalize(),
            slang_alias=slang_alias,
            location=location,
            location_upper=location.upper(),
            quality_tag=random.choice(["(AAA+ Grade)", "(Direct Import)", "(Uncut Purity 95%)", "(Lab Verified 🧪)"]),
            rates=rates,
            rate_small=rate_small,
            rate_bulk=rate_bulk,
            delivery=delivery,
            payment=payment,
            contact=contact,
            origin=random.choice(["Malana", "Amsterdam", "Colombia", "Kasol", "Golden Crescent", "Direct Factory"])
        )
        language = "hinglish"

    elif archetype == "buyer_inquiry":
        tmpl = random.choice(BUYER_INQUIRY_HINGLISH)
        text = tmpl.format(
            location=location,
            substance_name=slang_alias,
            slang_alias=slang_alias
        )
        language = "hinglish"

    elif archetype == "punjabi_broadcast":
        tmpl = random.choice(DEALER_BROADCAST_PUNJABI)
        text = tmpl.format(
            location=location,
            substance_name=punjabi_alias,
            slang_alias=punjabi_alias,
            emojis=emojis,
            rate_small=rate_small,
            delivery=delivery,
            payment=payment,
            contact=contact,
            handle=handle
        )
        language = "punjabi_romanized"

    elif archetype == "darknet_forum":
        tmpl = random.choice(DARKNET_FORUM_ENGLISH)
        text = tmpl.format(
            substance_upper=slang_alias.upper(),
            substance_name=slang_alias,
            slang_alias=slang_alias,
            emojis=emojis,
            rate_small=rate_small,
            rate_bulk=rate_bulk,
            rates=rates,
            contact=contact
        )
        language = "english"

    else:
        obf_sub = obfuscate_word(slang_alias)
        tmpl = random.choice(OBFUSCATED_PATTERNS)
        text = tmpl.format(
            emojis=emojis,
            obf_substance=obf_sub,
            location=location,
            handle=handle,
            rates=rates,
            delivery=delivery,
            contact=contact
        )
        is_obfuscated = True
        language = "hinglish"

    substances_present = [substance_cat]
    if random.random() < 0.25 and archetype in ["hinglish_listing", "darknet_forum"]:
        other_cat = random.choice([k for k in SUBSTANCE_TEMPLATES.keys() if k != substance_cat])
        other_term = random.choice(SUBSTANCE_TEMPLATES[other_cat]["slang_terms"])
        text += f"\nAlso in stock: {other_term.capitalize()} ({random.choice(SUBSTANCE_TEMPLATES[other_cat]['price_ranges'])})"
        substances_present.append(other_cat)

    platform = random.choice(["telegram", "telegram", "discord", "darknet_market", "session_forum"])
    risk_level = "CRITICAL" if any(c in substance_cat for c in ["cocaine", "heroin", "methamphetamine", "synthetic"]) else "HIGH"
    sample_id = hashlib.md5(text.encode()).hexdigest()[:12]

    return {
        "id": f"trace_pos_{sample_id}",
        "text": text.strip(),
        "label": 1,
        "category": substance_cat if len(substances_present) == 1 else "multi_substance_menu",
        "substances": substances_present,
        "platform": platform,
        "language": language,
        "risk_level": risk_level,
        "is_obfuscated": is_obfuscated,
        "location": location,
        "sample_type": "illicit_marketing"
    }



def generate_dataset(total_samples: int = 2000, positive_ratio: float = 0.5, seed: int = 42) -> List[Dict[str, Any]]:
    random.seed(seed)
    num_pos = int(total_samples * positive_ratio)
    num_neg = total_samples - num_pos

    dataset = []
    seen_texts = set()

    pos_count = 0
    attempts = 0
    while pos_count < num_pos and attempts < num_pos * 4:
        sample = generate_positive_sample()
        if sample["text"] not in seen_texts:
            seen_texts.add(sample["text"])
            dataset.append(sample)
            pos_count += 1
        attempts += 1

    neg_count = 0
    attempts = 0
    while neg_count < num_neg and attempts < num_neg * 4:
        sample = generate_negative_sample()
        if sample["text"] not in seen_texts:
            seen_texts.add(sample["text"])
            dataset.append(sample)
            neg_count += 1
        attempts += 1

    random.shuffle(dataset)
    return dataset

def export_to_files(dataset: List[Dict[str, Any]], output_dir: str, base_filename: str = "synthetic_drug_slang_dataset"):
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, f"{base_filename}.csv")
    json_path = os.path.join(output_dir, f"{base_filename}.json")
    jsonl_path = os.path.join(output_dir, f"{base_filename}.jsonl")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    import csv
    fieldnames = ["id", "text", "label", "category", "substances", "platform", "language", "risk_level", "is_obfuscated", "location", "sample_type"]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in dataset:
            row = item.copy()
            row["substances"] = "|".join(item["substances"])
            writer.writerow(row)

    print(f"\n[SUCCESS] Dataset generated successfully ({len(dataset)} samples):")
    print(f"  • CSV:   {csv_path}")
    print(f"  • JSON:  {json_path}")
    print(f"  • JSONL: {jsonl_path}")

    pos_count = sum(1 for d in dataset if d["label"] == 1)
    neg_count = sum(1 for d in dataset if d["label"] == 0)
    print("\n[SUMMARY STATS]")
    print(f"  • Total Samples:   {len(dataset)}")
    print(f"  • Illicit (Pos):   {pos_count} ({pos_count/len(dataset)*100:.1f}%)")
    print(f"  • Benign (Neg):    {neg_count} ({neg_count/len(dataset)*100:.1f}%)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for Indian Darknet & Encrypted Platform Drug Intelligence.")
    parser.add_argument("--samples", type=int, default=2000, help="Total number of samples to generate (default: 2000)")
    parser.add_argument("--pos-ratio", type=float, default=0.5, help="Ratio of illicit positive samples (default: 0.5)")
    parser.add_argument("--output-dir", type=str, default=os.path.join(BASE_DIR, "data"), help="Directory to save generated files")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()

    print(f"[*] Generating {args.samples} synthetic samples (pos_ratio={args.pos_ratio}, seed={args.seed})...")
    data = generate_dataset(total_samples=args.samples, positive_ratio=args.pos_ratio, seed=args.seed)
    export_to_files(data, output_dir=args.output_dir)
