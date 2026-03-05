# AI Pocket CFO - Complete Financial Management System

An **AI-powered financial management platform** for small businesses, featuring conversational transaction logging, comprehensive API-based management, and future voice interaction capabilities. Built with **FastAPI**, **Chainlit**, **Ollama AI**, **Supabase**, and **Python**.

---

## 🌟 System Overview

**AI Pocket CFO** is an integrated multi-module system designed to revolutionize small business financial tracking through:

- 🤖 **Natural Language Processing** - Log transactions using conversational AI
- 📊 **Comprehensive API** - Full-featured REST API for transaction management
- 🎙️ **Voice Interface** (Coming Soon) - Voice-powered transaction entry
- 💡 **AI Insights** - Real-time financial recommendations powered by Ollama

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Pocket CFO System                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐   ┌─────────────────────────────┐    │
│  │  Module 1        │   │  Chainlit AI Interface      │    │
│  │  pocketCFO       │   │  (pocket-cfo-chainlit)      │    │
│  │  FastAPI Backend │◄──┤  - Conversational UI        │    │
│  │                  │   │  - Ollama LLM (llama3.2)    │    │
│  │  - REST API      │   │  - Natural language logging │    │
│  │  - CRUD Ops      │   │  - Real-time insights       │    │
│  │  - CSV/PDF Export│   └─────────────────────────────┘    │
│  │  - Filters/Search│                                       │
│  └────────┬─────────┘   ┌─────────────────────────────┐    │
│           │             │  Module 2 (Future)          │    │
│           │             │  pocketCFO-module2-voice    │    │
│           │             │  - Voice recognition        │    │
│           │             │  - Hands-free logging       │    │
│           │             │  - Voice commands           │    │
│           │             └─────────────────────────────┘    │
│           │                                                 │
│           ▼                                                 │
│  ┌────────────────────────────────────────────────┐        │
│  │         Supabase PostgreSQL Database           │        │
│  │  - Transactions storage                        │        │
│  │  - User authentication                         │        │
│  │  - Row-level security                          │        │
│  └────────────────────────────────────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Modules

### **Module 1: pocketCFO (Core Backend)**

_This Repository_ - FastAPI-based transaction management API

**Features:**
✅ **View Transactions** - Paginated list of all transactions  
✅ **Search** - Search by keyword across description and category  
✅ **Filter** - By category, type (income/expense), and date range  
✅ **Sort** - By date, amount, or category  
✅ **CRUD Operations** - Create, read, update, delete transactions  
✅ **Personal Expense Warning** - Flag suspicious personal expenses  
✅ **Export to CSV** - Download transaction data as CSV  
✅ **Export to PDF** - Generate formatted report with summary  
✅ **Clean Error Handling** - Comprehensive error responses  
✅ **Type Safety** - Full Pydantic validation  
✅ **Async/Await** - Fast, non-blocking operations  
✅ **SQL Injection Safe** - Parameterized queries

### **Chainlit AI Interface: pocket-cfo-chainlit**

_Conversational Transaction Logging_

**Features:**
🤖 **Natural Language Processing** - "Spent $500 on rent" → Structured transaction  
💬 **Chainlit UI** - Clean, chat-based interface  
🦙 **Ollama Integration** - Local LLM (llama3.2) for transaction extraction  
💡 **AI Insights** - Real-time financial tips based on spending patterns  
📊 **Transaction History** - View last N transactions in conversation  
⚡ **Stream Responses** - Real-time streaming AI insights  
🔄 **Fallback Parsing** - Regex-based extraction if AI unavailable

**Tech Stack:**

- Chainlit (Conversational UI framework)
- Ollama (Local LLM inference)
- Supabase Python Client
- Async/await for performance

### **Module 2: pocketCFO-module2-voice**

_Voice Interaction Module_

**Current Status:** In Development (branch: `module2-voice`)

**Planned Features:**
🎙️ Voice-activated transaction logging  
🗣️ Speech-to-text conversion via STT models  
🔊 Voice command processing and NLU  
📱 Mobile-friendly voice interface  
🎧 Real-time voice feedback  
🌐 Multi-language support

**Repository:** Same as pocketCFO, branch `module2-voice`  
**Integration Point:** Uses same Supabase backend as Module 1

---

