"""
TRACE Database Layer
SQLite database for listings, vendors, wallets, transactions, alerts, evidence, watchlists
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trace.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL DEFAULT 'telegram',
            source_id TEXT,
            channel_name TEXT,
            text TEXT NOT NULL,
            image_url TEXT,
            image_hash TEXT,
            price REAL,
            currency TEXT DEFAULT 'INR',
            vendor_id INTEGER,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            slang_score REAL DEFAULT 0.0,
            emoji_score REAL DEFAULT 0.0,
            combined_score REAL DEFAULT 0.0,
            detected_substances TEXT DEFAULT '[]',
            detected_emoji TEXT DEFAULT '[]',
            detected_locations TEXT DEFAULT '[]',
            detected_quantities TEXT DEFAULT '[]',
            is_drug INTEGER DEFAULT 0,
            reviewed INTEGER DEFAULT 0,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            handle TEXT,
            platform TEXT NOT NULL DEFAULT 'telegram',
            bio TEXT,
            risk_score REAL DEFAULT 0.0,
            total_listings INTEGER DEFAULT 0,
            active_days INTEGER DEFAULT 0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS vendor_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_a INTEGER NOT NULL,
            vendor_b INTEGER NOT NULL,
            similarity_score REAL DEFAULT 0.0,
            link_types TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_a) REFERENCES vendors(id),
            FOREIGN KEY (vendor_b) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL UNIQUE,
            currency TEXT DEFAULT 'BTC',
            vendor_id INTEGER,
            balance REAL DEFAULT 0.0,
            total_received REAL DEFAULT 0.0,
            total_sent REAL DEFAULT 0.0,
            tx_count INTEGER DEFAULT 0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            risk_flags TEXT DEFAULT '[]',
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_from TEXT NOT NULL,
            wallet_to TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'BTC',
            tx_hash TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_mixer INTEGER DEFAULT 0,
            mixer_risk REAL DEFAULT 0.0,
            block_height INTEGER,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'info',
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            listing_id INTEGER,
            vendor_id INTEGER,
            wallet_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0,
            FOREIGN KEY (listing_id) REFERENCES listings(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER,
            vendor_id INTEGER,
            artifact_type TEXT NOT NULL DEFAULT 'listing',
            content_hash TEXT NOT NULL,
            capture_tool TEXT DEFAULT 'TRACE v1.0',
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT,
            notes TEXT,
            chain_of_custody TEXT DEFAULT '[]',
            FOREIGN KEY (listing_id) REFERENCES listings(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS watchlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            match_type TEXT DEFAULT 'keyword',
            severity TEXT DEFAULT 'warning',
            alert_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS slang_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            language TEXT DEFAULT 'hinglish',
            category TEXT DEFAULT 'substance',
            drug_type TEXT,
            confidence REAL DEFAULT 0.7,
            is_auto_discovered INTEGER DEFAULT 0,
            discovered_at TIMESTAMP,
            added_by TEXT DEFAULT 'system'
        );

        CREATE TABLE IF NOT EXISTS slang_drift (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            context_snippet TEXT,
            frequency INTEGER DEFAULT 1,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'candidate',
            reviewed INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source);
        CREATE INDEX IF NOT EXISTS idx_listings_score ON listings(combined_score DESC);
        CREATE INDEX IF NOT EXISTS idx_listings_detected ON listings(detected_at DESC);
        CREATE INDEX IF NOT EXISTS idx_vendors_platform ON vendors(platform);
        CREATE INDEX IF NOT EXISTS idx_vendors_risk ON vendors(risk_score DESC);
        CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
        CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address);
        CREATE INDEX IF NOT EXISTS idx_transactions_from ON transactions(wallet_from);
        CREATE INDEX IF NOT EXISTS idx_transactions_to ON transactions(wallet_to);
    """)
    conn.commit()
    conn.close()


# ── Listings ────────────────────────────────────────────────────────────────

def insert_listing(data: Dict[str, Any]) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO listings (source, source_id, channel_name, text, image_url, image_hash,
            price, currency, vendor_id, slang_score, emoji_score, combined_score,
            detected_substances, detected_emoji, detected_locations, detected_quantities, is_drug)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.get("source", "telegram"), data.get("source_id"), data.get("channel_name"),
        data["text"], data.get("image_url"), data.get("image_hash"),
        data.get("price"), data.get("currency", "INR"), data.get("vendor_id"),
        data.get("slang_score", 0), data.get("emoji_score", 0), data.get("combined_score", 0),
        str(data.get("detected_substances", [])), str(data.get("detected_emoji", [])),
        str(data.get("detected_locations", [])), str(data.get("detected_quantities", [])),
        1 if data.get("combined_score", 0) > 0.5 else 0
    ))
    lid = cur.lastrowid
    conn.commit()
    conn.close()
    return lid


