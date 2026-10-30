"""
TRACE Slang Model Trainer
Trains a TF-IDF + LinearSVC classifier on the labeled synthetic drug slang dataset.
Saves trained model + vectorizer to models/slang_model.pkl
"""
import json
import os
import re
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "synthetic_drug_slang_dataset.json")
MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, "slang_model.pkl")


def preprocess_text(text: str) -> str:
    """Normalize text for ML: lowercase, decode leetspeak, normalize whitespace."""
    text = text.lower().strip()
    # Decode common leetspeak
    leet_map = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's'}
    decoded = ''
    for c in text:
        decoded += leet_map.get(c, c)
    text = decoded
    # Remove excess whitespace
    text = re.sub(r'\s+', ' ', text)
    return text


def extract_handcrafted_features(text: str, sample: dict) -> list:
    """Extract additional features beyond TF-IDF."""
    text_lower = text.lower()
    features = []
    # Emoji count
    emoji_count = len(re.findall(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', text))
    features.append(emoji_count)
    # Has ₹ symbol
    features.append(1 if '₹' in text else 0)
    # Has price pattern
    features.append(1 if re.search(r'₹\d|price|rate|rs\.?', text_lower) else 0)
    # Has crypto reference
    features.append(1 if re.search(r'btc|bitcoin|usdt|crypto|monero|xmr|eth', text_lower) else 0)
    # Has contact info
    features.append(1 if re.search(r'dm|telegram|signal|session|wickr|proton|discord|@', text_lower) else 0)
    # Has location
    features.append(1 if sample.get('location') and sample['location'] != 'None' else 0)
    # Is obfuscated
    features.append(1 if sample.get('is_obfuscated', False) else 0)
    # Text length
    features.append(min(len(text) / 500.0, 1.0))
    # Has Hindi/Hinglish markers
    features.append(1 if re.search(r'\bbhai\b|\bbhaiya\b|\bkaro\b|\bhai\b|\bvich\b|\bda\b|\bae\b', text_lower) else 0)
    # Has delivery/shipping terms
    features.append(1 if re.search(r'delivery|shipping|courier|dispatch|drop|dead drop|stealth', text_lower) else 0)
    # Has quantity terms
    features.append(1 if re.search(r'\d+\s*(g|kg|mg|strip|tablet|tab|piece|pudi|tola|packet)', text_lower) else 0)
    # Has PGP reference
    features.append(1 if 'pgp' in text_lower else 0)
    # Has darknet vendor reference
    features.append(1 if re.search(r'vendor|\.onion|darknet|marketplace|escrow', text_lower) else 0)
    # Platform encoding
    platform_map = {'telegram': 0, 'discord': 1, 'session_forum': 2, 'general_web': 3,
                    'sms': 4, 'whatsapp': 5, 'darknet_market': 6}
    features.append(platform_map.get(sample.get('platform', ''), 7) / 7.0)
    # Language encoding
    lang_map = {'hinglish': 0, 'english': 1, 'punjabi_romanized': 2}
    features.append(lang_map.get(sample.get('language', ''), 3) / 3.0)
    return features


def load_dataset():
    """Load and preprocess the labeled dataset."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    texts = []
    labels = []
    extra_features = []

    for sample in raw_data:
        text = preprocess_text(sample["text"])
        label = sample["label"]
        extra = extract_handcrafted_features(sample["text"], sample)

        texts.append(text)
        labels.append(label)
        extra_features.append(extra)

    return texts, np.array(labels), np.array(extra_features)


def train_model():
    """Train the classifier with TF-IDF + handcrafted features."""
    print("Loading dataset...")
    texts, labels, extra_features = load_dataset()
    print(f"  {len(texts)} samples ({sum(labels)} positive, {len(labels)-sum(labels)} negative)")

    # TF-IDF on text (char n-grams capture leetspeak + word n-grams for phrases)
    print("Building TF-IDF features...")
    word_tfidf = TfidfVectorizer(
        analyzer='word',
        ngram_range=(1, 3),
        max_features=15000,
        sublinear_tf=True,
        min_df=2,
        max_df=0.95
    )
    char_tfidf = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 5),
        max_features=10000,
        sublinear_tf=True,
        min_df=2,
        max_df=0.95
    )

    word_features = word_tfidf.fit_transform(texts)
    char_features = char_tfidf.fit_transform(texts)

    # Combine all features
    from scipy.sparse import hstack, csr_matrix
    extra_sparse = csr_matrix(extra_features)
    X = hstack([word_features, char_features, extra_sparse])
    y = labels

    print(f"  Feature matrix: {X.shape}")

    # Cross-validation
    print("Running 5-fold cross-validation...")
    base_svc = LinearSVC(C=1.0, max_iter=5000, class_weight='balanced')
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(base_svc, X, y, cv=cv, scoring='accuracy')
    print(f"  CV Accuracy: {scores.mean():.4f} (+/- {scores.std():.4f})")

    # Train final model with calibration for probability output
    print("Training final calibrated model...")
    svc = LinearSVC(C=1.0, max_iter=5000, class_weight='balanced')
    calibrated = CalibratedClassifierCV(svc, cv=3, method='sigmoid')
    calibrated.fit(X, y)

    # Full train accuracy
    train_preds = calibrated.predict(X)
    train_acc = np.mean(train_preds == y)
    print(f"  Full train accuracy: {train_acc:.4f}")

    # Classification report
    print("\nClassification Report:")
    print(classification_report(y, train_preds, target_names=['BENIGN', 'DRUG']))

    # Confusion matrix
    cm = confusion_matrix(y, train_preds)
    print("Confusion Matrix:")
    print(f"  TN={cm[0][0]} FP={cm[0][1]}")
    print(f"  FN={cm[1][0]} TP={cm[1][1]}")
    print(f"  False Positive Rate: {cm[0][1]/(cm[0][0]+cm[0][1])*100:.1f}%")
    print(f"  False Negative Rate: {cm[1][0]/(cm[1][0]+cm[1][1])*100:.1f}%")

    # Save everything
    print(f"\nSaving model to {MODEL_PATH}...")
    model_data = {
        'calibrated_clf': calibrated,
        'word_tfidf': word_tfidf,
        'char_tfidf': char_tfidf,
        'model_version': '2.0',
        'trained_on': len(texts),
        'cv_accuracy': float(scores.mean()),
        'train_accuracy': float(train_acc),
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_data, f)
    print("  Done!")

    return calibrated, word_tfidf, char_tfidf


if __name__ == "__main__":
    train_model()