## 🚀 Quick Start Guide

### Option 1: API-Based Usage (Direct REST API)

Best for: Integrations, mobile apps, custom frontends

```bash
# Start the FastAPI backend
cd pocketCFO
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Access at: `http://localhost:8000`  
API Docs: `http://localhost:8000/docs`

### Option 2: Conversational AI Interface

Best for: Quick transaction logging, natural language interaction

```bash
# Terminal 1: Start FastAPI backend (as above)
cd pocketCFO
python -m uvicorn app.main:app --reload

# Terminal 2: Start Ollama (if not running)
# Download from https://ollama.ai
ollama pull llama3.2

# Terminal 3: Start Chainlit interface
cd pocket-cfo-chainlit
pip install chainlit supabase requests
chainlit run app.py
```

Access at: `http://localhost:8001`

**Example Conversation:**

```
User: "Spent $500 on office rent today"
AI: ✅ Logged: expense | 500 | Rent
💡 Insights: Your rent is consistent with last month...
```

### Option 3: Full System (API + AI Interface)

Run both FastAPI backend and Chainlit interface simultaneously for maximum flexibility.

---

## 🔗 Integration Patterns

### Database Schema (Shared)

Both modules share the same Supabase database:

- **pocketCFO** uses table: `transactions`
- **pocket-cfo-chainlit** uses table: `transactions_ai`

_Note: You can configure both to use the same table for unified data access_

### Environment Configuration

Create `.env` files in both directories:

**pocketCFO/.env:**

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SECRET_KEY=your-jwt-secret
```

**pocket-cfo-chainlit/.env:**

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2
```

---

## Project Structure

```
app/
├── main.py                          # FastAPI entry point
├── routes/
│   └── transactions.py             # Transaction endpoints
├── services/
│   └── transaction_service.py      # Business logic
├── models/
│   └── transaction_models.py       # Pydantic models
└── utils/
    ├── supabase_client.py          # Database client
    └── export_utils.py             # CSV/PDF generation
```

## Installation

### Prerequisites

- Python 3.9+
- Supabase project (with PostgreSQL database)

### Setup

1. **Clone/Create Project**

```bash
cd "module 4"
```

2. **Create Virtual Environment**

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate      # macOS/Linux
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure Environment**

```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SECRET_KEY=your-jwt-secret
```

5. **Database Setup**

Run this in Supabase SQL Editor to create the transactions table:

```sql
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  description TEXT NOT NULL,
  amount NUMERIC(12, 2) NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
  category TEXT NOT NULL,
  transaction_date DATE NOT NULL,
  is_personal BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(id)
);

-- Create index for user_id for faster queries
CREATE INDEX transactions_user_id_idx ON transactions(user_id);
CREATE INDEX transactions_transaction_date_idx ON transactions(transaction_date);
CREATE INDEX transactions_category_idx ON transactions(category);
```

6. **Run Application**

```bash
python -m uvicorn app.main:app --reload
```

Server will start at: `http://localhost:8000`

## API Endpoints

### Base URL

`http://localhost:8000/transactions`

### Get All Transactions

```http
GET /transactions?page=1&page_size=10&sort_by=transaction_date&order=desc
```

**Query Parameters:**

- `page` (int, default: 1) - Page number
- `page_size` (int, default: 10, max: 100) - Results per page
- `search` (string) - Search keyword
- `category` (string) - Filter by category
- `type` (string) - Filter by type: `income` or `expense`
- `start_date` (date) - Start date filter (YYYY-MM-DD)
- `end_date` (date) - End date filter (YYYY-MM-DD)
- `sort_by` (string) - Sort field: `transaction_date`, `amount`, `category`, or `is_personal`
- `order` (string) - Sort order: `asc` or `desc`

Example (personal transactions first):

```http
GET /transactions?sort_by=is_personal&order=desc
```

**Response:**

```json
{
  "success": true,
  "message": "Transactions retrieved successfully",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "user-123",
      "description": "Office supplies",
      "amount": "150.50",
      "type": "expense",
      "category": "Supplies",
      "transaction_date": "2024-02-27",
      "is_personal": false,
      "created_at": "2024-02-27T10:30:00",
      "updated_at": "2024-02-27T10:30:00",
      "warning": null
    }
  ],
  "total_count": 50,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

### Get Single Transaction

```http
GET /transactions/{id}
```

### Create Transaction

```http
POST /transactions
Content-Type: application/json

