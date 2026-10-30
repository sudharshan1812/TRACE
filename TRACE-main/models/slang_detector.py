"""
TRACE Slang Detector v3 — Hybrid ML + Lexicon Engine
Combines a trained TF-IDF + LinearSVC ML classifier with the rule-based
lexicon engine. ML provides accuracy, lexicon provides explainability.
"""
import json
import re
import os
import pickle
import numpy as np
from scipy.sparse import hstack, csr_matrix
from typing import Dict, List, Tuple, Optional

LEXICON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "slang_lexicon.json")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "slang_model.pkl")


class MLClassifier:
    """ML-based drug text classifier using TF-IDF + LinearSVC."""

    def __init__(self):
        self.model_data = None
        self.loaded = False
        self._load()

    def _load(self):
        """Load trained model from disk."""
        if not os.path.exists(MODEL_PATH):
            print("[TRACE] ML model not found at", MODEL_PATH, "— falling back to lexicon only")
            return
        try:
            with open(MODEL_PATH, "rb") as f:
                self.model_data = pickle.load(f)
            self.loaded = True
            print(f"[TRACE] ML model loaded (v{self.model_data.get('model_version', '?')}, "
                  f"trained on {self.model_data.get('trained_on', '?')} samples, "
                  f"CV acc: {self.model_data.get('cv_accuracy', '?'):.1%})")
        except Exception as e:
            print(f"[TRACE] Failed to load ML model: {e}")

    def _preprocess(self, text: str) -> str:
        text = text.lower().strip()
        leet_map = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's'}
        decoded = ''.join(leet_map.get(c, c) for c in text)
        return re.sub(r'\s+', ' ', decoded)

    def _extract_features(self, text: str, sample: dict = None) -> list:
        """Extract handcrafted features for the ML model."""
        text_lower = text.lower()
        sample = sample or {}
        features = []
        emoji_count = len(re.findall(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', text))
        features.append(emoji_count)
        features.append(1 if '₹' in text else 0)
        features.append(1 if re.search(r'₹\d|price|rate|rs\.?', text_lower) else 0)
        features.append(1 if re.search(r'btc|bitcoin|usdt|crypto|monero|xmr|eth', text_lower) else 0)
        features.append(1 if re.search(r'dm|telegram|signal|session|wickr|proton|discord|@', text_lower) else 0)
        features.append(1 if sample.get('location') and sample['location'] != 'None' else 0)
        features.append(1 if sample.get('is_obfuscated', False) else 0)
        features.append(min(len(text) / 500.0, 1.0))
        features.append(1 if re.search(r'\bbhai\b|\bbhaiya\b|\bkaro\b|\bhai\b|\bvich\b|\bda\b|\bae\b', text_lower) else 0)
        features.append(1 if re.search(r'delivery|shipping|courier|dispatch|drop|dead drop|stealth', text_lower) else 0)
        features.append(1 if re.search(r'\d+\s*(g|kg|mg|strip|tablet|tab|piece|pudi|tola|packet)', text_lower) else 0)
        features.append(1 if 'pgp' in text_lower else 0)
        features.append(1 if re.search(r'vendor|\.onion|darknet|marketplace|escrow', text_lower) else 0)
        platform_map = {'telegram': 0, 'discord': 1, 'session_forum': 2, 'general_web': 3,
                        'sms': 4, 'whatsapp': 5, 'darknet_market': 6}
        features.append(platform_map.get(sample.get('platform', ''), 7) / 7.0)
        lang_map = {'hinglish': 0, 'english': 1, 'punjabi_romanized': 2}
        features.append(lang_map.get(sample.get('language', ''), 3) / 3.0)
        return features

    def predict_proba(self, text: str, sample: dict = None) -> float:
        """Return probability that text is drug-related (0.0 to 1.0)."""
        if not self.loaded:
            return 0.5  # unknown, let lexicon decide

        try:
            preprocessed = self._preprocess(text)
            word_tfidf = self.model_data['word_tfidf']
            char_tfidf = self.model_data['char_tfidf']
            clf = self.model_data['calibrated_clf']

            word_feat = word_tfidf.transform([preprocessed])
            char_feat = char_tfidf.transform([preprocessed])
            extra_feat = csr_matrix([self._extract_features(text, sample)])
            X = hstack([word_feat, char_feat, extra_feat])

            proba = clf.predict_proba(X)[0][1]  # P(drug)
            return float(proba)
        except Exception as e:
            print(f"[TRACE] ML prediction error: {e}")
            return 0.5


class SlangDetector:
    """Multi-lingual drug slang detector with contextual pattern scoring (lexicon layer)."""

    def __init__(self):
        with open(LEXICON_PATH, "r", encoding="utf-8") as f:
            self.lexicon = json.load(f)
        self._build_term_index()

    def _build_term_index(self):
        """Build flat index of all known terms -> (substance, language, weight)."""
        self.term_index: Dict[str, List[Tuple[str, str, float]]] = {}
        substances = self.lexicon.get("substances", {})
        lang_weights = {"hindi": 0.9, "punjabi": 0.95, "hinglish": 1.0, "english": 0.85}

        for substance, langs in substances.items():
            for lang, terms in langs.items():
                weight = lang_weights.get(lang, 0.7)
                for term in terms:
                    key = term.lower().strip()
                    if key not in self.term_index:
                        self.term_index[key] = []
                    self.term_index[key].append((substance, lang, weight))

        for lang, terms in self.lexicon.get("dealer_terms", {}).items():
            weight = lang_weights.get(lang, 0.7) * 0.5
            for term in terms:
                key = term.lower().strip()
                if key not in self.term_index:
                    self.term_index[key] = []
                self.term_index[key].append(("dealer", lang, weight))

        for lang, terms in self.lexicon.get("transaction_terms", {}).items():
            weight = lang_weights.get(lang, 0.7) * 0.4
            for term in terms:
                key = term.lower().strip()
                if key not in self.term_index:
                    self.term_index[key] = []
                self.term_index[key].append(("transaction", lang, weight))

        for region, terms in self.lexicon.get("location_terms", {}).items():
            for term in terms:
                key = term.lower().strip()
                if key not in self.term_index:
                    self.term_index[key] = []
                self.term_index[key].append(("location", "geo", 0.5))

        for size, terms in self.lexicon.get("quantity_terms", {}).items():
            for term in terms:
                key = term.lower().strip()
                if key not in self.term_index:
                    self.term_index[key] = []
                self.term_index[key].append(("quantity", "unit", 0.6))

        for phrase in self.lexicon.get("indicators", {}).get("high_confidence", []):
            key = phrase.lower().strip()
            if key not in self.term_index:
                self.term_index[key] = []
            self.term_index[key].append(("indicator_high", "indicator", 1.0))

        for phrase in self.lexicon.get("indicators", {}).get("medium_confidence", []):
            key = phrase.lower().strip()
            if key not in self.term_index:
                self.term_index[key] = []
            self.term_index[key].append(("indicator_med", "indicator", 0.7))

        self.contextual_phrases = {}
        for category, phrases in self.lexicon.get("contextual_phrases", {}).items():
            for phrase in phrases:
                key = phrase.lower().strip()
                self.contextual_phrases[key] = category

        self.darknet_patterns = [p.lower() for p in self.lexicon.get("darknet_patterns", [])]

    def analyze(self, text: str) -> Dict:
        """
        Lexicon-based analysis for explainability.
        Returns matched terms, substances, and a rule-based score.
        """
        text_lower = text.lower()
        tokens = self._tokenize(text_lower)

        detected_substances = set()
        detected_locations = set()
        detected_quantities = []
        matched_terms = []
        total_score = 0.0
        slang_hits = 0

        # ── Layer 1: Direct lexicon matching ──
        sorted_phrases = sorted(self.term_index.keys(), key=len, reverse=True)
        matched_spans = set()
        for phrase in sorted_phrases:
            if " " not in phrase:
                continue
            if phrase in matched_spans:
                continue
            if phrase in text_lower:
                for substance, lang, weight in self.term_index[phrase]:
                    if substance not in ("transaction", "location", "quantity",
                                         "indicator_high", "indicator_med"):
                        detected_substances.add(substance)
                    if substance == "location":
                        detected_locations.add(phrase)
                    matched_terms.append({"term": phrase, "substance": substance,
                                          "language": lang, "weight": weight})
                    total_score += weight
                    slang_hits += 1
                matched_spans.add(phrase)

        for token in tokens:
            if len(token) < 2:
                continue
            if token in self.term_index:
                for substance, lang, weight in self.term_index[token]:
                    if substance not in ("transaction", "location", "quantity",
                                         "indicator_high", "indicator_med"):
                        detected_substances.add(substance)
                    if substance == "location":
                        detected_locations.add(token)
                    if substance == "quantity":
                        detected_quantities.append(token)
                    matched_terms.append({"term": token, "substance": substance,
                                          "language": lang, "weight": weight})
                    total_score += weight
                    slang_hits += 1

        qty_patterns = re.findall(
            r'(\d+(?:\.\d+)?)\s*(g|gm|gram|grams|kg|kilo|tola|piece|tablet|tab|strip|pudiya|potli|mg|mcg)',
            text_lower
        )
        for amount, unit in qty_patterns:
            detected_quantities.append(f"{amount}{unit}")
            total_score += 0.3

        price_patterns = re.findall(
            r'(?:rs\.?|₹|inr|price|rate|paisa|rupay?|usd|btc|eth)\s*(\d+(?:,?\d+)*(?:\.\d+)?)',
            text_lower
        )
        has_price = len(price_patterns) > 0
        if has_price:
            total_score += 0.4

        # ── Layer 2: Contextual phrase matching ──
        context_score = 0.0
        context_categories_matched = set()
        for phrase, category in self.contextual_phrases.items():
            if phrase in text_lower:
                context_categories_matched.add(category)
                if category == "drug_slang_hindi":
                    context_score += 0.5
                elif category == "drug交易_context":
                    context_score += 0.45
                elif category == "drug_availability":
                    context_score += 0.35
                elif category == "drug_inquiry":
                    context_score += 0.3
                elif category == "dealer_terms":
                    context_score += 0.4
                else:
                    context_score += 0.25

        if len(context_categories_matched) >= 2:
            context_score = min(context_score * 1.3, 2.0)
        total_score += context_score

        # Phase 2c: Context word scoring (only fires when substance or strong signal present)
        # These words alone are too generic (stock, fresh, rate appear in legitimate commerce)
        # They only boost score when a drug substance or strong indicator is already matched
        has_strong_signal = len(detected_substances) > 0 or len(context_categories_matched) >= 1
        if has_strong_signal:
            context_words_strong = {
                "maal": 0.4, "plug": 0.35, "dealer": 0.3, "source": 0.2,
                "aaja": 0.2, "le ja": 0.2, "bhej": 0.2,
                "crypto": 0.2, "escrow": 0.2, "prepaid": 0.15, "cod": 0.15,
                "dead drop": 0.3, "stealth": 0.2, "discreet": 0.2,
                "jaldi": 0.15, "fatafat": 0.15,
            }
            context_word_score = 0.0
            for word, weight in context_words_strong.items():
                if word.strip() in text_lower:
                    context_word_score += weight
            total_score += context_word_score

        # ── Layer 3: Transaction + Darknet pattern boosters ──
        transaction_boost = 0.0
        tx_terms = ["dm", "dm karo", "price negotiable", "bulk", "delivery",
                    "prepaid", "cod", "crypto", "usdt", "btc", "wallet", "escrow",
                    "pgp", "stealth", "dead drop", "vacuum-sealed", "discrete",
                    "shipping", "vendor", "marketplace", "listing", "for sale"]
        for term in tx_terms:
            if term in text_lower:
                transaction_boost += 0.12
        total_score += transaction_boost

        darknet_boost = 0.0
        for indicator in self.darknet_patterns:
            if indicator in text_lower:
                darknet_boost += 0.2
        total_score += min(darknet_boost, 0.8)

        # Leetspeak detection + decoded substance matching
        leet_map = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's'}
        obfuscation_patterns = self.lexicon.get("leetspeak_obfuscation", {}).get("patterns", [])
        for pattern in obfuscation_patterns:
            if pattern.lower() in text_lower:
                total_score += 0.35
                # Also decode and check if it matches a known substance
                decoded = ''.join(leet_map.get(c, c) for c in pattern.lower())
                decoded_clean = re.sub(r'[^a-z]', '', decoded)
                if decoded_clean in self.term_index:
                    for substance, lang, weight in self.term_index[decoded_clean]:
                        if substance not in ("transaction", "location", "quantity",
                                             "indicator_high", "indicator_med"):
                            detected_substances.add(substance)
                        matched_terms.append({"term": f"{pattern}->{decoded_clean}", "substance": substance,
                                              "language": lang, "weight": weight})
                        total_score += weight
                # Also try fuzzy: check if any substance term starts with the decoded text
                for term_key in self.term_index:
                    if len(decoded_clean) >= 3 and term_key.startswith(decoded_clean[:4]):
                        for substance, lang, weight in self.term_index[term_key]:
                            if substance not in ("transaction", "location", "quantity",
                                                 "indicator_high", "indicator_med",
                                                 "dealer", "transaction"):
                                detected_substances.add(substance)
                                matched_terms.append({"term": f"{pattern}->{term_key}", "substance": substance,
                                                      "language": lang, "weight": weight})
                                total_score += weight
                                break
                        break

        # Slang drift detection
        drug_context_words = self._find_unknown_words_in_drug_context(tokens, matched_terms)

        # Lexicon score (rule-based)
        lexicon_score = min(total_score / 3.5, 1.0)

        # Benign context filter: if text matches known benign patterns, reduce score
        # unless a drug substance was actually detected
        benign_patterns = [
            r'weather alert',
            r'temperature recorded',
            r'wholesale market \w+:',
            r'factory se .* dispatch',
            r'bilti ready',
            r'rtgs/neft',
            r'required: need.*wholesale',
            r'required: need.*\d+ (bori|boxes|kg|pieces)',
            r'spares? parts? ka maal',
            r'cotton fabric',
            r'cotton granules',
            r'plastic granules',
            r'denim jeans',
            r'jeans.*available',
            r'sarees? .* dispatch',
            r'export quality',
            r'fabric/goods',
            r'fridge me .* check',
            r'swiggy se order',
            r'self-medicate',
            r'prescription for purchasing',
            r'chemist shop',
            r'medicine order containing',
            r'order confirmed',
            r'out for delivery.*otp',
            r'health advice',
            r'consult.*hospital',
            r'symptoms persist',
            r'ipl screening',
            r'college students',
            r'cricket match',
            r'pull request',
            r'deployment',
            r'ice cream',
            r'ice cubes',
            r'diet coke',
            r'coke 2l',
            r'coke.*bottle',
            r'lemonade',
            r'sports arena',
            r'free entry',
            r'traffic advisory',
            r'road maintenance',
            r'commuters advised',
        ]
        is_benign = False
        for bp in benign_patterns:
            if re.search(bp, text_lower):
                is_benign = True
                lexicon_score *= 0.3
                detected_substances.clear()  # Clear false substance detections
                break
        # Weather/location false positives: weather alerts mention drug-area names
        if not is_benign:
            weather_location_patterns = [
                r'weather alert.*temperature',
                r'temperature recorded at.*clear skies',
                r'ipl screening',
                r'sports arena',
            ]
            for wp in weather_location_patterns:
                if re.search(wp, text_lower):
                    is_benign = True
                    lexicon_score *= 0.3
                    detected_substances.clear()
                    break

        return {
            "detected_substances": sorted(detected_substances),
            "detected_locations": sorted(detected_locations),
            "detected_quantities": detected_quantities,
            "matched_terms": matched_terms,
            "has_price_pattern": has_price,
            "transaction_language_boost": round(transaction_boost, 3),
            "slang_drift_candidates": drug_context_words,
            "lexicon_score": round(lexicon_score, 3),
        }

    def _fuzzy_leet_match(self, word: str, leet_term: str) -> bool:
        leet_map = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's'}
        normalized = ''.join(leet_map.get(c, c) for c in word)
        clean_leet = re.sub(r'[^a-z]', '', leet_term.lower())
        return normalized == clean_leet or clean_leet.startswith(normalized) or normalized.startswith(clean_leet[:3])

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r'[\w\u0900-\u097F]+', text.lower())
        bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
        trigrams = [f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}" for i in range(len(tokens) - 2)]
        return tokens + bigrams + trigrams

    def _find_unknown_words_in_drug_context(self, tokens: List[str],
                                             matched_terms: List[Dict]) -> List[str]:
        known = {m["term"] for m in matched_terms}
        candidates = []
        drug_context_positions = set()
        for i, token in enumerate(tokens):
            if token in known:
                drug_context_positions.add(i)
        for i, token in enumerate(tokens):
            if token in known or len(token) < 3:
                continue
            for pos in drug_context_positions:
                if abs(i - pos) <= 3:
                    candidates.append(token)
                    break
        seen = set()
        unique = [c for c in candidates if c not in seen and not seen.add(c)]
        return unique[:5]

    def _confidence_label(self, score: float) -> str:
        if score > 0.8:
            return "CRITICAL"
        elif score > 0.6:
            return "HIGH"
        elif score > 0.4:
            return "MEDIUM"
        elif score > 0.2:
            return "LOW"
        return "CLEAN"


