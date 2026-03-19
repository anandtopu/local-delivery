# local-delivery

A GoPuff-inspired local delivery system — built as a **system design practice application** demonstrating production-grade patterns: Haversine geo-filtering, SERIALIZABLE transaction ordering, Redis cache-aside, read/write DB split, and region partitioning.

---

## Architecture

```
React SPA (frontend:3000)
        ↓ /api/*
FastAPI Backend (backend:8000)
        ↓
┌────────────────────────────────┐
│  PostgreSQL (write + read)     │
│  Redis  (availability cache)   │
└────────────────────────────────┘
```
 
---

## Tech Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Backend runtime  | Python 3.11+                        |
| API framework    | FastAPI 0.115                        |
| ORM              | SQLAlchemy 2.0 async + asyncpg      |
| Migrations       | Alembic 1.14                        |
| Cache            | Redis 7 (redis-py asyncio)          |
| Frontend         | React 18 + Vite 6 + TypeScript 5   |
| State            | Zustand 5                           |
| Data fetching    | SWR 2 + Axios                       |
| Styling          | Tailwind CSS 3.4                    |
| Maps             | Leaflet + react-leaflet             |
| Containerization | Docker + Docker Compose             |
| Orchestration    | Kubernetes (Kustomize)              |
| Linting (BE)     | ruff + mypy                         |
| Linting (FE)     | ESLint + Prettier                   |
| Testing (BE)     | pytest + pytest-asyncio             |
| Testing (FE)     | Vitest                              |

---

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env

# 2. Start full stack
make dev

# 3. Apply DB migrations
make migrate

# 4. Seed sample data (50 DCs, 100 items, inventory)
make seed

# 5. Open browser
open http://localhost:3000
open http://localhost:8000/docs
```

---

## API Endpoints

| Method | Path                         | Description                              |
|--------|------------------------------|------------------------------------------|
| GET    | /health                      | Postgres + Redis health check            |
| GET    | /api/v1/availability         | Check item availability by lat/lng       |
| POST   | /api/v1/orders               | Place an order (SERIALIZABLE tx)         |
| GET    | /api/v1/orders               | List orders (paginated)                  |
| GET    | /api/v1/orders/{id}          | Order detail                             |
| GET    | /api/v1/dcs                  | List distribution centers                |
| GET    | /api/v1/dcs/{id}             | DC detail with inventory                 |
| POST   | /api/v1/dcs                  | Create DC                                |
| GET    | /api/v1/items                | List items (filter by category)          |
| GET    | /api/v1/items/{id}           | Item detail                              |
| POST   | /api/v1/items                | Create item                              |
| POST   | /api/v1/admin/seed           | Trigger data seed                        |
| POST   | /api/v1/admin/cache/flush    | Flush availability cache                 |
| GET    | /api/v1/admin/stats          | Aggregate statistics                     |

### Availability query example

```
GET /api/v1/availability?lat=34.0522&lng=-118.2437&item_ids=1,2,3&radius_km=15
```

Response includes `cache_status` (HIT / MISS / PARTIAL) and `response_ms`.

---

## Key Design Decisions

### 1. Haversine Geo-filtering

The `find_nearby_dcs()` function applies a **bounding-box pre-filter** (SQL `BETWEEN` on lat/lng columns) to reduce candidates from the full table, then applies the exact Haversine formula in Python for accurate great-circle distance. This two-pass approach avoids a full table scan while keeping accuracy.

```
1° latitude  ≈ 111 km  (constant)
1° longitude ≈ 111 × cos(lat) km  (varies by latitude)
```

### 2. Redis Cache-aside (TTL 60 s)

Availability reads check `avail:dc:{id}:item:{id}` in Redis first. On miss, PostgreSQL is queried and the result is cached with a 60-second TTL. On every successful order, the affected `(dc_id, item_id)` cache keys are **synchronously invalidated** so the next read gets fresh inventory. If cache invalidation fails (Redis unavailable), the TTL ensures stale data expires within 60 seconds.

### 3. SERIALIZABLE Transaction Ordering

Order placement uses PostgreSQL `SERIALIZABLE` isolation level to prevent phantom reads and write skews that could oversell inventory:

```
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE
→ SELECT ... FOR UPDATE on each inventory row
→ CHECK quantity >= requested
→ INSERT order + order_items
→ UPDATE inventory SET quantity = quantity - requested
→ COMMIT
→ (best effort) invalidate Redis keys
```

If two concurrent transactions conflict, PostgreSQL raises `SerializationFailure` (SQLSTATE 40001), which the API returns as HTTP 409 with a `retry` hint.

### 4. Read/Write DB Split

- `get_write_db()` → primary PostgreSQL (pool_size=10)
- `get_read_db()` → read replica (pool_size=20, pointing at primary in dev)
- Availability checks always use `get_read_db()`
- Order placement always uses `get_write_db()`

In production, set `READ_DATABASE_URL` to a read replica endpoint (e.g., an AWS RDS read replica or a GCP Cloud SQL replica).

### 5. Region Partitioning

```python
region_id = zipcode[:3]
```

Each DC is tagged with the first 3 digits of its ZIP code as its `region_id`. This coarse region key enables future table partitioning (`PARTITION BY LIST (region_id)`) and is indexed alongside `is_active` for fast filtered lookups.

---

## Service URLs (Local Dev)

| Service      | URL                      |
|--------------|--------------------------|
| Dashboard    | http://localhost:3000    |
| API + Swagger| http://localhost:8000/docs |
| PostgreSQL   | localhost:5432           |
| Redis        | localhost:6379           |

---

## Project Structure

```
local-delivery/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI factory + routers + health
│   │   ├── core/config.py       # Pydantic BaseSettings
│   │   ├── db/postgres.py       # Write + read engines, session deps
│   │   ├── db/redis_client.py   # Redis async singleton
│   │   ├── models/orm.py        # SQLAlchemy 2.0 ORM models
│   │   ├── models/schemas.py    # Pydantic v2 request/response schemas
│   │   ├── routers/             # availability, orders, dcs, items, admin
│   │   └── services/            # nearby, cache, availability, orders
│   ├── migrations/              # Alembic env.py + versions/
│   ├── scripts/seed_data.py     # 50 DCs, 100 items, inventory
│   ├── tests/                   # conftest, test_nearby, test_availability, test_orders
│   ├── requirements.txt
│   ├── pyproject.toml           # ruff + mypy config
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               # Dashboard, Availability, Orders, DCs, Items, PlaceOrder
│   │   ├── components/          # layout/, ui/
│   │   ├── services/            # api.ts, availabilityService, ordersService, ...
│   │   ├── hooks/               # useAvailability, useOrders, useDCs, useStats
│   │   ├── store/cartStore.ts   # Zustand cart + location
│   │   └── utils/formatters.ts
│   ├── package.json
│   └── Dockerfile
├── k8s/
│   ├── base/                    # namespace, deployments, services, configmap, ingress
│   └── overlays/dev|staging|prod
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Kubernetes Deployment

```bash
make k8s-deploy-dev       # 1 replica, debug logging
make k8s-deploy-staging   # 2 replicas, info logging
make k8s-deploy-prod      # 3 replicas backend, 2 frontend
```

Namespace: `local-delivery`

---

## Running Tests

```bash
make test-backend         # pytest -v
make test-backend-cov     # with HTML coverage report
make test-frontend        # vitest
make lint                 # ruff + eslint
make type-check           # mypy + tsc
```
