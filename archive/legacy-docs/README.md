# 🚀 AI Pocket CFO - Monorepo

An **integrated AI-powered financial management platform** for small businesses with modular architecture, featuring conversational AI transaction logging, comprehensive REST API, and planned voice interaction capabilities.

**Tech Stack:** FastAPI • Chainlit • Ollama • Supabase • Docker

---

## 📋 Table of Contents

- [Project Structure](#project-structure)
- [Modules](#modules)
- [Quick Start](#quick-start)
- [Docker Deployment](#docker-deployment)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Roadmap](#roadmap)

---

## 📁 Project Structure

```
pocketCFO/
├─ backend/                    # FastAPI Core Module
│  ├─ app/
│  │  ├─ main.py             # FastAPI application entry
│  │  ├─ config.py           # Configuration settings
│  │  ├─ models/             # Pydantic request/response models
│  │  ├─ routes/             # API endpoints
│  │  ├─ services/           # Business logic layer
│  │  └─ utils/              # Utilities (Supabase, export)
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ .env.example
│
├─ chainlit-ui/                # Conversational AI UI Module
│  ├─ app.py                 # Chainlit application
│  ├─ .chainlit/             # UI configuration
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ .env.example
│
├─ voice-module/               # Voice + AI Categorization Module
│  ├─ server.py              # Flask API for parse/categorize/save
│  ├─ parser.py              # Groq-powered transaction parsing
│  ├─ categorizer.py         # Rule + AI categorization logic
│  ├─ index.html             # Voice/text UI
│  ├─ tests/                 # Unit tests
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ README.md
│
├─ docs/                       # Documentation
│  └─ ARCHITECTURE.md
│
├─ docker-compose.yml         # Multi-service orchestration
├─ README.md                  # This file
├─ .env.example              # Environment template
└─ .gitignore

```

---

## 🧩 Modules

### **Module 1: Backend API** (`backend/`)

**FastAPI-based transaction management service**

- ✅ RESTful transaction CRUD operations
- ✅ Advanced filtering, sorting, pagination
- ✅ Full-text search across transactions
- ✅ CSV/PDF export with summaries
- ✅ Supabase PostgreSQL integration
- ✅ Type-safe Pydantic validation
- ✅ Async/await operations
- ✅ Health check & monitoring endpoints

**Runs on:** `http://localhost:8000`

**API Docs:** `http://localhost:8000/docs` (Swagger UI)

### **Module 2: Chainlit UI** (`chainlit-ui/`)

**Natural language conversational transaction logging**

- 🤖 AI-powered transaction extraction from natural language
- 💬 Clean chat-based interface
- 🦙 Ollama LLM integration (llama3.2 by default)
- 💡 Real-time financial insights
- 📊 Transaction history in conversation context
- ⚡ Streaming responses
- 🔄 Fallback regex parsing

**Runs on:** `http://localhost:8001`

**Example:**

```
User: "Spent $500 on office rent"
AI: ✅ Logged: expense | $500 | Rent | 2024-02-27
💡 Your rent is consistent with last month's expense pattern
```

### **Module 3: Voice Module** (`voice-module/`)

**Voice + AI parsing and categorization module**

- 🎙️ Voice/text transaction capture
- 🧠 Groq Llama-powered parser for natural language inputs
- 🏷️ Rule + AI category engine with correction learning
- 💾 Save and query categorized transactions in Supabase
- 📈 Summary endpoints for categories and overall totals

**Runs on:** `http://localhost:5000`

### **Integrated Frontend** (`voice-module/index.html`)

The primary web frontend is served by the voice module and integrates with backend APIs:

- Dashboard: parse text/voice inputs and save transactions
- Categories: spending-by-category chart and category totals
- Transactions: list, filter, pagination, delete, CSV/PDF export
- AI Chat button: opens Chainlit UI (`http://localhost:8001`)

Frontend host: `http://localhost:5000`

---

## 🚀 Quick Start

### Option 1: Run Locally (Manual Setup)

#### Prerequisites

- Python 3.9+
- Ollama (for Chainlit LLM)
- Supabase project with credentials
- Groq API key (for voice module parser)

#### Setup

```bash
# 1. Clone and enter directory
cd pocketCFO

# 2. Copy environment file
cp .env.example .env
# Edit .env with your Supabase credentials

# 3. Terminal 1: Start Backend
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate      # macOS/Linux

pip install -r requirements.txt
python -m uvicorn app.main:app --reload
# → API running at http://localhost:8000
```

```bash
# 4. Terminal 2: Start Ollama (if not running)
ollama pull llama3.2
ollama serve
# → Ollama running at http://localhost:11434
```

```bash
# 5. Terminal 3: Start Chainlit UI
cd chainlit-ui
python -m venv venv
source venv/Scripts/activate

pip install -r requirements.txt
chainlit run app.py
# → UI running at http://localhost:8001
```

```bash
# 6. Terminal 4: Start Voice Module
cd voice-module
python -m venv venv
source venv/Scripts/activate

pip install -r requirements.txt
python server.py
# → Voice module API running at http://localhost:5000
```

### Option 2: Docker Compose (Recommended)

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your credentials

# 2. Build and start all services
docker-compose up --build

# 3. Access services
# Backend API: http://localhost:8000
# Backend docs: http://localhost:8000/docs
# Chainlit UI: http://localhost:8001
# Ollama: http://localhost:11434
```

### Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs

# Test transaction creation
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Test expense",
    "amount": "50.00",
    "type": "expense",
    "category": "Testing",
    "transaction_date": "2024-02-27",
    "is_personal": false
  }'
```

---

## 🐳 Docker Deployment

The `docker-compose.yml` orchestrates 4 services:

| Service          | Port  | Role                  |
| ---------------- | ----- | --------------------- |
| **backend**      | 8000  | FastAPI API server    |
| **chainlit**     | 8001  | Conversational UI     |
| **voice-module** | 5000  | Voice + AI parser API |
| **ollama**       | 11434 | LLM inference engine  |

### Build Custom Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build chainlit
docker-compose build voice-module
```

### Start Services

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f  [service-name]

# Stop services
docker-compose down
```

### Environment Variables (docker-compose.yml)

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SECRET_KEY=your-secret-key

# Optional
DEBUG=false
OLLAMA_URL=http://ollama:11434/api/generate
OLLAMA_MODEL=llama3.2
GROQ_API_KEY=your-groq-api-key
```

---

## 📡 API Documentation

### Base URL

```
http://localhost:8000/transactions
```

### Endpoints

#### List Transactions

```http
GET /transactions?page=1&page_size=10&sort_by=transaction_date&order=desc
```

**Query Parameters:**

- `search` - Search keyword (description, category)
- `category` - Filter by category
- `type` - Filter by type: `income` or `expense`
- `start_date` - Start date (YYYY-MM-DD)
- `end_date` - End date (YYYY-MM-DD)
- `sort_by` - Sort field: `transaction_date`, `amount`, `category`, `is_personal`
- `order` - Sort order: `asc` or `desc`
- `page` - Page number (1-indexed, default: 1)
- `page_size` - Results per page (default: 10, max: 100)

**Example:**

```bash
curl "http://localhost:8000/transactions?type=expense&sort_by=amount&order=desc&page=1&page_size=5"
```

#### Get Single Transaction

```http
GET /transactions/{id}
```

#### Create Transaction

```http
POST /transactions
Content-Type: application/json

{
  "description": "Office supplies purchase",
  "amount": "150.50",
  "type": "expense",
  "category": "Supplies",
  "transaction_date": "2024-02-27",
  "is_personal": false
}
```

#### Update Transaction

```http
PUT /transactions/{id}
Content-Type: application/json

{
  "amount": "175.50",
  "category": "Equipment"
}
```

#### Delete Transaction

```http
DELETE /transactions/{id}
```

#### Export CSV

```http
GET /transactions/export/csv?category=Supplies&start_date=2024-01-01
```

Returns: CSV file download

#### Export PDF

```http
GET /transactions/export/pdf?type=expense&start_date=2024-01-01
```

Returns: PDF report with summary

### Response Format

**Success:**

```json
{
  "success": true,
  "data": [...],
  "message": "Operation successful"
}
```

**Error:**

```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE"
}
```

---

## 🛠️ Development

### Backend Development

```bash
cd backend

# Activate virtual environment
source venv/Scripts/activate  # Windows
source venv/bin/activate      # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
python -m uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black app/
flake8 app/
```

### Chainlit Development

```bash
cd chainlit-ui

# Activate virtual environment
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
chainlit run app.py

# Debug mode
chainlit run app.py --debug
```

### Adding Dependencies

```bash
# Backend
cd backend
pip install <package>
pip freeze > requirements.txt

# Chainlit
cd chainlit-ui
pip install <package>
pip freeze > requirements.txt
```

---

## 📊 Database Schema

### Transactions Table

```sql
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  description TEXT NOT NULL,
  amount NUMERIC(12, 2) NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
  category TEXT NOT NULL,
  transaction_date DATE NOT NULL,
  is_personal BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX transactions_user_id_idx ON transactions(user_id);
CREATE INDEX transactions_date_idx ON transactions(transaction_date);
CREATE INDEX transactions_category_idx ON transactions(category);
```

---

## 🛣️ Roadmap

### ✅ Phase 1: Core (Complete)

- [x] FastAPI backend with CRUD
- [x] Supabase PostgreSQL integration
- [x] Advanced filtering, sorting, pagination
- [x] CSV/PDF export
- [x] Chainlit conversational UI
- [x] Ollama LLM integration
- [x] Real-time financial insights

### ✅ Phase 2: Voice Module (Integrated)

- [x] Voice/text module extracted from `module2-voice` branch
- [x] Groq-powered parsing API (`/parse`)
- [x] Categorization API (`/categorize`, `/correct-category`)
- [x] Summary and transaction endpoints
- [x] Docker integration and module-level docs

### 📋 Phase 3: Enhancements (Planned)

- [ ] Dashboard with charts/analytics
- [ ] Multi-user teams support
- [ ] Receipt scanning (OCR)
- [ ] Bank account integration
- [ ] Budget tracking & alerts
- [ ] Tax category recommendations
- [ ] Multi-currency support
- [ ] iOS/Android apps

---

## 🔐 Security Notes

⚠️ **Important for Production:**

1. **JWT Authentication** - Implement proper token extraction and validation
2. **CORS** - Restrict origins to specific domains
3. **HTTPS** - Use HTTPS only in production
4. **Environment Variables** - Never commit real secrets; use `.env` files
5. **Rate Limiting** - Add rate limiting for API endpoints
6. **Input Validation** - All inputs are validated with Pydantic
7. **SQL Injection** - Protected through parameterized queries

---

## 📝 Configuration Files

### .env.example

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# JWT Configuration
SECRET_KEY=your-secret-key-change-in-production

# Application Configuration
DEBUG=false
LOG_LEVEL=info

# Ollama Configuration
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2
```

### Docker Configuration

- `Dockerfile` - Backend containerization
- `chainlit-ui/Dockerfile` - Chainlit containerization
- `docker-compose.yml` - Multi-service orchestration

---

## 📚 Related Documentation

- **API Docs** - `http://localhost:8000/docs` (Swagger UI)
- **Chainlit Docs** - [chainlit.io](https://chainlit.io/)
- **Ollama Docs** - [ollama.ai](https://ollama.ai/)
- **Supabase Docs** - [supabase.com/docs](https://supabase.com/docs)
- **FastAPI Docs** - [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)

---

## 🆘 Troubleshooting

### Backend won't start

```bash
# Check Supabase credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test API health
curl http://localhost:8000/health
```

### Chainlit not connecting to API

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check Chainlit logs
docker-compose logs chainlit

# Restart services
docker-compose restart
```

### Ollama not responding

```bash
# Check if Ollama is running
curl http://localhost:11434

# Pull model
ollama pull llama3.2

# Start Ollama service
docker-compose restart ollama
```

---

## 🤝 Contributing

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit changes (`git commit -m 'Add amazing feature'`)
3. Push to branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

Built with ❤️ for small business financial freedom.

- **FastAPI** - Modern, fast Python web framework
- **Chainlit** - Rapid LLM app development
- **Ollama** - Local LLM inference
- **Supabase** - Open-source Firebase alternative
- **Docker** - Container orchestration

---

**Questions?** Open an issue or check the [docs](./docs/)