class EmojiClassifier:
    """Maps emojis to drug substances with confidence scores."""

    def __init__(self):
        with open(LEXICON_PATH, "r", encoding="utf-8") as f:
            self.lexicon = json.load(f)
        self.emoji_map = self.lexicon.get("emoji_mappings", {})

    def classify(self, text: str) -> Dict:
        detected = []
        total_score = 0.0
        for emoji_char, info in self.emoji_map.items():
            count = text.count(emoji_char)
            if count > 0:
                entry = {
                    "emoji": emoji_char,
                    "substance": info["substance"],
                    "confidence": info["confidence"],
                    "count": count,
                    "contexts": info["contexts"]
                }
                detected.append(entry)
                total_score += info["confidence"] * min(count, 3)
        score = min(total_score / 2.0, 1.0) if detected else 0.0
        drug_emojis = [e for e in detected if e["substance"] not in ("dealer", "delivery",
                       "quality", "hot_new", "proof", "discreet", "contact", "price", "secure")]
        if len(drug_emojis) > 1:
            score = min(score + 0.2, 1.0)
        return {
            "detected_emoji": detected,
            "emoji_score": round(score, 3),
            "drug_emoji_count": len(drug_emojis),
            "total_emoji_count": len(detected),
            "has_drug_emoji": len(drug_emojis) > 0
        }