def get_listings(limit=50, source=None, min_score=0.0, offset=0):
    conn = get_db()
    query = "SELECT * FROM listings WHERE combined_score >= ?"
    params: list = [min_score]
    if source:
        query += " AND source = ?"
        params.append(source)
    query += " ORDER BY detected_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_listing(listing_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Vendors ─────────────────────────────────────────────────────────────────

def insert_vendor(data: Dict[str, Any]) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO vendors (name, handle, platform, bio, risk_score, total_listings, active_days, status)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        data["name"], data.get("handle"), data.get("platform", "telegram"),
        data.get("bio"), data.get("risk_score", 0), data.get("total_listings", 0),
        data.get("active_days", 0), data.get("status", "active")
    ))
    vid = cur.lastrowid
    conn.commit()
    conn.close()
    return vid


def get_vendors(limit=50, platform=None, min_risk=0.0):
    conn = get_db()
    query = "SELECT * FROM vendors WHERE risk_score >= ?"
    params: list = [min_risk]
    if platform:
        query += " AND platform = ?"
        params.append(platform)
    query += " ORDER BY risk_score DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_vendor(vendor_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Vendor Links ────────────────────────────────────────────────────────────

def insert_vendor_link(data: Dict[str, Any]) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO vendor_links (vendor_a, vendor_b, similarity_score, link_types)
        VALUES (?,?,?,?)
    """, (data["vendor_a"], data["vendor_b"], data.get("similarity_score", 0),
          str(data.get("link_types", []))))
    lid = cur.lastrowid
    conn.commit()
    conn.close()
    return lid


def get_vendor_links(vendor_id: int = None):
    conn = get_db()
    if vendor_id:
        rows = conn.execute("""
            SELECT vl.*, va.name as name_a, va.handle as handle_a,
                   vb.name as name_b, vb.handle as handle_b
            FROM vendor_links vl
            JOIN vendors va ON vl.vendor_a = va.id
            JOIN vendors vb ON vl.vendor_b = vb.id
            WHERE vl.vendor_a = ? OR vl.vendor_b = ?
            ORDER BY vl.similarity_score DESC
        """, (vendor_id, vendor_id)).fetchall()
    else:
        rows = conn.execute("""
            SELECT vl.*, va.name as name_a, va.handle as handle_a,
                   vb.name as name_b, vb.handle as handle_b
            FROM vendor_links vl
            JOIN vendors va ON vl.vendor_a = va.id
            JOIN vendors vb ON vl.vendor_b = vb.id
            ORDER BY vl.similarity_score DESC
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Wallets ─────────────────────────────────────────────────────────────────

def insert_wallet(data: Dict[str, Any]) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT OR IGNORE INTO wallets (address, currency, vendor_id, balance,
            total_received, total_sent, tx_count, risk_flags)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        data["address"], data.get("currency", "BTC"), data.get("vendor_id"),
        data.get("balance", 0), data.get("total_received", 0), data.get("total_sent", 0),
        data.get("tx_count", 0), str(data.get("risk_flags", []))
    ))
    wid = cur.lastrowid
    conn.commit()
    conn.close()
    return wid


