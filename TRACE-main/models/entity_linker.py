"""
TRACE Entity Linker — Cross-Platform Vendor Identity Resolution
Links the same vendor across Telegram, darknet marketplaces using:
  - Image perceptual hashing (pHash)
  - Text stylometry (TF-IDF + cosine similarity)
  - Handle/username matching
  - Writing style fingerprints
"""
import hashlib
import re
import math
from collections import Counter
from typing import Dict, List, Tuple, Optional


class EntityLinker:
    """Links vendor identities across platforms using multi-signal matching."""

    def __init__(self):
        self.vendor_profiles: Dict[int, Dict] = {}
        self.handle_index: Dict[str, int] = {}
        self.image_hash_index: Dict[str, List[int]] = {}
        self.style_vectors: Dict[int, Counter] = {}

    def register_vendor(self, vendor_id: int, data: Dict):
        """Register a vendor profile for linking."""
        self.vendor_profiles[vendor_id] = data

        # Index handles
        handle = data.get("handle", "").lower().strip("@").strip()
        if handle:
            self.handle_index[handle] = vendor_id
            # Also index stripped variants
            clean = re.sub(r'[^a-z0-9]', '', handle)
            if clean:
                self.handle_index[clean] = vendor_id

    def register_image_hash(self, vendor_id: int, image_hash: str):
        """Register an image hash for a vendor."""
        if vendor_id not in self.image_hash_index:
            self.image_hash_index[vendor_id] = []
        self.image_hash_index[vendor_id].append(image_hash)

    def compute_style_vector(self, vendor_id: int, texts: List[str]) -> Counter:
        """Compute a writing style fingerprint from vendor's text posts."""
        combined = " ".join(texts).lower()
        # Character bigrams (stylometry signature)
        bigrams = Counter()
        for i in range(len(combined) - 1):
            bg = combined[i:i+2]
            if bg.strip():
                bigrams[bg] += 1
        # Normalize
        total = sum(bigrams.values()) or 1
        for k in bigrams:
            bigrams[k] /= total
        self.style_vectors[vendor_id] = bigrams
        return bigrams

    def compute_similarity(self, vendor_a: int, vendor_b: int) -> Dict:
        """Compute multi-signal similarity between two vendors."""
        signals = {}
        total_score = 0.0
        link_types = []

        # Signal 1: Handle similarity
        handle_a = self.vendor_profiles.get(vendor_a, {}).get("handle", "").lower()
        handle_b = self.vendor_profiles.get(vendor_b, {}).get("handle", "").lower()
        if handle_a and handle_b:
            handle_sim = self._string_similarity(handle_a, handle_b)
            signals["handle"] = round(handle_sim, 3)
            if handle_sim > 0.6:
                total_score += handle_sim * 0.25
                link_types.append("handle_match")

        # Signal 2: Image hash similarity
        imgs_a = set(self.image_hash_index.get(vendor_a, []))
        imgs_b = set(self.image_hash_index.get(vendor_b, []))
        if imgs_a and imgs_b:
            intersection = imgs_a & imgs_b
            if intersection:
                signals["image_hash"] = 1.0
                total_score += 0.35
                link_types.append("image_match")
            else:
                # Hamming distance between hashes
                best_dist = float('inf')
                for ha in imgs_a:
                    for hb in imgs_b:
                        dist = self._hamming_distance(ha, hb)
                        best_dist = min(best_dist, dist)
                if best_dist < 10:
                    sim = 1.0 - (best_dist / 64.0)
                    signals["image_hash"] = round(sim, 3)
                    total_score += sim * 0.25
                    link_types.append("similar_image")

        # Signal 3: Writing style similarity (cosine of bigram vectors)
        vec_a = self.style_vectors.get(vendor_a)
        vec_b = self.style_vectors.get(vendor_b)
        if vec_a and vec_b:
            style_sim = self._cosine_similarity(vec_a, vec_b)
            signals["style"] = round(style_sim, 3)
            if style_sim > 0.7:
                total_score += style_sim * 0.25
                link_types.append("style_match")
            elif style_sim > 0.5:
                total_score += style_sim * 0.15
                link_types.append("similar_style")

        # Signal 4: Platform diversity bonus (cross-platform linking is more significant)
        plat_a = self.vendor_profiles.get(vendor_a, {}).get("platform", "")
        plat_b = self.vendor_profiles.get(vendor_b, {}).get("platform", "")
        if plat_a and plat_b and plat_a != plat_b:
            signals["cross_platform"] = True
            total_score += 0.1
            link_types.append("cross_platform")

        final_score = min(total_score, 1.0)
        return {
            "vendor_a": vendor_a,
            "vendor_b": vendor_b,
            "similarity_score": round(final_score, 3),
            "signals": signals,
            "link_types": link_types,
            "is_match": final_score > 0.5
        }

    def find_matches(self, vendor_id: int, threshold: float = 0.5) -> List[Dict]:
        """Find all vendors matching the given vendor above threshold."""
        matches = []
        for other_id in self.vendor_profiles:
            if other_id == vendor_id:
                continue
            result = self.compute_similarity(vendor_id, other_id)
            if result["similarity_score"] >= threshold:
                matches.append(result)
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches

    def get_graph_data(self) -> Dict:
        """Generate graph data for visualization (nodes + edges)."""
        nodes = []
        for vid, data in self.vendor_profiles.items():
            nodes.append({
                "id": vid,
                "label": data.get("name", f"Vendor {vid}"),
                "handle": data.get("handle", ""),
                "platform": data.get("platform", "unknown"),
                "risk_score": data.get("risk_score", 0),
                "group": data.get("platform", "unknown")
            })

        edges = []
        links = []
        # Compute all pairwise links
        vendor_ids = list(self.vendor_profiles.keys())
        for i in range(len(vendor_ids)):
            for j in range(i + 1, len(vendor_ids)):
                result = self.compute_similarity(vendor_ids[i], vendor_ids[j])
                if result["similarity_score"] > 0.3:
                    edges.append({
                        "from": vendor_ids[i],
                        "to": vendor_ids[j],
                        "value": result["similarity_score"],
                        "label": f"{result['similarity_score']:.0%}",
                        "link_types": result["link_types"]
                    })
                    links.append(result)

        return {"nodes": nodes, "edges": edges, "links": links}

    def _string_similarity(self, a: str, b: str) -> float:
        """Jaccard similarity on character trigrams."""
        if not a or not b:
            return 0.0
        trigrams_a = {a[i:i+3] for i in range(len(a) - 2)}
        trigrams_b = {b[i:i+3] for i in range(len(b) - 2)}
        if not trigrams_a or not trigrams_b:
            return 0.0
        intersection = trigrams_a & trigrams_b
        union = trigrams_a | trigrams_b
        return len(intersection) / len(union) if union else 0.0

    def _cosine_similarity(self, vec_a: Counter, vec_b: Counter) -> float:
        """Cosine similarity between two frequency vectors."""
        keys = set(vec_a.keys()) | set(vec_b.keys())
        dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in keys)
        mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values())) or 1
        mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values())) or 1
        return dot / (mag_a * mag_b)

    def _hamming_distance(self, hash_a: str, hash_b: str) -> int:
        """Compute Hamming distance between two hex hash strings."""
        if len(hash_a) != len(hash_b):
            return max(len(hash_a), len(hash_b)) * 4
        distance = 0
        for ca, cb in zip(hash_a, hash_b):
            xor = int(ca, 16) ^ int(cb, 16)
            distance += bin(xor).count('1')
        return distance


# Singleton
_linker = None


def get_entity_linker() -> EntityLinker:
    global _linker
    if _linker is None:
        _linker = EntityLinker()
    return _linker
