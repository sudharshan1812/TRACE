"""
TRACE Data Generator — Synthetic Drug Intelligence Data for Demo
Generates realistic Indian-context Telegram + darknet marketplace listings,
vendor profiles, wallet activity, and alerts for hackathon demonstration.
"""
import random
import hashlib
import datetime
import json
from typing import List, Dict

# ── Synthetic Templates ──────────────────────────────────────────────────────

TELEGRAM_CHANNELS = [
    {"name": "Chd deals 🔌", "type": "drug_market"},
    {"name": "Punjab Supply 📦", "type": "drug_market"},
    {"name": "High Quality Stock ❄️", "type": "drug_market"},
    {"name": "Mohan Market 🌿", "type": "drug_market"},
    {"name": "North India Supply ⚡", "type": "drug_market"},
    {"name": "Sector 17 Connect 🔥", "type": "drug_market"},
    {"name": "Chandigarh Plug 💎", "type": "drug_market"},
    {"name": "Tricity Underground", "type": "drug_market"},
    {"name": "PB Drug Store 📸", "type": "drug_market"},
    {"name": "White Market Premium ❄️", "type": "drug_market"},
    {"name": "Stock Available 📦", "type": "drug_market"},
    {"name": "Desi Maal 🌿", "type": "drug_market"},
    {"name": "Legal News Channel", "type": "news"},
    {"name": "Punjab Cricket", "type": "sports"},
]

TELEGRAM_LISTINGS = [
    # High confidence drug listings (Hinglish/Punjabi/English)
    {"text": "❄️❄️❄️ Premium White Available\n1g = ₹2500\n5g = ₹11000\n10g = ₹20000\nDM karo for bulk price\nPan India delivery\n📦 Discreet packaging\nCrypto accepted (USDT)", "source": "telegram", "expected_score": 0.95},
    {"text": "🌿🌿 Good Quality Green Stock\nChandigarh local pickup available\n1g = ₹800 | 5g = ₹3500\nWhatsApp pe contact karo\nTested and pure 🧪", "source": "telegram", "expected_score": 0.88},
    {"text": "💊💊 Party pills available\nMDMA / Ecstasy\n200mg strength\nPrice: ₹1500 per piece\nMinimum order 5 pieces\nEscrow available 🔒", "source": "telegram", "expected_score": 0.92},
    {"text": "🧊 Crystal Meth Available\nHigh quality product\nChandigarh, Mohali, Panchkula\nDM for price 💰\nSame day delivery available 🚚", "source": "telegram", "expected_score": 0.96},
    {"text": "Bhai maal available hai stock mein\nGanja charas sab milega\nRate negotiable hai\nChandigarh local\nDM karo jaldi 📱", "source": "telegram", "expected_score": 0.82},
    {"text": "🍫🍫 Brown MDMA\n250mg premium press\nGet 5 get 1 free offer\nTested at lab 🧪\nDelivery available\nUSDT accepted", "source": "telegram", "expected_score": 0.90},
    {"text": "Afeem ka paani mil rha hai\nPunjab se stock aaya hai\nFresh supply ⚡\nRate fixed hai\nPudde wale contact karein", "source": "telegram", "expected_score": 0.78},
    {"text": "Dawaai available 💊\nCodeine syrup\nTramadol 100mg\nXanax bars 2mg\nCOD available in tricity\nPrepaid pan India", "source": "telegram", "expected_score": 0.75},
    {"text": "❄️❄️ Blotter Acid available\nLSD tabs 200mcg\nQuantity available\nDM for rate\nDiscreet shipping 🤫\nCrypto only", "source": "telegram", "expected_score": 0.88},
    {"text": "Premium Cali Packs 🌿🔥\nUSA imported strains\nKush / Haze / OG\nRate: ₹2000/g\nBulk orders welcome\nTested product 🧪", "source": "telegram", "expected_score": 0.85},
    {"text": "Plug available in tricity 🔌\nAll types of stock\nDM for menu 📱\nSame day delivery\nDiscreet packaging guaranteed 🔒", "source": "telegram", "expected_score": 0.80},
    {"text": "Ice crystal available 🧊\nHigh purity product\n1g = ₹3000\n5g = ₹13500\nChandigarh Mohali delivery\nWhatsApp: DM karo", "source": "telegram", "expected_score": 0.93},
    {"text": "Brown sugar fresh stock 💰\nNew batch arrived\nQuality tested\nContact for rate\nDelhi Punjab both available\nCrypto only 📱", "source": "telegram", "expected_score": 0.87},
    {"text": "Xanax bars and percs 💊\n2mg Alprazolam\n10mg Oxycodone\nBulk rate available\nCOD Chandigarh\nRest Punjab prepaid", "source": "telegram", "expected_score": 0.72},
    {"text": "Goli available 💊\nParty pills\nParty maal\nDM karo rate ke liye\nChandigarh local only\nMinimum order 10 pieces", "source": "telegram", "expected_score": 0.83},
    # Lower confidence / borderline
    {"text": "Check our channel for latest stock updates\nFresh supply arriving daily\nDM for inquiries 📱\nPremium quality guaranteed", "source": "telegram", "expected_score": 0.45},
    {"text": "Price list updated ✅\nContact for rates\nBulk orders get discount\nPan India shipping\nPayment: Prepaid only", "source": "telegram", "expected_score": 0.38},
    # Clean / non-drug
    {"text": "Chandigarh weather update: Temperature 32°C, humidity 65%. Stay hydrated everyone! 💧", "source": "telegram", "expected_score": 0.05},
    {"text": "Punjab Kings vs MI match tonight at 7:30 PM. Who's watching? 🏏", "source": "telegram", "expected_score": 0.02},
    {"text": "Sector 17 market is closed tomorrow for maintenance. Plan accordingly.", "source": "telegram", "expected_score": 0.03},
]