def get_wallets(vendor_id=None, limit=50):
    conn = get_db()
    if vendor_id:
        rows = conn.execute("SELECT * FROM wallets WHERE vendor_id = ? LIMIT ?", (vendor_id, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM wallets ORDER BY total_received DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_wallet(address: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM wallets WHERE address = ?", (address,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Transactions ────────────────────────────────────────────────────────────

def insert_transaction(data: Dict[str, Any]) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO transactions (wallet_from, wallet_to, amount, currency, tx_hash,
            timestamp, is_mixer, mixer_risk, block_height, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        data["wallet_from"], data["wallet_to"], data["amount"],
        data.get("currency", "BTC"), data.get("tx_hash"),
        data.get("timestamp", datetime.now().isoformat()),
        data.get("is_mixer", 0), data.get("mixer_risk", 0),
        data.get("block_height"), data.get("notes")
    ))
    tid = cur.lastrowid
    conn.commit()
    conn.close()
    return tid


def get_transactions(wallet_address=None, limit=100):
    conn = get_db()
    if wallet_address:
        rows = conn.execute("""
            SELECT * FROM transactions
            WHERE wallet_from = ? OR wallet_to = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (wallet_address, wallet_address, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Alerts ──────────────────────────────────────────────────────────────────

def insert_alert(data: Dict[str, Any]) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO alerts (type, severity, title, message, listing_id, vendor_id, wallet_id)
        VALUES (?,?,?,?,?,?,?)
    """, (
        data["type"], data.get("severity", "info"), data["title"], data["message"],
        data.get("listing_id"), data.get("vendor_id"), data.get("wallet_id")
    ))
    aid = cur.lastrowid
    conn.commit()
    conn.close()
    return aid


def get_alerts(limit=50, severity=None, unread_only=False):
    conn = get_db()
    query = "SELECT * FROM alerts WHERE 1=1"
    params: list = []
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if unread_only:
        query += " AND is_read = 0"
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_alert_read(alert_id: int):
    conn = get_db()
    conn.execute("UPDATE alerts SET is_read = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()


def get_alert_counts():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    critical = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity='critical' AND is_read=0").fetchone()[0]
    warning = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity='warning' AND is_read=0").fetchone()[0]
    info = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity='info' AND is_read=0").fetchone()[0]
    conn.close()
    return {"total": total, "critical": critical, "warning": warning, "info": info}


# ── Evidence ────────────────────────────────────────────────────────────────

def insert_evidence(data: Dict[str, Any]) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO evidence (listing_id, vendor_id, artifact_type, content_hash,
            capture_tool, file_path, notes, chain_of_custody)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        data.get("listing_id"), data.get("vendor_id"), data.get("artifact_type", "listing"),
        data["content_hash"], data.get("capture_tool", "TRACE v1.0"),
        data.get("file_path"), data.get("notes"), str(data.get("chain_of_custody", []))
    ))
    eid = cur.lastrowid
    conn.commit()
    conn.close()
    return eid


def get_evidence(vendor_id=None, listing_id=None, limit=100):
    conn = get_db()
    query = "SELECT * FROM evidence WHERE 1=1"
    params: list = []
    if vendor_id:
        query += " AND vendor_id = ?"
        params.append(vendor_id)
    if listing_id:
        query += " AND listing_id = ?"
        params.append(listing_id)
    query += " ORDER BY captured_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Watchlists ──────────────────────────────────────────────────────────────

def insert_watchlist(data: Dict[str, Any]) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO watchlists (keyword, match_type, severity)
        VALUES (?,?,?)
    """, (data["keyword"], data.get("match_type", "keyword"), data.get("severity", "warning")))
    wid = cur.lastrowid
    conn.commit()
    conn.close()
    return wid


def get_watchlists():
    conn = get_db()
    rows = conn.execute("SELECT * FROM watchlists WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_watchlist(watchlist_id: int):
    conn = get_db()
    conn.execute("DELETE FROM watchlists WHERE id = ?", (watchlist_id,))
    conn.commit()
    conn.close()


# ── Slang Drift ─────────────────────────────────────────────────────────────

def insert_slang_drift(data: Dict[str, Any]) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO slang_drift (term, context_snippet, frequency, status)
        VALUES (?,?,?,?)
    """, (data["term"], data.get("context_snippet"), data.get("frequency", 1),
          data.get("status", "candidate")))
    sid = cur.lastrowid
    conn.commit()
    conn.close()
    return sid


def get_slang_drift(status=None, limit=50):
    conn = get_db()
    query = "SELECT * FROM slang_drift WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY frequency DESC, first_seen DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Stats ───────────────────────────────────────────────────────────────────

def get_dashboard_stats():
    conn = get_db()
    stats = {}
    stats["total_listings"] = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    stats["drug_listings"] = conn.execute("SELECT COUNT(*) FROM listings WHERE is_drug=1").fetchone()[0]
    stats["total_vendors"] = conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
    stats["high_risk_vendors"] = conn.execute("SELECT COUNT(*) FROM vendors WHERE risk_score > 0.7").fetchone()[0]
    stats["total_wallets"] = conn.execute("SELECT COUNT(*) FROM wallets").fetchone()[0]
    stats["total_transactions"] = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    stats["total_alerts"] = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    stats["unread_alerts"] = conn.execute("SELECT COUNT(*) FROM alerts WHERE is_read=0").fetchone()[0]
    stats["critical_alerts"] = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity='critical' AND is_read=0").fetchone()[0]
    stats["total_evidence"] = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    stats["avg_slang_score"] = conn.execute("SELECT COALESCE(AVG(slang_score),0) FROM listings").fetchone()[0]
    stats["avg_emoji_score"] = conn.execute("SELECT COALESCE(AVG(emoji_score),0) FROM listings").fetchone()[0]

    # Listings by source
    rows = conn.execute("SELECT source, COUNT(*) as count FROM listings GROUP BY source").fetchall()
    stats["listings_by_source"] = {r["source"]: r["count"] for r in rows}

    # Listings by day (last 7 days)
    rows = conn.execute("""
        SELECT DATE(detected_at) as day, COUNT(*) as count, SUM(is_drug) as drug_count
        FROM listings
        WHERE detected_at >= datetime('now', '-7 days')
        GROUP BY DATE(detected_at) ORDER BY day
    """).fetchall()
    stats["listings_by_day"] = [dict(r) for r in rows]

    # Top substances
    rows = conn.execute("""
        SELECT detected_substances, COUNT(*) as count FROM listings
        WHERE detected_substances != '[]'
        GROUP BY detected_substances ORDER BY count DESC LIMIT 10
    """).fetchall()
    stats["top_substances_raw"] = [dict(r) for r in rows]

    # Alerts by severity
    rows = conn.execute("SELECT severity, COUNT(*) as count FROM alerts GROUP BY severity").fetchall()
    stats["alerts_by_severity"] = {r["severity"]: r["count"] for r in rows}

    conn.close()
    return stats
