# Vibeathon Dark Store - Agentic Backend PRD

## Project Overview
B2B operational architecture for "dark stores" (micro-fulfillment centers) managing 10-minute delivery networks with autonomous agents making logistics decisions.

## Tech Stack
- **Backend:** FastAPI + MongoDB + Python
- **Frontend:** Expo React Native (SDK 54) with React Native SVG
- **Decision Engine:** Rule-based heuristics + predictive analytics
- **Auth:** JWT-based with bcrypt password hashing

## Core Features

### 1. Inventory Agent
- Monitors all 50 product stock levels against reorder points
- Calculates demand velocity (items/hour) and hours to stockout
- Auto-generates B2B purchase orders with detailed reasoning
- Urgency classification: CRITICAL (<2h), HIGH (<4h), MEDIUM
- Simulated PO fulfillment (auto-restocks after 60 seconds)

### 2. Dispatch Agent
- Groups pending orders by delivery zone (10 Bangalore zones)
- Batches orders (max 6 per batch) for efficient fulfillment
- Optimizes picking paths through store aisles (A-G)
- Simulates full delivery lifecycle: pending → batched → picking → dispatched → delivered
- 94% simulated success rate

### 3. B2B Manager Dashboard (4-Tab Mobile App)
- **Live Decision Feed:** Real-time agent decision log with expandable reasoning, filter by agent type, auto-refresh every 5s
- **Chaos Meter:** SVG circular stress gauge (0-100%), 6 operational metric cards, auto-refresh every 4s
- **Stock Heatmap:** Color-coded product grid (critical/low/moderate/healthy), category filters, demand velocity indicators
- **Stress Test Engine:** Configurable 50-200 order volume, real-time progress, detailed results summary

### 4. Simulated High-Volume Engine
- Generates simultaneous orders across all delivery zones
- Agents process flood in accelerated cycles
- Tracks: orders created, agent decisions, success rates, duration

## Data Model
- **Products:** 50 realistic Indian grocery/essentials products across 7 categories
- **Orders:** Items, delivery zones, status lifecycle, priority scoring
- **Purchase Orders:** B2B orders with reasoning, supplier, cost tracking
- **Agent Decisions:** Type, summary, reasoning steps, analysis, confidence score, outcome
- **System Metrics:** Real-time computed from order/product state

## API Endpoints
- `POST /api/auth/login` - Manager authentication
- `GET /api/auth/me` - Current user info
- `GET /api/dashboard/live-feed` - Agent decision stream
- `GET /api/dashboard/metrics` - System health metrics
- `GET /api/dashboard/stock-heatmap` - Product inventory status
- `GET /api/dashboard/categories` - Product categories
- `POST /api/orders/create` - Create test order
- `POST /api/agents/run` - Manual agent trigger
- `POST /api/stress-test/start` - Launch stress test
- `GET /api/stress-test/status` - Stress test progress

## Design
- Dark theme command center (#0A0A0A, #121212)
- Neon accent colors: Blue (#007AFF), Red (#FF3B30), Green (#34C759), Yellow (#FFCC00)
- Tab-based navigation with top header showing LIVE status
- Dense, data-rich layouts optimized for logistics managers

## Credentials
- Manager: manager@darkstore.ai / darkstore2024