# ── Singleton management ──────────────────────────────────────────────────

_detector = None
_ml_clf = None
_emoji_clf = None
_lexicon_mtime = 0.0


def _check_lexicon_reload():
    global _detector, _emoji_clf, _lexicon_mtime
    try:
        current_mtime = os.path.getmtime(LEXICON_PATH)
        if current_mtime != _lexicon_mtime:
            _detector = None
            _emoji_clf = None
            _lexicon_mtime = current_mtime
    except OSError:
        pass


def get_detector() -> SlangDetector:
    global _detector
    _check_lexicon_reload()
    if _detector is None:
        _detector = SlangDetector()
    return _detector


def get_ml_classifier() -> MLClassifier:
    global _ml_clf
    if _ml_clf is None:
        _ml_clf = MLClassifier()
    return _ml_clf


def get_emoji_classifier() -> EmojiClassifier:
    global _emoji_clf
    _check_lexicon_reload()
    if _emoji_clf is None:
        _emoji_clf = EmojiClassifier()
    return _emoji_clf


def reset_detector():
    global _detector, _ml_clf, _emoji_clf
    _detector = None
    _ml_clf = None
    _emoji_clf = None


def analyze_text(text: str, sample: dict = None) -> Dict:
    """
    Hybrid ML + Lexicon analysis.
    ML provides the primary classification (accuracy).
    Lexicon provides explainability (which terms matched).
    """
    detector = get_detector()
    ml_clf = get_ml_classifier()
    emoji_clf = get_emoji_classifier()

    # ML layer — primary accuracy
    ml_score = ml_clf.predict_proba(text, sample)

    # Lexicon layer — explainability
    lexicon_result = detector.analyze(text)
    lexicon_score = lexicon_result["lexicon_score"]

    # Emoji layer
    emoji_result = emoji_clf.classify(text)

    # ── Hybrid score combination ──
    # Strategy: take the HIGHER of ML and lexicon scores, weighted by confidence.
    # ML excels at long structured texts; lexicon excels at short slang-heavy texts.
    has_substance_match = len(lexicon_result["detected_substances"]) > 0
    has_high_lexicon = lexicon_score >= 0.6
    has_dealer = any(m["substance"] == "dealer" for m in lexicon_result["matched_terms"])
    has_location = len(lexicon_result["detected_locations"]) > 0
    has_dealer_location = has_dealer and has_location

    if ml_clf.loaded:
        if has_substance_match and has_high_lexicon:
            # Lexicon found a drug substance with high confidence — trust it
            combined = max(ml_score, lexicon_score * 0.85)
        elif has_substance_match:
            # Lexicon found substance but lower confidence — blend heavily toward lexicon
            combined = max(ml_score * 0.4 + lexicon_score * 0.6, lexicon_score * 0.7)
        elif lexicon_score >= 0.5:
            # High lexicon score but no specific substance — context is suspicious
            combined = max(ml_score * 0.3 + lexicon_score * 0.7, lexicon_score * 0.6)
        else:
            # No substance match, low lexicon — ML leads, lexicon supports
            combined = ml_score * 0.7 + lexicon_score * 0.3

        # Substance detected boost: if lexicon found a drug substance, ensure minimum score
        if has_substance_match and combined < 0.5:
            combined = max(combined, 0.5)

        # Dealer + Location boost: dealer term + location is a strong signal
        if has_dealer_location and combined < 0.5:
            combined = min(combined + 0.2, 1.0)

        # Emoji bonus
        if emoji_result["has_drug_emoji"] and combined > 0.2:
            combined = min(combined + emoji_result["emoji_score"] * 0.15, 1.0)
    else:
        # Fallback: pure lexicon + emoji
        has_emoji = emoji_result["has_drug_emoji"]
        if has_emoji:
            combined = min(lexicon_score * 0.55 + emoji_result["emoji_score"] * 0.45, 1.0)
        else:
            combined = lexicon_score
        if has_substance_match and has_emoji:
            combined = min(combined + 0.15, 1.0)

    combined = round(min(combined, 1.0), 3)
    is_drug = combined > 0.4

    # Confidence label based on combined score
    if combined > 0.8:
        confidence_label = "CRITICAL"
    elif combined > 0.6:
        confidence_label = "HIGH"
    elif combined > 0.4:
        confidence_label = "MEDIUM"
    elif combined > 0.2:
        confidence_label = "LOW"
    else:
        confidence_label = "CLEAN"

    return {
        "text": text,
        "combined_score": combined,
        "ml_score": round(ml_score, 3),
        "lexicon_score": lexicon_result["lexicon_score"],
        "emoji_score": emoji_result["emoji_score"],
        "detected_substances": lexicon_result["detected_substances"],
        "detected_locations": lexicon_result["detected_locations"],
        "detected_quantities": lexicon_result["detected_quantities"],
        "detected_emoji": emoji_result["detected_emoji"],
        "matched_terms": lexicon_result["matched_terms"],
        "has_price_pattern": lexicon_result["has_price_pattern"],
        "has_drug_emoji": emoji_result["has_drug_emoji"],
        "is_drug": is_drug,
        "confidence_label": confidence_label,
        "slang_drift_candidates": lexicon_result["slang_drift_candidates"]
    }
