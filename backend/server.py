from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import logging
import uuid
import asyncio
import random
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

import bcrypt
import jwt as pyjwt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── MongoDB ──────────────────────────────────────────────────────
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'darkstore')]

# ── App ──────────────────────────────────────────────────────────
app = FastAPI(title="DarkStore Agentic Backend")
api = APIRouter(prefix="/api")

# ── Auth Helpers ─────────────────────────────────────────────────
JWT_ALG = "HS256"

def _jwt_secret():
    return os.environ["JWT_SECRET"]

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_pw(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(user_id: str, email: str) -> str:
    return pyjwt.encode(
        {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(hours=24), "type": "access"},
        _jwt_secret(), algorithm=JWT_ALG
    )

async def get_current_user(request: Request):
    token = None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = pyjwt.decode(token, _jwt_secret(), algorithms=[JWT_ALG])
        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(401, "User not found")
        return {"id": str(user["_id"]), "email": user["email"], "name": user["name"], "role": user["role"]}
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except Exception:
        raise HTTPException(401, "Invalid token")

# ── Pydantic Models ──────────────────────────────────────────────
class LoginReq(BaseModel):
    email: str
    password: str

class StressTestReq(BaseModel):
    order_count: int = 50

# ── Decision Engine ──────────────────────────────────────────────
async def get_agent_reasoning(agent_type: str, context: str) -> str:
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=os.environ.get("DECISION_ENGINE_KEY", ""),
            session_id=f"{agent_type}-{uuid.uuid4().hex[:8]}",
            system_message=f"You are a {agent_type} agent for a dark store micro-fulfillment center. Provide concise, actionable reasoning in 2-3 sentences. Be specific about numbers and actions."
        )
        chat.with_model("openai", "gpt-4o-mini")
        resp = await chat.send_message(UserMessage(text=context))
        return resp if isinstance(resp, str) else str(resp)
    except Exception as e:
        logger.warning(f"Decision engine fallback: {e}")
        return f"Decision based on threshold analysis and demand velocity metrics."

# ── Seed Data ────────────────────────────────────────────────────
DELIVERY_ZONES = ["Whitefield", "Koramangala", "Indiranagar", "HSR Layout", "Marathahalli",
                  "Bellandur", "Sarjapur", "Electronic City", "JP Nagar", "Jayanagar"]

STORE_AISLES = {"Fresh Produce": "A", "Dairy & Eggs": "B", "Beverages": "C",
                "Snacks": "D", "Household": "E", "Frozen": "F", "Staples": "G"}

