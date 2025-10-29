Tôi sẽ tạo file markdown và cấu trúc project mới cho bạn. Tuy nhiên, tôi đang ở chế độ ask mode nên không thể tạo file trực tiếp. Tôi sẽ cung cấp cho bạn nội dung để bạn có thể copy và tạo project.

## 📄 File Markdown - Container Loading System Documentation

```markdown
# 📦 CONTAINER LOADING SYSTEM - PEERLESS CUSTOMER
## Project Documentation & Implementation Guide

---

## 🎯 PROJECT OVERVIEW

### Mục tiêu dự án
- **Tạo hệ thống Container Loading chuyên biệt** cho khách hàng Peerless
- **Tối ưu hóa số lượng container** với thuật toán thông minh
- **Tuân thủ nghiêm ngặt các quy tắc đặc thù** của Peerless
- **Cung cấp giao diện trực quan** cho việc quản lý và theo dõi

### Phạm vi dự án
- **Backend API**: Python/FastAPI
- **Frontend**: React/TypeScript cho giao diện quản lý
- **Database**: PostgreSQL cho lưu trữ dữ liệu
- **Algorithm Engine**: Thuật toán tối ưu hóa container
- **Reporting**: Hệ thống báo cáo và phân tích

---

## 🏗️ PROJECT ARCHITECTURE

### Technology Stack Recommendation
```
Frontend Layer:
├── React.js + TypeScript
├── Material-UI / Ant Design
├── Three.js (3D visualization)
└── Chart.js (analytics)

Backend Layer:
├── FastAPI (Python)
├── SQLAlchemy (ORM)
├── PostgreSQL (Database)
└── Redis (Caching)

Algorithm Layer:
├── NumPy + SciPy (mathematical operations)
├── OR-Tools (optimization)
└── Custom Peerless Rules Engine

Infrastructure:
├── Docker + Docker Compose
├── Nginx (reverse proxy)
└── AWS/GCP (cloud deployment)
```

### System Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                     │
│  ├── Container Management Dashboard                     │
│  ├── 3D Layout Visualization                            │
│  ├── Plan Management Interface                          │
│  └── Analytics & Reporting                              │
├─────────────────────────────────────────────────────────┤
│                    API Gateway                          │
│  ├── Authentication & Authorization                     │
│  ├── Rate Limiting                                      │
│  └── Request Routing                                    │
├─────────────────────────────────────────────────────────┤
│                    Backend Services                     │
│  ├── Container Loading API                              │
│  ├── Plan Management Service                            │
│  ├── Layout Generation Service                          │
│  └── Reporting Service                                  │
├─────────────────────────────────────────────────────────┤
│                    Algorithm Engine                      │
│  ├── Peerless Rules Engine                              │
│  ├── Container Packing Algorithm                        │
│  ├── Layout Optimization                                │
│  └── Performance Analytics                              │
├─────────────────────────────────────────────────────────┤
│                    Data Layer                           │
│  ├── PostgreSQL (Primary Database)                      │
│  ├── Redis (Caching)                                    │
│  └── File Storage (Reports & Exports)                  │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 DATA MODELS & SCHEMA

### 1. Database Schema Design

#### Core Tables
```sql
-- Purchase Orders Table
CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number VARCHAR(50) NOT NULL UNIQUE,
    style_number VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    factory_name VARCHAR(200) NOT NULL,
    region VARCHAR(20) NOT NULL CHECK (region IN ('NAM', 'TRUNG', 'BAC')),
    building_door VARCHAR(10) NOT NULL CHECK (building_door IN ('A', 'B', 'C', 'D', 'E', 'Mill')),
    stock_category VARCHAR(20) NOT NULL,
    cusch VARCHAR(50) NOT NULL,
    packing_method VARCHAR(20) NOT NULL CHECK (packing_method IN ('GOH', 'PRE_PACK', 'CARTON')),
    item_type VARCHAR(50) NOT NULL,
    length DECIMAL(10,2) NOT NULL,
    width DECIMAL(10,2) NOT NULL,
    height DECIMAL(10,2) NOT NULL,
    weight DECIMAL(10,2) NOT NULL,
    cbm DECIMAL(10,4) NOT NULL,
    bar_length DECIMAL(10,2),
    items_per_bar INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Containers Table