DARKNET_LISTINGS = [
    {"text": "Cocaine - Colombian Premium\n5g minimum order\nShips worldwide in vacuum-sealed packs\nPayment: BTC only\nEscrow supported\nVendor: IceKing420 | 98% positive", "source": "darknet", "expected_score": 0.94},
    {"text": "MDMA Crystals - Dutch Origin\n10g available\nClean product, no cut\nSame day shipping\nPGP encrypted comms\nVendor: PartyMaster", "source": "darknet", "expected_score": 0.91},
    {"text": "Heroin #4 - Southeast Asian\nDiscrete packaging\n100% stealth shipping\nBTC accepted\nDead drop available\nVendor: BrownSugar_king", "source": "darknet", "expected_score": 0.93},
    {"text": "LSD Blotter - 150mcg per tab\nSheet of 25 available\nLab tested\nStealth first class shipping\nVendor: AcidDreams_420", "source": "darknet", "expected_score": 0.89},
    {"text": "Amphetamine Sulfate - EU Source\n100g minimum\nPowder form\nEscrow only\nVendor: SpeedDemon", "source": "darknet", "expected_score": 0.86},
]

VENDOR_NAMES = [
    ("IceKing420", "telegram", "Chandigarh"),
    ("PartyMaster", "darknet", "Punjab"),
    ("BrownSugar_king", "telegram", "Delhi"),
    ("AcidDreams_420", "darknet", "Mumbai"),
    ("ChdPlug_One", "telegram", "Chandigarh"),
    ("PBWhiteSupply", "telegram", "Punjab"),
    ("TricityMarket", "telegram", "Chandigarh"),
    ("Mohan_bhai420", "telegram", "Mohali"),
    ("PremiumStock_Punjab", "telegram", "Punjab"),
    ("CrystalChd", "telegram", "Chandigarh"),
    ("SpeedDemon", "darknet", "International"),
    ("DarkVendor_X", "darknet", "International"),
]

BTC_ADDRESSES = [
    "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",
    "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
    "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
    "3Kzh9qAqVWQhEsfQz7zEQL1EuSx5tyNLNS",
    "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
    "1CounterpartyXXXXXXXXXXXXXXXUWLpVr",
    "3FHNBLobJnbCTFTVakh5TXmEneyf5PT61B",
    "bc1q42lja79elem0anu8q860p50k2wztkc8e4z4auk",
    "1JCe8z4jJVNXSjohjM4i9HP7KMBNYpc7gP",
    "3LCGsSmfr24demGvriN4e3ft8wEcDuHFoK",
    "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3c",
    "1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ",
    "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
    "bc1qkl53aukd757fw2v2dg220j7r9a6pj7tj9qs0w5",
]

WALLET_RISK_FLAGS = ["known_exchange", "mixer_interaction", "high_volume",
                     "structuring_pattern", "darknet_linked", "new_wallet"]