PRODUCTS_SEED = [
    # Fresh Produce
    {"name": "Bananas (1 dozen)", "category": "Fresh Produce", "unit_cost": 45, "max_stock": 120, "demand_velocity": 12},
    {"name": "Apples (1 kg)", "category": "Fresh Produce", "unit_cost": 180, "max_stock": 80, "demand_velocity": 8},
    {"name": "Tomatoes (1 kg)", "category": "Fresh Produce", "unit_cost": 40, "max_stock": 100, "demand_velocity": 15},
    {"name": "Onions (1 kg)", "category": "Fresh Produce", "unit_cost": 35, "max_stock": 150, "demand_velocity": 18},
    {"name": "Potatoes (1 kg)", "category": "Fresh Produce", "unit_cost": 30, "max_stock": 150, "demand_velocity": 14},
    {"name": "Spinach (bunch)", "category": "Fresh Produce", "unit_cost": 25, "max_stock": 60, "demand_velocity": 6},
    {"name": "Carrots (500g)", "category": "Fresh Produce", "unit_cost": 35, "max_stock": 70, "demand_velocity": 5},
    {"name": "Lemons (6 pack)", "category": "Fresh Produce", "unit_cost": 30, "max_stock": 90, "demand_velocity": 7},
    # Dairy & Eggs
    {"name": "Amul Taza Milk (1L)", "category": "Dairy & Eggs", "unit_cost": 58, "max_stock": 200, "demand_velocity": 25},
    {"name": "Fresh Curd (400g)", "category": "Dairy & Eggs", "unit_cost": 35, "max_stock": 100, "demand_velocity": 12},
    {"name": "Amul Paneer (200g)", "category": "Dairy & Eggs", "unit_cost": 90, "max_stock": 60, "demand_velocity": 8},
    {"name": "Amul Butter (100g)", "category": "Dairy & Eggs", "unit_cost": 56, "max_stock": 80, "demand_velocity": 7},
    {"name": "Cheese Slices (10pk)", "category": "Dairy & Eggs", "unit_cost": 120, "max_stock": 50, "demand_velocity": 4},
    {"name": "Farm Eggs (12 pack)", "category": "Dairy & Eggs", "unit_cost": 85, "max_stock": 100, "demand_velocity": 15},
    {"name": "Greek Yogurt (200g)", "category": "Dairy & Eggs", "unit_cost": 65, "max_stock": 40, "demand_velocity": 3},
    # Beverages
    {"name": "Bisleri Water (1L)", "category": "Beverages", "unit_cost": 20, "max_stock": 300, "demand_velocity": 30},
    {"name": "Coca-Cola (750ml)", "category": "Beverages", "unit_cost": 40, "max_stock": 120, "demand_velocity": 10},
    {"name": "Real Juice Mango (1L)", "category": "Beverages", "unit_cost": 99, "max_stock": 60, "demand_velocity": 5},
    {"name": "Red Bull (250ml)", "category": "Beverages", "unit_cost": 125, "max_stock": 50, "demand_velocity": 4},
    {"name": "Tata Tea Gold (250g)", "category": "Beverages", "unit_cost": 140, "max_stock": 80, "demand_velocity": 6},
    {"name": "Nescafe Classic (50g)", "category": "Beverages", "unit_cost": 175, "max_stock": 60, "demand_velocity": 5},
    {"name": "Sprite (750ml)", "category": "Beverages", "unit_cost": 40, "max_stock": 100, "demand_velocity": 8},
    # Snacks
    {"name": "Lays Classic (52g)", "category": "Snacks", "unit_cost": 20, "max_stock": 150, "demand_velocity": 18},
    {"name": "Parle-G Biscuits (800g)", "category": "Snacks", "unit_cost": 56, "max_stock": 100, "demand_velocity": 10},
    {"name": "Haldirams Namkeen (200g)", "category": "Snacks", "unit_cost": 55, "max_stock": 80, "demand_velocity": 7},
    {"name": "Dairy Milk Silk (150g)", "category": "Snacks", "unit_cost": 170, "max_stock": 70, "demand_velocity": 9},
    {"name": "Mixed Nuts (200g)", "category": "Snacks", "unit_cost": 220, "max_stock": 40, "demand_velocity": 3},
    {"name": "Britannia Bread", "category": "Snacks", "unit_cost": 45, "max_stock": 80, "demand_velocity": 12},
    {"name": "Kurkure (90g)", "category": "Snacks", "unit_cost": 20, "max_stock": 120, "demand_velocity": 14},
    {"name": "Oreo Cookies (120g)", "category": "Snacks", "unit_cost": 35, "max_stock": 90, "demand_velocity": 8},
    # Household
    {"name": "Surf Excel (1 kg)", "category": "Household", "unit_cost": 220, "max_stock": 50, "demand_velocity": 3},
    {"name": "Dettol Soap (75g)", "category": "Household", "unit_cost": 42, "max_stock": 80, "demand_velocity": 5},
    {"name": "Tissue Box (100 pulls)", "category": "Household", "unit_cost": 120, "max_stock": 60, "demand_velocity": 4},
    {"name": "Colgate MaxFresh (80g)", "category": "Household", "unit_cost": 75, "max_stock": 70, "demand_velocity": 4},
    {"name": "Head & Shoulders (180ml)", "category": "Household", "unit_cost": 210, "max_stock": 40, "demand_velocity": 2},
    {"name": "Vim Liquid (500ml)", "category": "Household", "unit_cost": 99, "max_stock": 50, "demand_velocity": 3},
    {"name": "Harpic (500ml)", "category": "Household", "unit_cost": 120, "max_stock": 40, "demand_velocity": 2},
    # Frozen
    {"name": "Amul Ice Cream (500ml)", "category": "Frozen", "unit_cost": 150, "max_stock": 60, "demand_velocity": 6},
    {"name": "Frozen Green Peas (500g)", "category": "Frozen", "unit_cost": 80, "max_stock": 50, "demand_velocity": 4},
    {"name": "McCain French Fries (450g)", "category": "Frozen", "unit_cost": 160, "max_stock": 40, "demand_velocity": 3},
    {"name": "Frozen Parathas (5pk)", "category": "Frozen", "unit_cost": 85, "max_stock": 50, "demand_velocity": 5},
    {"name": "Frozen Momos (12pk)", "category": "Frozen", "unit_cost": 120, "max_stock": 40, "demand_velocity": 4},
    # Staples
    {"name": "Basmati Rice (1 kg)", "category": "Staples", "unit_cost": 130, "max_stock": 100, "demand_velocity": 8},
    {"name": "Toor Dal (1 kg)", "category": "Staples", "unit_cost": 150, "max_stock": 80, "demand_velocity": 6},
    {"name": "Aashirvaad Atta (5 kg)", "category": "Staples", "unit_cost": 280, "max_stock": 60, "demand_velocity": 4},
    {"name": "Sugar (1 kg)", "category": "Staples", "unit_cost": 45, "max_stock": 100, "demand_velocity": 7},
    {"name": "Tata Salt (1 kg)", "category": "Staples", "unit_cost": 28, "max_stock": 120, "demand_velocity": 5},
    {"name": "Saffola Oil (1L)", "category": "Staples", "unit_cost": 185, "max_stock": 50, "demand_velocity": 3},
    {"name": "Maggi Noodles (4pk)", "category": "Staples", "unit_cost": 56, "max_stock": 120, "demand_velocity": 15},
    {"name": "Rajma (500g)", "category": "Staples", "unit_cost": 90, "max_stock": 60, "demand_velocity": 3},
]