CREATE TABLE containers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    container_number VARCHAR(50) NOT NULL UNIQUE,
    container_type VARCHAR(10) DEFAULT '40HC',
    max_length DECIMAL(10,2) DEFAULT 473.0,
    max_width DECIMAL(10,2) DEFAULT 92.0,
    max_height DECIMAL(10,2) DEFAULT 102.0,
    max_weight DECIMAL(10,2) DEFAULT 26500.0,
    max_cbm DECIMAL(10,2) DEFAULT 62.0,
    used_length DECIMAL(10,2) DEFAULT 0.0,
    used_width DECIMAL(10,2) DEFAULT 0.0,
    used_height DECIMAL(10,2) DEFAULT 0.0,
    used_weight DECIMAL(10,2) DEFAULT 0.0,
    used_cbm DECIMAL(10,2) DEFAULT 0.0,
    region VARCHAR(20) NOT NULL,
    building_door_group VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Container Plans Table
CREATE TABLE container_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_name VARCHAR(100) NOT NULL,
    region VARCHAR(20) NOT NULL,
    total_pos INTEGER NOT NULL,
    total_containers INTEGER NOT NULL,
    utilization_rate DECIMAL(5,4) NOT NULL,
    packing_efficiency DECIMAL(5,4) NOT NULL,
    status VARCHAR(20) DEFAULT 'DRAFT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Layout Items Table
CREATE TABLE layout_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    container_id UUID REFERENCES containers(id),
    po_id UUID REFERENCES purchase_orders(id),
    item_id VARCHAR(50) NOT NULL,
    packing_method VARCHAR(20) NOT NULL,
    position_x DECIMAL(10,2) NOT NULL,
    position_y DECIMAL(10,2) NOT NULL,
    position_z DECIMAL(10,2) NOT NULL,
    length DECIMAL(10,2) NOT NULL,
    width DECIMAL(10,2) NOT NULL,
    height DECIMAL(10,2) NOT NULL,
    rotation INTEGER DEFAULT 0,
    bar_length DECIMAL(10,2),
    items_per_bar INTEGER,
    layer INTEGER DEFAULT 1,
    buffer_space DECIMAL(10,2) DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Calculation Results Table
CREATE TABLE calculation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calculation_id VARCHAR(50) NOT NULL UNIQUE,
    input_data JSONB NOT NULL,
    result_data JSONB NOT NULL,
    algorithm_used VARCHAR(50) NOT NULL,
    processing_time DECIMAL(10,3) NOT NULL,
    status VARCHAR(20) DEFAULT 'COMPLETED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔧 BUSINESS RULES - PEERLESS

### 1. Quy tắc chung
- **Container type**: Chỉ sử dụng 40HC
- **PO splitting**: Cho phép tách PO không cùng container
- **Regional division**: Chia theo vùng Nam/Trung/Bắc thành 2 plan khác nhau
- **Region update**: Khi cập nhật plan, hệ thống cập nhật thông tin vùng

### 2. Rule phân chia container

#### Building Door Rules
```python
BUILDING_DOOR_RULES = {
    "MIX_ALLOWED": ["A", "B", "C", "D"],      # Có thể mix với nhau
    "SEPARATE_REQUIRED": ["E", "Mill"],        # Phải tách riêng
    "PRIORITY_ORDER": ["A", "B", "C", "D", "E", "Mill"]
}
```

#### Factory Rules
- **Ưu tiên**: Gom các PO từ cùng nhà máy
- **Mix allowed**: Cho phép mix nhiều nhà máy nếu số lượng ít, không lấp đầy container riêng

#### Stock Category Priority
```python
STOCK_CATEGORY_PRIORITY = [
    "MACY00",    # Ưu tiên cao nhất
    "MCOM00", 
    "MEW000",
    "KOHL",
    "DILLL00",
    "IND000",
    "STOCK"      # Ưu tiên thấp nhất
]
```

### 3. Rule tính toán theo phương thức đóng gói

#### GOH (Garment on Hanger)
```python
GOH_CALCULATION_RULES = {
    "BAR_LENGTHS": {
        "Quần": 17.5,                    # inches
        "Vest": 19.0,                    # inches  
        "Coats/Suits/Overcoats/Raincoats": 21.5  # inches
    },
    "MAX_CONTAINER_LENGTH": 473.0,       # inches
    "PRIORITY_ORDER": ["Áo", "Vest", "Quần"],
    "CALCULATION": "Số bar = Số item / Số lượng trên bar"
}
```