{
  "description": "Monthly subscription",
  "amount": "99.99",
  "type": "expense",
  "category": "Software",
  "transaction_date": "2024-02-27",
  "is_personal": false
}
```

### Update Transaction

```http
PUT /transactions/{id}
Content-Type: application/json

{
  "amount": "109.99",
  "category": "Subscriptions"
}
```

### Delete Transaction

```http
DELETE /transactions/{id}
```

### Export to CSV

```http
GET /transactions/export/csv?category=Supplies&start_date=2024-01-01
```

**Query Parameters:** Same as GET /transactions (but no pagination)

**Response:** CSV file download

**Example CSV Output:**

```csv
Transaction Date,Description,Category,Type,Amount,Is Personal
2024-02-27,Office supplies,Supplies,expense,150.50,No
2024-02-25,Client payment,Revenue,income,5000.00,No
```

### Export to PDF

```http
GET /transactions/export/pdf?type=expense&start_date=2024-01-01&end_date=2024-02-27
```

**Query Parameters:** Same as GET /transactions (but no pagination)

**Response:** PDF file download with formatted report and summary

**Report Includes:**

- Transaction details table (Date, Description, Category, Type, Amount)
- Summary section:
  - Total Income
  - Total Expense
  - Net Profit

## Features Detail

### 1. Dynamic Filtering

Combine multiple filters simultaneously:

```http
GET /transactions?category=Personal&type=expense&start_date=2024-01-01&search=medical
```

### 2. Pagination

Efficient pagination with total count:

```http
GET /transactions?page=2&page_size=25
```

### 3. Sorting

Sort by any numeric or text field:

```http
GET /transactions?sort_by=amount&order=asc
```

### 4. Personal Expense Warning

Transactions marked as personal or with "Personal" category include a warning:

```json
{
  "warning": "This expense is marked as personal and may affect business profit clarity."
}
```

### 5. Export Features

**CSV Export** - Perfect for Excel/Sheets analysis

- All filtered transactions in clean format
- Compatible with all spreadsheet applications

**PDF Export** - Professional financial report

- Formatted transaction table
- Summary with totals
- Perfect for sharing with accountants

## Database Schema

```sql
Table: transactions

Columns:
- id (UUID, PK)
- user_id (UUID, FK) - Links to auth.users
- description (TEXT) - Transaction description
- amount (NUMERIC) - Transaction amount
- type (TEXT) - 'income' or 'expense'
- category (TEXT) - Transaction category
- transaction_date (DATE) - When transaction occurred
- is_personal (BOOLEAN) - Personal expense flag
- created_at (TIMESTAMP) - Record creation time
- updated_at (TIMESTAMP) - Last update time
```

## Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "message": "Descriptive error message",
  "error_code": "ERROR_CODE"
}
```

**Common Error Codes:**

- `TRANSACTION_NOT_FOUND` - Transaction doesn't exist
- `TRANSACTION_FETCH_ERROR` - Failed to retrieve transaction
- `TRANSACTION_CREATE_ERROR` - Failed to create transaction
- `TRANSACTION_UPDATE_ERROR` - Failed to update transaction
- `TRANSACTION_DELETE_ERROR` - Failed to delete transaction
- `EXPORT_CSV_ERROR` - Failed to generate CSV
- `EXPORT_PDF_ERROR` - Failed to generate PDF
- `NO_DATA_FOR_EXPORT` - No transactions to export

## Authentication Note

⚠️ **Important:** The current implementation uses a placeholder user ID. In production, you must:

1. Implement JWT token extraction from Authorization header
2. Decode and validate JWT tokens using your SECRET_KEY
3. Extract user_id from token claims

Replace the `get_user_id()` function in `routes/transactions.py`:

```python
from fastapi import Request
from jose import jwt, JWTError

async def get_user_id(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing authorization")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## Testing with cURL

```bash
# Get all transactions
curl http://localhost:8000/transactions

# Search transactions
curl "http://localhost:8000/transactions?search=office"

# Create transaction
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Office rent",
    "amount": "2000.00",
    "type": "expense",
    "category": "Rent",
    "transaction_date": "2024-02-27",
    "is_personal": false
  }'