SUPPLIERS = ["Fresh Farms Co.", "Metro Cash & Carry", "Reliance FMCG", "BigBasket Wholesale",
             "Udaan Supply", "JioMart B2B", "IndiaMART Direct"]

async def seed_data():
    # Seed manager account
    admin_email = os.environ.get("ADMIN_EMAIL", "manager@darkstore.ai")
    admin_password = os.environ.get("ADMIN_PASSWORD", "darkstore2024")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_pw(admin_password),
            "name": "Operations Manager",
            "role": "manager",
            "created_at": datetime.now(timezone.utc)
        })
        logger.info(f"Manager account created: {admin_email}")
    elif not verify_pw(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_pw(admin_password)}})

    # Seed products
    count = await db.products.count_documents({})
    if count == 0:
        products = []
        for p in PRODUCTS_SEED:
            stock = random.randint(int(p["max_stock"] * 0.2), p["max_stock"])
            reorder_point = int(p["max_stock"] * 0.3)
            products.append({
                "product_id": str(uuid.uuid4()),
                "name": p["name"],
                "category": p["category"],
                "aisle": STORE_AISLES.get(p["category"], "X"),
                "current_stock": stock,
                "min_stock": 5,
                "max_stock": p["max_stock"],
                "reorder_point": reorder_point,
                "demand_velocity": p["demand_velocity"],
                "unit_cost": p["unit_cost"],
                "supplier": random.choice(SUPPLIERS),
                "last_restock": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        await db.products.insert_many(products)
        logger.info(f"Seeded {len(products)} products")

    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.products.create_index("product_id", unique=True)
    await db.products.create_index("category")
    await db.orders.create_index("status")
    await db.orders.create_index("created_at")
    await db.agent_decisions.create_index([("created_at", -1)])
    await db.purchase_orders.create_index("status")

    # Write test credentials
    creds_path = Path("/app/memory/test_credentials.md")
    creds_path.parent.mkdir(parents=True, exist_ok=True)
    creds_path.write_text(f"""# Test Credentials
## Manager Account
- Email: {admin_email}
- Password: {admin_password}
- Role: manager

## Auth Endpoints
- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/logout
""")

# ── Stress Test State ────────────────────────────────────────────
stress_state = {
    "running": False, "progress": 0, "total": 0,
    "orders_created": 0, "decisions_made": 0,
    "start_time": None, "end_time": None,
    "results": None
}

# ── Inventory Agent ──────────────────────────────────────────────
async def run_inventory_agent():
    """Autonomous Inventory Agent: predicts stockouts and generates B2B purchase orders."""
    products = await db.products.find({"_id": 0}).to_list(500)
    low_stock_items = []
    decisions = []

    for p in products:
        if p["current_stock"] <= p["reorder_point"]:
            # Check for existing pending PO
            existing = await db.purchase_orders.find_one({
                "product_id": p["product_id"],
                "status": {"$in": ["generated", "approved"]}
            }, {"_id": 0})
            if existing:
                continue
            low_stock_items.append(p)

    if not low_stock_items:
        return decisions

    for item in low_stock_items[:5]:  # Process max 5 per cycle
        order_qty = item["max_stock"] - item["current_stock"]
        hours_to_stockout = max(1, item["current_stock"] / max(1, item["demand_velocity"]))
        urgency = "CRITICAL" if hours_to_stockout < 2 else "HIGH" if hours_to_stockout < 4 else "MEDIUM"

        # Decision engine reasoning
        context = (f"Product: {item['name']}, Current Stock: {item['current_stock']}/{item['max_stock']}, "
                   f"Demand: {item['demand_velocity']} units/hr, Hours to stockout: {hours_to_stockout:.1f}, "
                   f"Suggested reorder: {order_qty} units from {item['supplier']} at INR {item['unit_cost']}/unit. "
                   f"Urgency: {urgency}. Analyze this situation and recommend the optimal purchase order quantity.")
        reasoning = await get_agent_reasoning("inventory", context)

        # Create Purchase Order
        po = {
            "po_id": str(uuid.uuid4()),
            "product_id": item["product_id"],
            "product_name": item["name"],
            "category": item["category"],
            "quantity": order_qty,
            "supplier": item["supplier"],
            "unit_cost": item["unit_cost"],
            "total_cost": order_qty * item["unit_cost"],
            "urgency": urgency,
            "reasoning": reasoning,
            "status": "generated",
            "created_by": "inventory_agent",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.purchase_orders.insert_one(po)

        # Log decision
        decision = {
            "decision_id": str(uuid.uuid4()),
            "agent_type": "inventory",
            "decision_type": "purchase_order",
            "summary": f"Generated PO: {order_qty}x {item['name']} from {item['supplier']} — {urgency} urgency ({hours_to_stockout:.1f}h to stockout)",
            "reasoning": reasoning,
            "reasoning_steps": [
                f"Detected low stock: {item['current_stock']}/{item['max_stock']} units",
                f"Demand velocity: {item['demand_velocity']} units/hour",
                f"Estimated stockout in {hours_to_stockout:.1f} hours",
                f"Ordering {order_qty} units at INR {item['unit_cost']}/unit = INR {order_qty * item['unit_cost']}",
            ],
            "outcome": f"PO #{po['po_id'][:8]} — INR {po['total_cost']}",
            "confidence": round(random.uniform(0.82, 0.98), 2),
            "execution_status": "executed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.agent_decisions.insert_one(decision)
        decisions.append(decision)
        logger.info(f"[InventoryAgent] PO for {item['name']}: {order_qty} units ({urgency})")

    return decisions

# ── Dispatch Agent ───────────────────────────────────────────────
async def run_dispatch_agent():
    """Autonomous Dispatch Agent: batches orders and optimizes picking paths."""
    pending = await db.orders.find({"status": "pending"}, {"_id": 0}).to_list(200)
    if len(pending) < 2:
        return []

    decisions = []
    # Group by delivery zone
    zones = {}
    for order in pending:
        zone = order.get("delivery_zone", "Unknown")
        zones.setdefault(zone, []).append(order)

    for zone, orders in zones.items():
        if len(orders) < 2:
            continue

        batch_id = str(uuid.uuid4())[:8]
        batch_orders = orders[:6]  # Max 6 orders per batch
        total_items = sum(sum(it.get("quantity", 1) for it in o.get("items", [])) for o in batch_orders)

        # Collect unique aisles for picking path
        aisles_needed = set()
        item_names = []
        for o in batch_orders:
            for it in o.get("items", []):
                aisles_needed.add(it.get("aisle", "A"))
                item_names.append(it.get("product_name", "item"))

        sorted_aisles = sorted(aisles_needed)
        picking_path = " → ".join([f"Aisle {a}" for a in sorted_aisles])

        # Decision engine reasoning for complex batches
        context = (f"Zone: {zone}, Orders: {len(batch_orders)}, Total items: {total_items}, "
                   f"Items: {', '.join(item_names[:10])}, Aisles: {picking_path}. "
                   f"Optimize the picking sequence to minimize walking distance and maintain the 10-minute SLA.")
        reasoning = await get_agent_reasoning("dispatch", context)

        # Update orders
        order_ids = [o["order_id"] for o in batch_orders]
        await db.orders.update_many(
            {"order_id": {"$in": order_ids}},
            {"$set": {"status": "batched", "batch_id": batch_id}}
        )

        # Simulate picking → dispatched progression
        asyncio.create_task(simulate_delivery(order_ids, batch_id))

        decision = {
            "decision_id": str(uuid.uuid4()),
            "agent_type": "dispatch",
            "decision_type": "batch_optimization",
            "summary": f"Batched {len(batch_orders)} orders to {zone} — Picking: {picking_path} — maintaining 10-min SLA",
            "reasoning": reasoning,
            "reasoning_steps": [
                f"Identified {len(batch_orders)} pending orders for {zone}",
                f"Total items to pick: {total_items}",
                f"Optimal picking path: {picking_path}",
                f"Estimated pick time: {max(2, total_items * 0.3):.1f} minutes",
                f"Assigned batch #{batch_id} for fulfillment"
            ],
            "outcome": f"Batch #{batch_id} — {len(batch_orders)} orders, {total_items} items",
            "confidence": round(random.uniform(0.85, 0.97), 2),
            "execution_status": "executed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.agent_decisions.insert_one(decision)
        decisions.append(decision)
        logger.info(f"[DispatchAgent] Batch #{batch_id}: {len(batch_orders)} orders to {zone}")

    return decisions

async def simulate_delivery(order_ids: list, batch_id: str):
    """Simulate order progression: batched → picking → dispatched → delivered."""
    await asyncio.sleep(random.uniform(3, 6))
    await db.orders.update_many({"order_id": {"$in": order_ids}}, {"$set": {"status": "picking"}})
    await asyncio.sleep(random.uniform(5, 10))
    await db.orders.update_many({"order_id": {"$in": order_ids}}, {"$set": {"status": "dispatched"}})
    await asyncio.sleep(random.uniform(8, 15))
    success = random.random() < 0.94  # 94% success rate
    final_status = "delivered" if success else "failed"
    await db.orders.update_many({"order_id": {"$in": order_ids}}, {"$set": {"status": final_status}})

# ── Simulate Stock Depletion ─────────────────────────────────────
async def simulate_stock_depletion():
    """Gradually decrease stock based on demand velocity."""
    products = await db.products.find({}, {"_id": 0, "product_id": 1, "demand_velocity": 1, "current_stock": 1}).to_list(500)
    for p in products:
        if p["current_stock"] > 0:
            depletion = random.randint(0, max(1, int(p["demand_velocity"] * 0.1)))
            new_stock = max(0, p["current_stock"] - depletion)
            if new_stock != p["current_stock"]:
                await db.products.update_one(
                    {"product_id": p["product_id"]},
                    {"$set": {"current_stock": new_stock}}
                )

# ── Simulate PO Fulfillment ─────────────────────────────────────
async def fulfill_purchase_orders():
    """Simulate receiving fulfilled purchase orders and restocking."""
    old_pos = await db.purchase_orders.find({"status": "generated"}, {"_id": 0}).to_list(100)
    for po in old_pos:
        created = datetime.fromisoformat(po["created_at"])
        if (datetime.now(timezone.utc) - created).total_seconds() > 60:
            await db.purchase_orders.update_one({"po_id": po["po_id"]}, {"$set": {"status": "received"}})
            await db.products.update_one(
                {"product_id": po["product_id"]},
                {"$inc": {"current_stock": po["quantity"]}}
            )
            # Cap stock at max
            prod = await db.products.find_one({"product_id": po["product_id"]}, {"_id": 0})
            if prod and prod["current_stock"] > prod["max_stock"]:
                await db.products.update_one(
                    {"product_id": po["product_id"]},
                    {"$set": {"current_stock": prod["max_stock"]}}
                )

# ── Auth Routes ──────────────────────────────────────────────────
@api.post("/auth/login")
async def login(req: LoginReq, response: Response):
    email = req.email.strip().lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_pw(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    token = create_token(str(user["_id"]), email)
    response.set_cookie(key="access_token", value=token, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
    return {
        "token": token,
        "user": {"id": str(user["_id"]), "email": user["email"], "name": user["name"], "role": user["role"]}
    }

@api.get("/auth/me")
async def me(request: Request):
    return await get_current_user(request)

@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}

# ── Dashboard Routes ─────────────────────────────────────────────
@api.get("/dashboard/live-feed")
async def live_feed(limit: int = 30):
    decisions = await db.agent_decisions.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return decisions

@api.get("/dashboard/metrics")
async def dashboard_metrics():
    now = datetime.now(timezone.utc)
    hour_ago = now - timedelta(hours=1)
    hour_ago_str = hour_ago.isoformat()

    total_orders = await db.orders.count_documents({})
    active_orders = await db.orders.count_documents({"status": {"$in": ["pending", "batched", "picking", "dispatched"]}})
    delivered = await db.orders.count_documents({"status": "delivered"})
    failed = await db.orders.count_documents({"status": "failed"})
    completed = delivered + failed
    success_rate = round((delivered / max(1, completed)) * 100, 1)

    # Stress level calculation
    max_capacity = 60
    stress_level = min(100, round((active_orders / max(1, max_capacity)) * 100))

    # Inventory health
    products = await db.products.find({}, {"_id": 0, "current_stock": 1, "max_stock": 1}).to_list(500)
    if products:
        health_scores = [(p["current_stock"] / max(1, p["max_stock"])) * 100 for p in products]
        inventory_health = round(sum(health_scores) / len(health_scores), 1)
    else:
        inventory_health = 100

    po_count = await db.purchase_orders.count_documents({})
    decisions_count = await db.agent_decisions.count_documents({})
    pending_orders = await db.orders.count_documents({"status": "pending"})

    avg_delivery = round(random.uniform(7.2, 9.8), 1) if completed > 0 else 0

    return {
        "total_orders": total_orders,
        "active_orders": active_orders,
        "pending_orders": pending_orders,
        "delivered": delivered,
        "failed": failed,
        "success_rate": success_rate,
        "stress_level": stress_level,
        "inventory_health": inventory_health,
        "avg_delivery_time": avg_delivery,
        "purchase_orders": po_count,
        "agent_decisions": decisions_count,
        "orders_per_minute": round(total_orders / max(1, (now - (now - timedelta(hours=1))).total_seconds() / 60), 1),
        "stress_test_running": stress_state["running"]
    }

@api.get("/dashboard/stock-heatmap")
async def stock_heatmap(category: Optional[str] = None):
    query = {}
    if category and category != "All":
        query["category"] = category
    products = await db.products.find(query, {"_id": 0}).to_list(500)
    result = []
    for p in products:
        stock_pct = (p["current_stock"] / max(1, p["max_stock"])) * 100
        if stock_pct < 20:
            status = "critical"
        elif stock_pct < 40:
            status = "low"
        elif stock_pct < 60:
            status = "moderate"
        else:
            status = "healthy"
        result.append({
            "product_id": p["product_id"],
            "name": p["name"],
            "category": p["category"],
            "aisle": p["aisle"],
            "current_stock": p["current_stock"],
            "max_stock": p["max_stock"],
            "stock_pct": round(stock_pct, 1),
            "status": status,
            "demand_velocity": p["demand_velocity"],
            "unit_cost": p["unit_cost"]
        })
    result.sort(key=lambda x: x["stock_pct"])
    return result

@api.get("/dashboard/categories")
async def get_categories():
    categories = await db.products.distinct("category")
    return ["All"] + sorted(categories)

@api.get("/dashboard/purchase-orders")
async def get_purchase_orders(limit: int = 20):
    pos = await db.purchase_orders.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return pos

# ── Stress Test Routes ───────────────────────────────────────────
@api.post("/stress-test/start")
async def start_stress_test(req: StressTestReq):
    if stress_state["running"]:
        raise HTTPException(400, "Stress test already running")
    asyncio.create_task(execute_stress_test(req.order_count))
    return {"status": "started", "order_count": req.order_count}

@api.get("/stress-test/status")
async def stress_test_status():
    return stress_state

async def execute_stress_test(order_count: int):
    global stress_state
    stress_state = {
        "running": True, "progress": 0, "total": order_count,
        "orders_created": 0, "decisions_made": 0,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None, "results": None
    }

    try:
        # Phase 1: Generate orders rapidly
        for i in range(order_count):
            zone = random.choice(DELIVERY_ZONES)
            products = await db.products.find({}, {"_id": 0}).to_list(500)
            if not products:
                break
            num_items = random.randint(1, 5)
            selected = random.sample(products, min(num_items, len(products)))
            items = [{"product_id": p["product_id"], "product_name": p["name"],
                       "quantity": random.randint(1, 3), "aisle": p["aisle"]} for p in selected]

            order = {
                "order_id": str(uuid.uuid4()),
                "items": items,
                "delivery_zone": zone,
                "status": "pending",
                "priority_score": round(random.uniform(0.5, 1.0), 2),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.orders.insert_one(order)

            # Deplete stock for ordered items
            for it in items:
                await db.products.update_one(
                    {"product_id": it["product_id"], "current_stock": {"$gte": it["quantity"]}},
                    {"$inc": {"current_stock": -it["quantity"]}}
                )

            stress_state["orders_created"] = i + 1
            stress_state["progress"] = round(((i + 1) / order_count) * 50)  # First half: order creation

            if i % 5 == 0:
                await asyncio.sleep(0.1)  # Small delay to not overwhelm

        # Phase 2: Run agents to process the flood
        for cycle in range(5):
            inv_decisions = await run_inventory_agent()
            disp_decisions = await run_dispatch_agent()
            stress_state["decisions_made"] += len(inv_decisions) + len(disp_decisions)
            stress_state["progress"] = 50 + round(((cycle + 1) / 5) * 50)
            await asyncio.sleep(1)

        # Calculate results
        total = await db.orders.count_documents({})
        active = await db.orders.count_documents({"status": {"$in": ["pending", "batched", "picking", "dispatched"]}})
        delivered = await db.orders.count_documents({"status": "delivered"})
        failed = await db.orders.count_documents({"status": "failed"})
        pos = await db.purchase_orders.count_documents({"status": "generated"})

        stress_state["results"] = {
            "total_orders": total,
            "orders_processed": delivered + failed,
            "orders_still_active": active,
            "success_rate": round((delivered / max(1, delivered + failed)) * 100, 1),
            "purchase_orders_generated": pos,
            "agent_decisions": stress_state["decisions_made"],
            "duration_seconds": round((datetime.now(timezone.utc) - datetime.fromisoformat(stress_state["start_time"])).total_seconds(), 1)
        }
    except Exception as e:
        logger.error(f"Stress test error: {e}")
        stress_state["results"] = {"error": str(e)}
    finally:
        stress_state["running"] = False
        stress_state["progress"] = 100
        stress_state["end_time"] = datetime.now(timezone.utc).isoformat()

# ── Orders Route ─────────────────────────────────────────────────
@api.get("/orders")
async def get_orders(status: Optional[str] = None, limit: int = 50):
    query = {}
    if status:
        query["status"] = status
    orders = await db.orders.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return orders

@api.post("/orders/create")
async def create_order():
    """Create a single random order for testing."""
    products = await db.products.find({}, {"_id": 0}).to_list(500)
    if not products:
        raise HTTPException(400, "No products available")
    num_items = random.randint(1, 4)
    selected = random.sample(products, min(num_items, len(products)))
    items = [{"product_id": p["product_id"], "product_name": p["name"],
               "quantity": random.randint(1, 3), "aisle": p["aisle"]} for p in selected]
    order = {
        "order_id": str(uuid.uuid4()),
        "items": items,
        "delivery_zone": random.choice(DELIVERY_ZONES),
        "status": "pending",
        "priority_score": round(random.uniform(0.5, 1.0), 2),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.orders.insert_one(order)
    for it in items:
        await db.products.update_one(
            {"product_id": it["product_id"], "current_stock": {"$gte": it["quantity"]}},
            {"$inc": {"current_stock": -it["quantity"]}}
        )
    return {"order_id": order["order_id"], "items": len(items), "zone": order["delivery_zone"]}

# ── Manual Agent Trigger ─────────────────────────────────────────
@api.post("/agents/run")
async def run_agents_manual():
    inv = await run_inventory_agent()
    disp = await run_dispatch_agent()
    return {"inventory_decisions": len(inv), "dispatch_decisions": len(disp)}

# ── Health ───────────────────────────────────────────────────────
@api.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# ── Include Router & CORS ────────────────────────────────────────
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Background Agent Loop ────────────────────────────────────────
agent_task = None

async def agent_loop():
    """Run agents periodically."""
    await asyncio.sleep(10)  # Initial delay
    while True:
        try:
            await simulate_stock_depletion()
            await fulfill_purchase_orders()
            await run_inventory_agent()
            await run_dispatch_agent()
        except Exception as e:
            logger.error(f"Agent loop error: {e}")
        interval = 15 if stress_state["running"] else 30
        await asyncio.sleep(interval)

@app.on_event("startup")
async def startup():
    global agent_task
    logger.info("Starting DarkStore Agentic Backend...")
    await seed_data()
    agent_task = asyncio.create_task(agent_loop())
    logger.info("Agent loop started")

@app.on_event("shutdown")
async def shutdown():
    global agent_task
    if agent_task:
        agent_task.cancel()
    client.close()