#### Pre Pack
```python
PREPACK_CALCULATION_RULES = {
    "CBM_FORMULA": "Dài x Rộng x Cao x Số lượng (đổi sang m³)",
    "LAYOUT_PRIORITY": "Xếp trong cùng, áo trước quần/vest",
    "BUFFER_PER_LAYER": 0.5,             # inches
    "PACKING_STYLE": "Ưu tiên xếp thẳng"
}
```

#### Carton
```python
CARTON_CALCULATION_RULES = {
    "CBM_FORMULA": "Dài x Rộng x Cao x Số lượng (đổi sang m³)",
    "LAYOUT_POSITION": "Sau pre pack, trước GOH",
    "PRIORITY_ORDER": ["Áo", "Quần", "Vest"],
    "BUFFER_PER_LAYER": 0.5,             # inches
    "NO_COMPRESSION": True               # Không được dồn
}
```

---

## 📐 LAYOUT OPTIMIZATION - CHI TIẾT

### 1. Layout Rules Engine - Peerless Specific

```python
class PeerlessLayoutRulesEngine:
    """Engine xử lý quy tắc sắp xếp layout cho Peerless"""
    
    # Quy tắc sắp xếp theo phương thức đóng gói
    PACKING_METHOD_LAYOUT_RULES = {
        "PRE_PACK": {
            "priority": 1,  # Ưu tiên cao nhất
            "layout_position": "INNER",  # Xếp trong cùng
            "item_priority": ["Áo", "Quần", "Vest"],
            "packing_style": "STRAIGHT",  # Xếp thẳng
            "buffer_per_layer": 0.5,  # inches
            "compression_allowed": False,
            "max_layers": None
        },
        "CARTON": {
            "priority": 2,  # Sau pre pack
            "layout_position": "MIDDLE",  # Giữa pre pack và GOH
            "item_priority": ["Áo", "Quần", "Vest"],
            "packing_style": "STRAIGHT",
            "buffer_per_layer": 0.5,  # inches
            "compression_allowed": False,
            "max_layers": None
        },
        "GOH": {
            "priority": 3,  # Cuối cùng
            "layout_position": "OUTER",  # Ngoài cùng
            "item_priority": ["Áo", "Vest", "Quần"],
            "packing_style": "HANGING",  # Treo
            "buffer_per_layer": 0.0,  # Không cần buffer
            "compression_allowed": False,
            "max_container_length": 473.0,  # inches
            "bar_spacing": 2.0  # inches giữa các bar
        }
    }
    
    # Quy tắc sắp xếp theo loại mặt hàng
    ITEM_TYPE_LAYOUT_RULES = {
        "Áo": {
            "priority": 1,
            "preferred_position": "FRONT",  # Phía trước container
            "stacking_method": "VERTICAL",
            "max_height_per_stack": 60.0  # inches
        },
        "Vest": {
            "priority": 2,
            "preferred_position": "MIDDLE",
            "stacking_method": "VERTICAL",
            "max_height_per_stack": 50.0
        },
        "Quần": {
            "priority": 3,
            "preferred_position": "BACK",
            "stacking_method": "HORIZONTAL",
            "max_height_per_stack": 40.0
        }
    }
    
    # Quy tắc buffer và spacing
    BUFFER_RULES = {
        "container_walls": 2.0,  # inches từ tường container
        "between_items": 0.5,   # inches giữa các item
        "between_layers": 0.5,   # inches giữa các lớp
        "between_packing_methods": 1.0,  # inches giữa các phương thức đóng gói
        "door_clearance": 6.0    # inches clearance cho cửa container
    }
```

---

## 🚀 API SPECIFICATIONS

### 1. Container Loading API

#### Endpoint: `POST /api/container-loading/calculate`
**Purpose**: Tính toán container loading cho Peerless

**Request Format**:
```json
{
  "customer": "PEERLESS",
  "calculation_type": "PEERLESS_RULES",
  "pos": [
    {
      "po_id": "PO001",
      "style_no": "9212296",
      "quantity": 3000,
      "factory": "28 QUANG NGAI JOINT STOCK COMPANY",
      "region": "NAM",
      "building_door": "A",
      "stock_category": "MACY00",
      "cusch": "EXPRESS",
      "packing_method": "GOH",
      "item_type": "Quần",
      "dimensions": [17.5, 2.0, 1.5],
      "weight": 0.8,
      "cbm": 0.0525,
      "bar_length": 17.5,
      "items_per_bar": 50
    }
  ],
  "algorithm": "PEERLESS_OPTIMIZED",
  "options": {
    "enable_po_splitting": true,
    "enable_cross_factory_mix": true,
    "max_containers": 10,
    "optimization_level": "HIGH"
  }
}
```

