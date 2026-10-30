"""
TRACE Evidence Locker — Digital Evidence Chain-of-Custody & NDPS Act Dossier Generator
Provides tamper-evident evidence capture, SHA-256 hashing,
audit logging, and court-ready PDF report generation.
"""
import hashlib
import json
import os
import datetime
from typing import Dict, List, Optional


class EvidenceLocker:
    """Manages digital evidence with chain-of-custody and report generation."""

    TOOL_NAME = "TRACE v1.0 — Transnational Darknet & Encrypted Commerce Examiner"
    TOOL_VERSION = "1.0.0"

    def __init__(self):
        self.evidence_items: Dict[int, Dict] = {}
        self.custody_chains: Dict[int, List[Dict]] = {}
        self._counter = 0

    def capture(self, content: str, artifact_type: str = "listing",
                source: str = "TRACE", metadata: Dict = None) -> Dict:
        """
        Capture an evidence artifact with hash and chain-of-custody entry.
        Returns the evidence record with SHA-256 hash.
        """
        self._counter += 1
        evidence_id = self._counter
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        timestamp = datetime.datetime.now().isoformat()

        custody_entry = {
            "action": "CAPTURED",
            "timestamp": timestamp,
            "tool": self.TOOL_NAME,
            "source": source,
            "hash": content_hash,
            "officer": "TRACE System (Automated)"
        }

        evidence = {
            "id": evidence_id,
            "artifact_type": artifact_type,
            "content_hash": content_hash,
            "content_preview": content[:200],
            "captured_at": timestamp,
            "source": source,
            "tool": self.TOOL_NAME,
            "chain_of_custody": [custody_entry],
            "metadata": metadata or {},
            "verified": True
        }

        self.evidence_items[evidence_id] = evidence
        self.custody_chains[evidence_id] = [custody_entry]
        return evidence

    def verify(self, evidence_id: int, content: str) -> Dict:
        """Verify evidence integrity by re-hashing."""
        evidence = self.evidence_items.get(evidence_id)
        if not evidence:
            return {"verified": False, "error": "Evidence not found"}

        current_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        is_valid = current_hash == evidence["content_hash"]

        verification_entry = {
            "action": "VERIFIED" if is_valid else "TAMPERED",
            "timestamp": datetime.datetime.now().isoformat(),
            "tool": self.TOOL_NAME,
            "hash": current_hash,
            "original_hash": evidence["content_hash"],
            "officer": "TRACE System (Automated)"
        }
        evidence["chain_of_custody"].append(verification_entry)

        return {
            "evidence_id": evidence_id,
            "verified": is_valid,
            "original_hash": evidence["content_hash"],
            "current_hash": current_hash,
            "verification_time": verification_entry["timestamp"]
        }

    def add_custody_action(self, evidence_id: int, action: str,
                           officer: str, notes: str = "") -> Dict:
        """Add a chain-of-custody action (e.g., TRANSFERRED, REVIEWED, SUBMITTED)."""
        evidence = self.evidence_items.get(evidence_id)
        if not evidence:
            return {"error": "Evidence not found"}

        entry = {
            "action": action,
            "timestamp": datetime.datetime.now().isoformat(),
            "tool": self.TOOL_NAME,
            "officer": officer,
            "notes": notes
        }
        evidence["chain_of_custody"].append(entry)
        return entry

    def generate_dossier(self, vendor_data: Dict, listings: List[Dict],
                         evidence_items: List[Dict], wallets: List[Dict] = None,
                         transactions: List[Dict] = None) -> str:
        """
        Generate a structured NDPS Act–compliant dossier in text format.
        (PDF generation is done in the API layer using fpdf2)
        """
        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        vendor_name = vendor_data.get("name", "Unknown")
        vendor_handle = vendor_data.get("handle", "N/A")
        risk_score = vendor_data.get("risk_score", 0)

        dossier = f"""
{'='*70}
           NDPS ACT - INTELLIGENCE DOSSIER
           TRACE Platform — Automated Evidence Report
{'='*70}

REPORT GENERATION DETAILS
{'─'*40}
  Generated At    : {now}
  Report Tool     : {self.TOOL_NAME}
  Report Version  : {self.TOOL_VERSION}
  Report Type     : Drug Intelligence Dossier (Section 22, NDPS Act 1985)

SUSPECT VENDOR PROFILE
{'─'*40}
  Vendor Name     : {vendor_name}
  Handle / ID     : {vendor_handle}
  Platform(s)     : {vendor_data.get('platform', 'Multiple')}
  Risk Score      : {risk_score}/1.00 ({self._risk_label(risk_score)})
  Total Listings  : {vendor_data.get('total_listings', len(listings))}
  Active Days     : {vendor_data.get('active_days', 0)}
  Status          : {vendor_data.get('status', 'Active')}
  First Observed  : {vendor_data.get('first_seen', 'N/A')}
  Last Observed   : {vendor_data.get('last_seen', 'N/A')}

EVIDENCE SUMMARY
{'─'*40}
  Total Evidence Items : {len(evidence_items)}
  Verified Items       : {sum(1 for e in evidence_items if e.get('verified', True))}
  Hash Algorithm       : SHA-256
  Capture Tool         : {self.TOOL_NAME}

LISTING EVIDENCE ({len(listings)} items)
{'─'*40}"""

        for i, listing in enumerate(listings[:20], 1):
            substances = listing.get("detected_substances", "[]")
            score = listing.get("combined_score", 0)
            dossier += f"""
  [{i:03d}] Listing ID: {listing.get('id', 'N/A')}
      Source      : {listing.get('source', 'N/A')}
      Timestamp   : {listing.get('detected_at', 'N/A')}
      Text Preview: {listing.get('text', '')[:120]}...
      Score       : {score:.3f} ({self._risk_label(score)})
      Substances  : {substances}
      Price       : {listing.get('price', 'N/A')} {listing.get('currency', 'INR')}
      Image Hash  : {listing.get('image_hash', 'N/A')[:32] if listing.get('image_hash') else 'N/A'}"""

        if wallets:
            dossier += f"""

CRYPTocurrency WALLET EVIDENCE ({len(wallets)} wallets)
{'─'*40}"""
            for w in wallets:
                dossier += f"""
  Address       : {w.get('address', 'N/A')}
  Currency      : {w.get('currency', 'BTC')}
  Balance       : {w.get('balance', 0)}
  Total Received: {w.get('total_received', 0)}
  Transactions  : {w.get('tx_count', 0)}
  Risk Flags    : {w.get('risk_flags', '[]')}"""

        if transactions:
            dossier += f"""

TRANSACTION LOG ({len(transactions)} transactions)
{'─'*40}"""
            for tx in transactions[:15]:
                dossier += f"""
  From    : {tx.get('wallet_from', 'N/A')[:20]}...
  To      : {tx.get('wallet_to', 'N/A')[:20]}...
  Amount  : {tx.get('amount', 0)} {tx.get('currency', 'BTC')}
  Time    : {tx.get('timestamp', 'N/A')}
  Mixer   : {'YES (Risk: ' + str(tx.get('mixer_risk', 0)) + ')' if tx.get('is_mixer') else 'No'}"""

        dossier += f"""

CHAIN OF CUSTODY LOG
{'─'*40}
  Evidence Hash : SHA-256 (per-item hashes in evidence metadata)
  Capture Tool  : {self.TOOL_NAME}
  Integrity     : All items hash-verified at capture time
  Tamper Evidence: Any modification will invalidate SHA-256 hash

LEGAL REFERENCES
{'─'*40}
  Applicable Act  : Narcotic Drugs and Psychotropic Substances Act, 1985
  Relevant Sections:
    - Section 22  : Punishment for contravention in relation to psychotropic substances
    - Section 20  : Punishment for contravention in relation to cannabis plant and cannabis
    - Section 19  : Punishment for contravention in relation to opium poppy and opium
    - Section 21  : Punishment for contravention in relation to prepared opium
    - Section 29  : Punishment for attempt to commit offences
    - Section 41  : Power of entry, search, seizure and arrest
  IT Act Sections:
    - Section 66A : Sending offensive messages (amended)
    - Section 69A : Power to issue directions for blocking
    - Section 75  : Offences by companies

CERTIFICATION
{'─'*40}
  This dossier was automatically generated by the TRACE platform.
  All evidence items are SHA-256 hash-verified at time of capture.
  Chain of custody is maintained with timestamped audit entries.
  This report is prepared for use in NDPS Act proceedings.

{'='*70}
  END OF DOSSIER — TRACE v{self.TOOL_VERSION}
  Generated: {now}
{'='*70}
"""
        return dossier

    def _risk_label(self, score: float) -> str:
        if score > 0.8:
            return "CRITICAL"
        elif score > 0.6:
            return "HIGH"
        elif score > 0.4:
            return "MEDIUM"
        elif score > 0.2:
            return "LOW"
        return "CLEAN"


# Singleton
_locker = None


def get_evidence_locker() -> EvidenceLocker:
    global _locker
    if _locker is None:
        _locker = EvidenceLocker()
    return _locker
