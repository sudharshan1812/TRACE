"""
TRACE — Transnational Darknet & Encrypted Commerce Examiner
Main FastAPI Application
Chandigarh Police Hackathon 2026
"""
import os
import sys
import json
import socket
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from models import database as db
from models.slang_detector import analyze_text, get_detector, get_emoji_classifier
from models.entity_linker import get_entity_linker
from models.crypto_tracer import get_crypto_tracer
from models.evidence_locker import get_evidence_locker
from models.data_generator import generate_demo_data

# ── App Setup ────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
DB_PATH = os.path.join(BASE_DIR, "trace.db")


@asynccontextmanager
async def lifespan(app_instance):
    """Initialize database and generate demo data on startup."""
    try:
        db.init_db()
        if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) < 100:
            print("\n  [TRACE] First run detected — generating demo data...")
            generate_demo_data()
        else:
            stats = db.get_dashboard_stats()
            if stats["total_listings"] == 0:
                print("\n  [TRACE] Empty database — generating demo data...")
                generate_demo_data()
            else:
                print(f"\n  [TRACE] Database loaded — {stats['total_listings']} listings, "
                      f"{stats['total_vendors']} vendors")
    except Exception as e:
        print(f"\n  [TRACE] WARNING: Database init error: {e}")
        print("  [TRACE] Creating fresh database...")
        db.init_db()
        generate_demo_data()
    print("  [TRACE] Server ready.")
    print("  [TRACE] Open http://localhost:8000 in your browser\n")
    yield
    print("  [TRACE] Server shutting down.")


app = FastAPI(
    title="TRACE — Drug Intelligence Platform",
    description="Darknet & Encrypted Platform Drug Intelligence",
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)


# ── Pages ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── Dashboard API ────────────────────────────────────────────────────────────

@app.get("/api/dashboard/stats")
async def dashboard_stats():
    return db.get_dashboard_stats()


@app.get("/api/dashboard/alerts")
async def dashboard_alerts(limit: int = 20, severity: Optional[str] = None):
    return db.get_alerts(limit=limit, severity=severity)


@app.get("/api/dashboard/alert-counts")
async def alert_counts():
    return db.get_alert_counts()


