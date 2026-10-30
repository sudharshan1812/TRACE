"""
TRACE Crypto Tracer — Cryptocurrency Wallet Analysis & Fund Flow Visualization
Provides wallet clustering, mixer/tumbler detection, transaction graph building,
and fund flow visualization data for the investigation dashboard.
"""
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class CryptoTracer:
    """Traces cryptocurrency wallet activity and builds fund flow graphs."""

    # Known exchange/mixer wallet prefixes (simplified for demo)
    KNOWN_EXCHANGES = {
        "1A1zP1": "Satoshi Nakamoto (Genesis)",
        "3J98t1W": "Coinbase Hot Wallet",
        "bc1qm": "Bitstamp",
        "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s": "Binance",
        "0x28C6c06298d514Db089934071355E5743bf21d60": "Binance",
        "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549": "Binance",
    }

    KNOWN_MIXERS = {
        "1CoinJo": "CoinJoin (Wasabi)",
        "bc1qa": "JoinMarket",
        "0xs": "Tornado Cash",
        "TAddr": "ChipMixer",
    }

    def __init__(self):
        self.wallets: Dict[str, Dict] = {}
        self.transactions: List[Dict] = []
        self.clusters: Dict[str, set] = {}

    def register_wallet(self, address: str, data: Dict = None):
        """Register a wallet address for tracking."""
        if address not in self.wallets:
            self.wallets[address] = {
                "address": address,
                "currency": data.get("currency", "BTC") if data else "BTC",
                "balance": data.get("balance", 0) if data else 0,
                "total_received": data.get("total_received", 0) if data else 0,
                "total_sent": data.get("total_sent", 0) if data else 0,
                "tx_count": data.get("tx_count", 0) if data else 0,
                "vendor_id": data.get("vendor_id") if data else None,
                "risk_flags": [],
                "first_seen": data.get("first_seen", datetime.now().isoformat()) if data else datetime.now().isoformat(),
                "labels": self._label_wallet(address),
            }

    def add_transaction(self, tx: Dict) -> Dict:
        """Record a transaction and compute risk indicators."""
        tx_from = tx.get("wallet_from", "")
        tx_to = tx.get("wallet_to", "")
        amount = tx.get("amount", 0)

        # Detect mixer involvement
        mixer_risk = 0.0
        is_mixer = False
        for pattern, name in self.KNOWN_MIXERS.items():
            if pattern in tx_from or pattern in tx_to:
                mixer_risk = 0.9
                is_mixer = True
                break

        # Round-number transaction risk (common in laundering)
        if amount > 0 and amount == round(amount, 0) and amount >= 1.0:
            mixer_risk = max(mixer_risk, 0.3)

        # High-value single transaction
        if amount >= 10.0:
            mixer_risk = max(mixer_risk, 0.4)

        # Structuring detection (multiple transactions just below threshold)
        recent_sends = [t for t in self.transactions
                        if t.get("wallet_from") == tx_from
                        and t.get("amount", 0) >= 0.9 and t.get("amount", 0) <= 1.1]
        if len(recent_sends) > 3:
            mixer_risk = max(mixer_risk, 0.7)

        enriched_tx = {
            **tx,
            "is_mixer": 1 if is_mixer else 0,
            "mixer_risk": round(mixer_risk, 2),
            "risk_level": self._risk_label(mixer_risk)
        }
        self.transactions.append(enriched_tx)
        return enriched_tx

    def get_wallet_risk(self, address: str) -> Dict:
        """Compute aggregate risk score for a wallet."""
        wallet = self.wallets.get(address, {})
        incoming = [t for t in self.transactions if t.get("wallet_to") == address]
        outgoing = [t for t in self.transactions if t.get("wallet_from") == address]
        all_txs = incoming + outgoing

        total_volume = sum(t.get("amount", 0) for t in all_txs)
        mixer_txs = [t for t in all_txs if t.get("is_mixer")]
        max_mixer_risk = max((t.get("mixer_risk", 0) for t in all_txs), default=0)

        # Exchange interaction
        exchange_interactions = 0
        for t in all_txs:
            for pattern in self.KNOWN_EXCHANGES:
                if pattern in t.get("wallet_from", "") or pattern in t.get("wallet_to", ""):
                    exchange_interactions += 1

        risk_score = min(
            max_mixer_risk * 0.4 +
            (len(mixer_txs) / max(len(all_txs), 1)) * 0.3 +
            min(total_volume / 100, 1.0) * 0.15 +
            min(exchange_interactions / max(len(all_txs), 1), 1.0) * 0.15,
            1.0
        )

        return {
            "address": address,
            "risk_score": round(risk_score, 3),
            "risk_label": self._risk_label(risk_score),
            "total_volume": round(total_volume, 6),
            "tx_count": len(all_txs),
            "mixer_interactions": len(mixer_txs),
            "exchange_interactions": exchange_interactions,
            "max_mixer_risk": round(max_mixer_risk, 3),
            "labels": wallet.get("labels", [])
        }

    def build_fund_flow_graph(self, center_address: str, depth: int = 3) -> Dict:
        """Build a fund flow graph centered on a wallet address."""
        nodes = []
        edges = []
        visited = set()

        def _trace(address: str, current_depth: int):
            if current_depth > depth or address in visited:
                return
            visited.add(address)

            wallet = self.wallets.get(address, {})
            risk = self.get_wallet_risk(address)
            nodes.append({
                "id": address,
                "label": address[:12] + "..." if len(address) > 15 else address,
                "full_address": address,
                "balance": wallet.get("balance", 0),
                "risk_score": risk["risk_score"],
                "risk_label": risk["risk_label"],
                "labels": risk["labels"],
                "is_center": address == center_address
            })

            # Outgoing
            for tx in self.transactions:
                if tx.get("wallet_from") == address and tx.get("wallet_to") not in visited:
                    to_addr = tx["wallet_to"]
                    edges.append({
                        "from": address,
                        "to": to_addr,
                        "amount": tx.get("amount", 0),
                        "is_mixer": tx.get("is_mixer", 0),
                        "mixer_risk": tx.get("mixer_risk", 0),
                        "timestamp": tx.get("timestamp", "")
                    })
                    _trace(to_addr, current_depth + 1)

                # Incoming
                if tx.get("wallet_to") == address and tx.get("wallet_from") not in visited:
                    from_addr = tx["wallet_from"]
                    edges.append({
                        "from": from_addr,
                        "to": address,
                        "amount": tx.get("amount", 0),
                        "is_mixer": tx.get("is_mixer", 0),
                        "mixer_risk": tx.get("mixer_risk", 0),
                        "timestamp": tx.get("timestamp", "")
                    })
                    _trace(from_addr, current_depth + 1)

        _trace(center_address, 0)
        return {"nodes": nodes, "edges": edges}

    def get_all_wallets_summary(self) -> List[Dict]:
        """Get summary of all tracked wallets with risk scores."""
        summaries = []
        for addr, wallet in self.wallets.items():
            risk = self.get_wallet_risk(addr)
            summaries.append({
                "address": addr,
                "short_address": addr[:16] + "...",
                "currency": wallet.get("currency", "BTC"),
                "balance": wallet.get("balance", 0),
                "total_received": wallet.get("total_received", 0),
                "tx_count": wallet.get("tx_count", 0),
                "risk_score": risk["risk_score"],
                "risk_label": risk["risk_label"],
                "vendor_id": wallet.get("vendor_id"),
                "labels": wallet.get("labels", []),
                "first_seen": wallet.get("first_seen", "")
            })
        summaries.sort(key=lambda x: x["risk_score"], reverse=True)
        return summaries

    def _label_wallet(self, address: str) -> List[str]:
        """Auto-label known wallets."""
        labels = []
        for pattern, name in self.KNOWN_EXCHANGES.items():
            if pattern in address:
                labels.append(f"Exchange: {name}")
        for pattern, name in self.KNOWN_MIXERS.items():
            if pattern in address:
                labels.append(f"Mixer: {name}")
        return labels

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
_tracer = None


def get_crypto_tracer() -> CryptoTracer:
    global _tracer
    if _tracer is None:
        _tracer = CryptoTracer()
    return _tracer