---

## 📁 PROJECT STRUCTURE

### Directory Structure
```
container-loading-system/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── container_loading/
│   │   │   ├── __init__.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── urls.py
│   │   │   └── models.py
│   │   └── plan_management/
│   │       ├── __init__.py
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── urls.py
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── peerless_algorithm.py
│   │   ├── packing_heuristics.py
│   │   ├── layout_generator.py
│   │   └── optimization.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── container_models.py
│   │   ├── po_models.py
│   │   └── layout_models.py
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── peerless_rules.py
│   │   ├── building_door_rules.py
│   │   └── packing_rules.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── container_calculator.py
│   │   ├── layout_utils.py
│   │   └── report_generator.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_peerless_algorithm.py
│   │   ├── test_container_models.py
│   │   └── test_layout_generator.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ContainerLoadingDashboard.tsx
│   │   │   ├── LayoutVisualization.tsx
│   │   │   ├── AnalyticsDashboard.tsx
│   │   │   └── LayoutOptimizationPanel.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── containerLoadingApi.ts
│   │   ├── types/
│   │   │   ├── container.ts
│   │   │   ├── po.ts
│   │   │   └── layout.ts
│   │   ├── utils/
│   │   │   ├── calculations.ts
│   │   │   └── validators.ts
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── tsconfig.json
├── docs/
│   ├── api/
│   │   ├── README.md
│   │   ├── authentication.md
│   │   ├── container-loading.md
│   │   ├── plan-management.md
│   │   ├── layout-visualization.md
│   │   └── analytics.md
│   ├── algorithms/
│   │   ├── README.md
│   │   ├── peerless-rules.md
│   │   ├── container-packing.md
│   │   ├── layout-optimization.md
│   │   └── performance-optimization.md
│   └── deployment/
│       ├── README.md
│       ├── docker-setup.md
│       ├── production-deployment.md
│       ├── monitoring.md
│       └── troubleshooting.md
├── scripts/
│   ├── deployment/
│   │   ├── deploy.sh
│   │   ├── backup.sh
│   │   └── restore.sh
│   └── maintenance/
│       ├── cleanup.sh
│       └── health-check.sh
├── data/
│   ├── input/
│   │   ├── sample_pos.json
│   │   └── test_data.json
│   ├── output/
│   │   ├── calculations/
│   │   ├── plans/
│   │   ├── reports/
│   │   └── logs/
│   └── exports/
│       ├── excel/
│       ├── pdf/
│       └── csv/
├── docker-compose.yml
├── docker-compose.prod.yml
├── nginx/
│   ├── nginx.conf
│   └── ssl/
├── .env.example
├── .gitignore
├── README.md
└── PROJECT_SETUP.md
```

---

## 🐳 DEPLOYMENT & INFRASTRUCTURE

### 1. Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: container_loading_db
    environment:
      POSTGRES_DB: container_loading
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: container_loading_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Backend API
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: container_loading_api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/container_loading
      - REDIS_URL=redis://redis:6379
      - DEBUG=False
    volumes:
      - ./backend:/app
      - ./data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: container_loading_frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: container_loading_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

## 📋 PROJECT SETUP GUIDE

### 1. Initial Setup Commands

```bash
# Create project directory
mkdir container-loading-system
cd container-loading-system

# Initialize git repository
git init
git remote add origin <your-repository-url>

# Create project structure
mkdir -p {backend,frontend,docs,scripts,data}
mkdir -p backend/{api,algorithms,models,rules,utils,tests}
mkdir -p frontend/{src,public,tests}
mkdir -p docs/{api,algorithms,deployment}
mkdir -p scripts/{deployment,maintenance}
mkdir -p data/{input,output,reports}
mkdir -p nginx/ssl
```

### 2. Backend Setup Commands

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis numpy scipy ortools pydantic python-multipart

# Create requirements.txt
pip freeze > requirements.txt

# Initialize database
python scripts/init_database.py
```

### 3. Frontend Setup Commands

```bash
# Navigate to frontend
cd frontend