# Export CSV
curl "http://localhost:8000/transactions/export/csv?category=Supplies" \
  --output transactions.csv

# Export PDF
curl "http://localhost:8000/transactions/export/pdf" \
  --output report.pdf
```

## Production Recommendations

1. **Security**
   - Change CORS origins to specific domains
   - Implement proper JWT authentication
   - Use HTTPS only
   - Add rate limiting
   - Validate and sanitize all inputs

2. **Performance**
   - Add database query caching
   - Implement request pagination limits
   - Add database indexes (included in schema)
   - Monitor API response times

3. **Logging**
   - Implement structured logging
   - Add request/response logging
   - Monitor errors and exceptions

4. **Testing**
   - Add unit tests
   - Add integration tests
   - Test export functionality
   - Load test pagination

---

## 🗂️ Repository Structure

This repository is part of the **AI Pocket CFO** ecosystem organized across three integrated projects:

### Main Repository: pocketCFO
**URL:** https://github.com/YazheneS/pocketCFO

- **Branch `master`**: Core FastAPI backend 
  - RESTful API with full transaction management
  - Database operations and business logic
  - CSV/PDF export functionality
  - Production-ready implementation

- **Branch `module2-voice`**: Voice interaction module 
  - Voice recognition and STT integration
  - Voice command processing
  - Mobile voice interface
  - Real-time voice feedback system

### Integrated Projects

#### 1. **pocket-cfo-chainlit** (Conversational AI Layer)
Located in same workspace directory  
Integrates with: pocketCFO master branch

**Purpose:** Natural language transaction logging  
**Technology:** Chainlit + Ollama LLM (llama3.2)  
**Features:**
- Chat-based transaction entry ("Spent $500 on rent")
- Real-time AI-generated insights  
- Fallback regex parsing for robustness  
- Transaction history in conversation context

**Key Files:**
- `app.py` - Main Chainlit application
- `.chainlit/` - UI configuration
- `.env` - Supabase and Ollama credentials

#### 2. **pocketCFO-module2-voice** (Voice Module)
Located in same workspace directory  
Repository: Same as pocketCFO, branch `module2-voice`

**Purpose:** Voice-powered financial interaction  
**Technology:** STT/TTS + Voice processing  
**Development Status:** In progress  
**Integration Point:** Shares Supabase backend with master

---

## 🔄 System Data Flow

```
User Input Channels:
│
├─→ REST API (HTTP)
│   └─→ pocketCFO FastAPI Backend
│       └─→ Supabase PostgreSQL
│           ├─→ transactions (main)
│           └─→ transactions_ai (AI logs)
│
├─→ Natural Language (Chat)
│   └─→ pocket-cfo-chainlit (Chainlit UI)
│       └─→ Ollama LLM (llama3.2)
│           └─→ pocketCFO API
│               └─→ Supabase Database
│
└─→ Voice (Coming Soon)
    └─→ pocketCFO-module2-voice
        └─→ Speech-to-Text Engine
            └─→ pocketCFO API
                └─→ Supabase Database
```

---

## 🔗 Cross-Module Integration

### Shared Database
All modules write to the same Supabase PostgreSQL instance:

```
Supabase Project Tables:
├── transactions
│   ├── id (UUID, PK)
│   ├── user_id (UUID, FK)
│   ├── description (TEXT)
│   ├── amount (NUMERIC)
│   ├── type (TEXT) - 'income'|'expense'
│   ├── category (TEXT)
│   ├── transaction_date (DATE)
│   ├── is_personal (BOOLEAN)
│   ├── created_at (TIMESTAMP)
│   └── updated_at (TIMESTAMP)
│
└── transactions_ai (optional, for AI-specific logging)
    └── Same structure with AI metadata
```

### API Contract
All modules interact through the pocketCFO REST API:

```json
POST /transactions
{
  "description": "Transaction description",
  "amount": "100.00",
  "type": "expense|income",
  "category": "Category Name",
  "transaction_date": "2024-02-27",
  "is_personal": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Transaction created successfully",
  "data": {
    "id": "uuid",
    "description": "Transaction description",
    "amount": "100.00",
    "type": "expense",
    "category": "Category Name",
    "transaction_date": "2024-02-27",
    "is_personal": false,
    "created_at": "2024-02-27T10:30:00",
    "updated_at": "2024-02-27T10:30:00"
  }
}
```

### Configuration Across Modules

**Shared `.env` Variables:**

```env
# Database (required in all modules)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Backend (pocketCFO only)
SECRET_KEY=your-jwt-secret