@app.post("/api/dashboard/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int):
    db.mark_alert_read(alert_id)
    return {"status": "ok"}


# ── Listings API ─────────────────────────────────────────────────────────────

@app.get("/api/listings")
async def list_listings(limit: int = 50, source: Optional[str] = None,
                        min_score: float = 0.0, offset: int = 0):
    return db.get_listings(limit=limit, source=source, min_score=min_score, offset=offset)


@app.get("/api/listings/{listing_id}")
async def get_listing(listing_id: int):
    listing = db.get_listing(listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    return listing


@app.post("/api/analyze")
async def analyze_listing(request: Request):
    body = await request.json()
    text = body.get("text", "")
    if not text:
        raise HTTPException(400, "No text provided")
    result = analyze_text(text)
    return result


# ── Vendors API ──────────────────────────────────────────────────────────────

@app.get("/api/vendors")
async def list_vendors(limit: int = 50, platform: Optional[str] = None,
                       min_risk: float = 0.0):
    return db.get_vendors(limit=limit, platform=platform, min_risk=min_risk)


@app.get("/api/vendors/{vendor_id}")
async def get_vendor(vendor_id: int):
    vendor = db.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    links = db.get_vendor_links(vendor_id)
    wallets = db.get_wallets(vendor_id=vendor_id)
    listings = db.get_listings(limit=50)
    vendor["links"] = links
    vendor["wallets"] = wallets
    vendor["recent_listings"] = [l for l in listings if l.get("vendor_id") == vendor_id][:5]
    return vendor


@app.get("/api/vendors/graph/data")
async def vendor_graph():
    """Get vendor network graph data."""
    vendors = db.get_vendors(limit=30)
    linker = get_entity_linker()
    all_listings = db.get_listings(limit=120)
    for v in vendors:
        linker.register_vendor(v["id"], v)
        vendor_listings = [l["text"] for l in all_listings if l.get("vendor_id") == v["id"]]
        if vendor_listings:
            linker.compute_style_vector(v["id"], vendor_listings)
    return linker.get_graph_data()


@app.get("/api/vendors/links/all")
async def all_vendor_links():
    return db.get_vendor_links()


# ── Crypto API ───────────────────────────────────────────────────────────────

@app.get("/api/crypto/wallets")
async def list_wallets(vendor_id: Optional[int] = None, limit: int = 50):
    return db.get_wallets(vendor_id=vendor_id, limit=limit)


@app.get("/api/crypto/wallet/{address}")
async def get_wallet_detail(address: str):
    wallet = db.get_wallet(address)
    if not wallet:
        raise HTTPException(404, "Wallet not found")
    tracer = get_crypto_tracer()
    for w in db.get_wallets(limit=100):
        tracer.register_wallet(w["address"], w)
    for tx in db.get_transactions(limit=200):
        tracer.add_transaction(tx)
    risk = tracer.get_wallet_risk(address)
    flow = tracer.build_fund_flow_graph(address)
    txs = db.get_transactions(wallet_address=address)
    return {"wallet": wallet, "risk": risk, "flow": flow, "transactions": txs}


@app.get("/api/crypto/flow/{address}")
async def crypto_flow(address: str, depth: int = 3):
    tracer = get_crypto_tracer()
    for w in db.get_wallets(limit=100):
        tracer.register_wallet(w["address"], w)
    for tx in db.get_transactions(limit=200):
        tracer.add_transaction(tx)
    return tracer.build_fund_flow_graph(address, depth)


@app.get("/api/crypto/transactions")
async def list_transactions(wallet_address: Optional[str] = None, limit: int = 100):
    return db.get_transactions(wallet_address=wallet_address, limit=limit)


@app.get("/api/crypto/risk/{address}")
async def wallet_risk(address: str):
    tracer = get_crypto_tracer()
    for w in db.get_wallets(limit=100):
        tracer.register_wallet(w["address"], w)
    for tx in db.get_transactions(limit=200):
        tracer.add_transaction(tx)
    return tracer.get_wallet_risk(address)


# ── Evidence API ─────────────────────────────────────────────────────────────

@app.get("/api/evidence")
async def list_evidence(vendor_id: Optional[int] = None, listing_id: Optional[int] = None):
    return db.get_evidence(vendor_id=vendor_id, listing_id=listing_id)


@app.post("/api/evidence/capture")
async def capture_evidence(request: Request):
    body = await request.json()
    locker = get_evidence_locker()
    result = locker.capture(
        content=body.get("content", ""),
        artifact_type=body.get("type", "listing"),
        source=body.get("source", "Manual Capture"),
        metadata=body.get("metadata", {})
    )
    db.insert_evidence({
        "listing_id": body.get("listing_id"),
        "vendor_id": body.get("vendor_id"),
        "artifact_type": body.get("type", "listing"),
        "content_hash": result["content_hash"],
        "notes": body.get("notes", "")
    })
    return result


@app.post("/api/evidence/verify/{evidence_id}")
async def verify_evidence(evidence_id: int, request: Request):
    body = await request.json()
    locker = get_evidence_locker()
    return locker.verify(evidence_id, body.get("content", ""))


@app.get("/api/evidence/dossier/{vendor_id}")
async def generate_dossier(vendor_id: int):
    vendor = db.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    locker = get_evidence_locker()
    listings = [l for l in db.get_listings(limit=100) if l.get("vendor_id") == vendor_id]
    evidence = db.get_evidence(vendor_id=vendor_id)
    wallets = db.get_wallets(vendor_id=vendor_id)
    txs = []
    for w in wallets:
        txs.extend(db.get_transactions(wallet_address=w["address"], limit=20))
    dossier = locker.generate_dossier(vendor, listings, evidence, wallets, txs)
    return PlainTextResponse(dossier)


# ── Watchlist API ────────────────────────────────────────────────────────────

@app.get("/api/watchlist")
async def list_watchlist():
    return db.get_watchlists()


@app.post("/api/watchlist")
async def add_watchlist(request: Request):
    body = await request.json()
    wid = db.insert_watchlist(body)
    return {"id": wid, "status": "added"}


@app.delete("/api/watchlist/{watchlist_id}")
async def delete_watchlist(watchlist_id: int):
    db.delete_watchlist(watchlist_id)
    return {"status": "deleted"}


# ── Slang Drift API ─────────────────────────────────────────────────────────

@app.get("/api/slang/drift")
async def slang_drift(status: Optional[str] = None, limit: int = 50):
    return db.get_slang_drift(status=status, limit=limit)


@app.post("/api/slang/analyze")
async def slang_analyze(request: Request):
    body = await request.json()
    text = body.get("text", "")
    if not text:
        raise HTTPException(400, "No text provided")
    return analyze_text(text)


@app.get("/api/slang/lexicon")
async def get_lexicon():
    detector = get_detector()
    return {
        "term_count": len(detector.term_index),
        "substances": list(detector.lexicon.get("substances", {}).keys()),
        "emoji_count": len(detector.lexicon.get("emoji_mappings", {})),
        "location_regions": list(detector.lexicon.get("location_terms", {}).keys())
    }


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    PORT = 8000
    # Check if port is already in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("0.0.0.0", PORT))
        sock.close()
    except OSError:
        print(f"\n  [TRACE] Port {PORT} is already in use!")
        print(f"  [TRACE] Try closing the existing server first, or a new port will be used.\n")
        PORT = 8001
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock2.bind(("0.0.0.0", PORT))
            sock2.close()
        except OSError:
            print(f"  [TRACE] Port {PORT} also in use. Trying 8002...")
            PORT = 8002

    print(f"\n  TRACE Platform starting on http://localhost:{PORT}\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