def generate_demo_data():
    """Generate all synthetic data for the TRACE demo."""
    from . import database as db

    print("  [DATA] Generating vendor profiles...")
    vendor_ids = []
    for name, platform, region in VENDOR_NAMES:
        risk = random.uniform(0.3, 0.98)
        total_listings = random.randint(15, 200)
        active_days = random.randint(7, 180)
        vid = db.insert_vendor({
            "name": name,
            "handle": f"@{name.lower()}",
            "platform": platform,
            "bio": f"{region} based vendor. Active on {platform}.",
            "risk_score": round(risk, 3),
            "total_listings": total_listings,
            "active_days": active_days,
            "status": random.choice(["active", "active", "active", "suspended"])
        })
        vendor_ids.append(vid)

    print("  [DATA] Generating listings...")
    listing_templates = TELEGRAM_LISTINGS + DARKNET_LISTINGS
    for i in range(120):
        template = random.choice(listing_templates)
        source = template["source"]
        channel = random.choice(TELEGRAM_CHANNELS) if source == "telegram" else {"name": "Onion Market"}

        # Add random variation
        price = random.choice([800, 1500, 2000, 2500, 3000, 5000, 8000, 12000, 20000])
        vendor_id = random.choice(vendor_ids)
        days_ago = random.randint(0, 6)
        hours_ago = random.randint(0, 23)
        detected_at = (datetime.datetime.now() - datetime.timedelta(days=days_ago, hours=hours_ago)).isoformat()

        # Compute real analysis score
        from .slang_detector import analyze_text
        analysis = analyze_text(template["text"])

        img_hash = hashlib.md5(f"img_{i}_{vendor_id}".encode()).hexdigest() if random.random() > 0.4 else None

        db.insert_listing({
            "source": source,
            "source_id": f"{'TG' if source == 'telegram' else 'DN'}-{1000+i}",
            "channel_name": channel.get("name", ""),
            "text": template["text"],
            "image_url": f"https://placeholder.trace/img/{i}.jpg" if img_hash else None,
            "image_hash": img_hash,
            "price": price,
            "currency": "INR" if source == "telegram" else "BTC",
            "vendor_id": vendor_id,
            "slang_score": analysis.get("ml_score", analysis.get("lexicon_score", 0)),
            "emoji_score": analysis["emoji_score"],
            "combined_score": analysis["combined_score"],
            "detected_substances": analysis["detected_substances"],
            "detected_emoji": [e["emoji"] for e in analysis["detected_emoji"]],
            "detected_locations": analysis["detected_locations"],
            "detected_quantities": analysis["detected_quantities"],
            "is_drug": 1 if analysis["combined_score"] > 0.4 else 0
        })

    print("  [DATA] Generating wallet activity...")
    wallet_map = {}
    for i, addr in enumerate(BTC_ADDRESSES[:len(vendor_ids)]):
        vid = vendor_ids[i] if i < len(vendor_ids) else None
        balance = round(random.uniform(0.01, 5.0), 4)
        received = round(random.uniform(0.5, 20.0), 4)
        sent = round(received - balance + random.uniform(-0.5, 0.5), 4)
        flags = random.sample(WALLET_RISK_FLAGS, k=random.randint(1, 3))
        db.insert_wallet({
            "address": addr,
            "currency": random.choice(["BTC", "ETH", "USDT"]),
            "vendor_id": vid,
            "balance": balance,
            "total_received": received,
            "total_sent": max(sent, 0),
            "tx_count": random.randint(5, 50),
            "risk_flags": flags
        })
        wallet_map[addr] = vid

    print("  [DATA] Generating transactions...")
    wallet_addrs = list(wallet_map.keys())
    for i in range(80):
        from_addr = random.choice(wallet_addrs)
        to_addr = random.choice(wallet_addrs)
        while to_addr == from_addr:
            to_addr = random.choice(wallet_addrs)
        amount = round(random.uniform(0.001, 2.0), 4)
        days_ago = random.randint(0, 30)
        ts = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).isoformat()
        db.insert_transaction({
            "wallet_from": from_addr,
            "wallet_to": to_addr,
            "amount": amount,
            "currency": "BTC",
            "tx_hash": hashlib.sha256(f"tx_{i}_{from_addr}_{to_addr}".encode()).hexdigest()[:64],
            "timestamp": ts,
            "is_mixer": 1 if random.random() > 0.85 else 0,
            "mixer_risk": round(random.uniform(0, 0.9), 2) if random.random() > 0.8 else 0,
            "block_height": 800000 + i * 10
        })

    print("  [DATA] Generating alerts...")
    alert_templates = [
        {"type": "high_confidence_listing", "severity": "critical", "title": "HIGH-CONFIDENCE DRUG LISTING DETECTED",
         "message": "New listing with 95%+ drug confidence score detected in Telegram channel"},
        {"type": "new_vendor", "severity": "warning", "title": "NEW VENDOR ACTIVITY",
         "message": "New vendor account detected with multiple drug-related listings"},
        {"type": "cross_platform_link", "severity": "critical", "title": "CROSS-PLATFORM VENDOR LINK",
         "message": "Vendor identified on both Telegram and darknet marketplace — identity match 87%"},
        {"type": "price_anomaly", "severity": "warning", "title": "PRICE ANOMALY DETECTED",
         "message": "Sudden 40% price drop detected — possible law enforcement pressure indicator"},
        {"type": "new_slang", "severity": "info", "title": "NEW SLANG TERM DETECTED",
         "message": "Auto-detected potential new codeword appearing in drug context clusters"},
        {"type": "mixer_interaction", "severity": "critical", "title": "MIXER/TUMBLER INTERACTION",
         "message": "Tracked wallet interacted with known mixing service — fund trace obfuscation detected"},
        {"type": "bulk_listing", "severity": "warning", "title": "BULK SUPPLY LISTING",
         "message": "Large quantity listing detected (1kg+) — high-priority vendor activity"},
        {"type": "new_emoji_pattern", "severity": "info", "title": "NEW EMOJI PATTERN",
         "message": "Novel emoji combination detected as potential drug codeword pattern"},
        {"type": "vendor_migration", "severity": "critical", "title": "VENDOR MIGRATION ALERT",
         "message": "Previously suspended vendor detected reappearing on new channel with altered handle"},
        {"type": "darknet_listing", "severity": "warning", "title": "DARKNET MARKETPLACE LISTING",
         "message": "New drug listing scraped from darknet marketplace matching Chandigarh region keywords"},
    ]
    for i in range(35):
        template = random.choice(alert_templates)
        days_ago = random.randint(0, 5)
        hours_ago = random.randint(0, 23)
        created_at = (datetime.datetime.now() - datetime.timedelta(days=days_ago, hours=hours_ago)).isoformat()
        vid = random.choice(vendor_ids) if random.random() > 0.3 else None
        db.insert_alert({
            "type": template["type"],
            "severity": template["severity"],
            "title": template["title"],
            "message": f"{template['message']} — Vendor ID: {vid or 'N/A'}",
            "vendor_id": vid,
            "listing_id": random.randint(1, 50) if random.random() > 0.5 else None,
        })

    print("  [DATA] Generating evidence items...")
    for i in range(20):
        content = f"Evidence item {i}: Captured listing from Telegram channel"
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        db.insert_evidence({
            "listing_id": random.randint(1, 50),
            "vendor_id": random.choice(vendor_ids),
            "artifact_type": random.choice(["listing", "screenshot", "wallet_snapshot", "chat_export"]),
            "content_hash": content_hash,
            "notes": f"Auto-captured by TRACE — item #{i}"
        })

    print("  [DATA] Generating watchlist entries...")
    for keyword in ["cocaine", "crystal meth", " MDMA", "lsd", "heroin", "brown sugar", "charas", "ganja"]:
        db.insert_watchlist({"keyword": keyword, "match_type": "keyword", "severity": "warning"})

    print("  [DATA] Generating slang drift candidates...")
    drift_terms = ["newboi", "freshstock", "chalu", "satti", "molly2026", "premiumQ", "quickdeal"]
    for term in drift_terms:
        db.insert_slang_drift({
            "term": term,
            "context_snippet": f"... available {term} DM karo ...",
            "frequency": random.randint(3, 15),
            "status": "candidate"
        })

    stats = db.get_dashboard_stats()
    print(f"  [DATA] Done — {stats['total_listings']} listings, {stats['total_vendors']} vendors, "
          f"{stats['total_wallets']} wallets, {stats['total_alerts']} alerts, "
          f"{stats['total_evidence']} evidence items")
    return stats