# Ollama/AI (Chainlit only)
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2

# Voice (module2-voice only)
STT_ENGINE=google-cloud|azure|local
TTS_ENGINE=gcloud-text-to-speech|azure-speech
```

---

## 🚀 Complete Setup (All Modules)

### Start All Services

**Terminal 1 - FastAPI Backend:**
```bash
cd pocketCFO
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
# → Running at http://localhost:8000
```

**Terminal 2 - Ollama LLM:**
```bash
# Install from https://ollama.ai, then:
ollama pull llama3.2
ollama serve
# → Listening at http://localhost:11434
```

**Terminal 3 - Chainlit Interface:**
```bash
cd pocket-cfo-chainlit
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
chainlit run app.py
# → Running at http://localhost:8001
```

**Terminal 4 - Voice Module (Development):**
```bash
cd pocketCFO-module2-voice
# Setup and run when implementation is complete
```

### Verify Integration

After all services are running:

```bash
# 1. Check API health
curl http://localhost:8000/docs

# 2. Test API transaction creation
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"description": "Test", "amount": "100", "type": "expense", "category": "Test", "transaction_date": "2024-02-27", "is_personal": false}'

# 3. Test Chainlit interface
open http://localhost:8001
# Send message: "Spent $100 on supplies"

# 4. Verify database
# Check Supabase dashboard for new transactions
```

---

---

## 🛣️ Roadmap & Module Status

### ✅ Module 1: Core Backend (pocketCFO - Master Branch)

**Status: Production Ready**

- [x] FastAPI REST API with full CRUD
- [x] Supabase PostgreSQL integration
- [x] Search, filter, and sort functionality
- [x] CSV and PDF export capabilities
- [x] Error handling and validation
- [x] Type-safe Pydantic models
- [x] Async/await operations

### ✅ Module 1.5: Chainlit AI Interface (pocket-cfo-chainlit)

**Status: Production Ready**

- [x] Chainlit conversational UI
- [x] Ollama AI integration (llama3.2)
- [x] Natural language transaction parsing
- [x] Real-time financial insights
- [x] Transaction history in context
- [x] Fallback regex parsing
- [x] Stream responses for UX

### 🚧 Module 2: Voice Interaction (pocketCFO - Module2-Voice Branch)

**Status: In Development**

- [ ] Voice recognition integration
- [ ] Speech-to-text processing
- [ ] Voice command system
- [ ] Mobile voice interface
- [ ] Voice feedback/TTS
- [ ] Multi-language support
- [ ] Voice-to-API integration

### 📋 Future Enhancements (Post-Module-2)

- [ ] Dashboard with charts/analytics
- [ ] Multi-user teams support
- [ ] Automated receipt scanning (OCR)
- [ ] Bank account integration
- [ ] Expense approval workflows
- [ ] Budget tracking and alerts
- [ ] Tax category recommendations
- [ ] Multi-currency support
- [ ] iOS/Android mobile apps
- [ ] Desktop client application

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 Documentation

- **API Documentation**: Available at `/docs` endpoint when running the server
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Examples**: See [EXAMPLES.md](EXAMPLES.md)
- **Database Schema**: See [schema.sql](schema.sql)

---

## License

MIT

## 🆘 Support & Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/YazheneS/pocketCFO/issues)
- **Discussions**: [Join community discussions](https://github.com/YazheneS/pocketCFO/discussions)
- **Documentation**: Check `/docs` endpoint for interactive API documentation

---

## 🙏 Acknowledgments

Built with:

- [FastAPI](https://fastapi.tiangolo.com/) - High-performance Python web framework
- [Chainlit](https://chainlit.io/) - Conversational AI interface framework
- [Ollama](https://ollama.ai/) - Local LLM inference engine
- [Supabase](https://supabase.com/) - Open-source Firebase alternative
- [ReportLab](https://www.reportlab.com/) - PDF generation library

---

**Made with ❤️ for small businesses seeking smarter financial management**