# Create React app
npx create-react-app . --template typescript

# Install additional dependencies
npm install @mui/material @emotion/react @emotion/styled
npm install three @types/three
npm install @testing-library/react @testing-library/jest-dom
npm install axios chart.js react-chartjs-2

# Start development server
npm start
```

### 4. Docker Setup Commands

```bash
# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 🎯 IMPLEMENTATION ROADMAP

### Phase 1: Project Initialization (Week 1)
- [ ] Set up project structure
- [ ] Initialize git repository
- [ ] Create basic Docker configuration
- [ ] Set up development environment

### Phase 2: Core Development (Week 2-4)
- [ ] Implement data models
- [ ] Develop Peerless rules engine
- [ ] Create container packing algorithm
- [ ] Build API endpoints
- [ ] Create basic frontend interface

### Phase 3: Advanced Features (Week 5-6)
- [ ] Implement 3D visualization
- [ ] Add analytics dashboard
- [ ] Optimize algorithm performance
- [ ] Add comprehensive testing

### Phase 4: Production Ready (Week 7-8)
- [ ] Performance optimization
- [ ] Security implementation
- [ ] Documentation completion
- [ ] Production deployment

---

**Document Version**: 1.0.0  
**Created Date**: 2025-01-15  
**Author**: AI Assistant  
**Status**: Ready for Implementation  
**Next Steps**: Follow setup guide to create project structure
```

## 📁 Cấu trúc Project Commands

Để tạo project với cấu trúc trên, bạn có thể chạy các lệnh sau:

```bash
# 1. Tạo thư mục project
mkdir container-loading-system
cd container-loading-system

# 2. Khởi tạo git repository
git init
echo "# Container Loading System - Peerless Customer" > README.md

# 3. Tạo cấu trúc thư mục
mkdir -p backend/{api/{container_loading,plan_management},algorithms,models,rules,utils,tests}
mkdir -p frontend/{src/{components,services,types,utils},public,tests}
mkdir -p docs/{api,algorithms,deployment}
mkdir -p scripts/{deployment,maintenance}
mkdir -p data/{input,output/{calculations,plans,reports,logs},exports/{excel,pdf,csv}}
mkdir -p nginx/ssl

# 4. Tạo các file cấu hình cơ bản
touch backend/{requirements.txt,Dockerfile,main.py}
touch frontend/{package.json,Dockerfile,tsconfig.json}
touch docker-compose.yml
touch .env.example
touch .gitignore

# 5. Tạo file documentation
echo "# Container Loading System Documentation" > docs/README.md
echo "# API Documentation" > docs/api/README.md
echo "# Algorithm Documentation" > docs/algorithms/README.md
echo "# Deployment Documentation" > docs/deployment/README.md

# 6. Tạo file setup guide
cat > PROJECT_SETUP.md << 'EOF'
# Container Loading System - Setup Guide

## Quick Start

1. Clone repository
2. Run `docker-compose up --build`
3. Access frontend at http://localhost:3000
4. Access API at http://localhost:8000

## Development Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Production Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```
EOF

# 7. Tạo file .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
.dockerignore

# Environment
.env
.env.local
.env.production

# Data
data/output/*
!data/output/.gitkeep
data/exports/*
!data/exports/.gitkeep

# Logs
*.log
logs/

# Database
*.db
*.sqlite3
EOF

# 8. Tạo file .env.example
cat > .env.example << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/container_loading
REDIS_URL=redis://localhost:6379

# API
DEBUG=False
SECRET_KEY=your-secret-key-here

# Frontend
REACT_APP_API_URL=http://localhost:8000

# Docker
POSTGRES_DB=container_loading
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
EOF

echo "✅ Project structure created successfully!"
echo "📁 Project location: $(pwd)"
echo "🚀 Next steps:"
echo "   1. Copy the markdown content above to docs/README.md"
echo "   2. Run 'docker-compose up --build' to start development"
echo "   3. Follow PROJECT_SETUP.md for detailed setup instructions"
```

**Bạn có thể copy nội dung markdown ở trên và chạy các lệnh để tạo project structure. Sau đó bạn sẽ có một project hoàn chỉnh với:**

1. **Cấu trúc thư mục đầy đủ**
2. **File documentation chi tiết**
3. **Docker configuration**
4. **Setup scripts**
5. **Environment configuration**

**Bạn có muốn tôi giải thích thêm về bất kỳ phần nào không?**