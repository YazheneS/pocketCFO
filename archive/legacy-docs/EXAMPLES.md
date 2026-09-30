"""
Example usage and cURL commands for the Transaction Management API.

This file demonstrates common API usage patterns.
"""

# ============================================================

# SETUP

# ============================================================

# 1. Install dependencies:

# pip install -r requirements.txt

#

# 2. Configure environment:

# Copy .env.example to .env

# Update with your Supabase credentials

#

# 3. Create database table (in Supabase SQL Editor):

# See README.md for SQL schema

#

# 4. Run the application:

# python -m uvicorn app.main:app --reload

# ============================================================

# API EXAMPLES USING cURL

# ============================================================

# 1. Health check

curl http://localhost:8000/health

# 2. API info

curl http://localhost:8000/

# 3. Get all transactions (first page, 10 per page)

curl http://localhost:8000/transactions

# 4. Get with pagination

curl "http://localhost:8000/transactions?page=2&page_size=20"

# 5. Search transactions

curl "http://localhost:8000/transactions?search=office"

# 6. Filter by category

curl "http://localhost:8000/transactions?category=Supplies"

# 7. Filter by type

curl "http://localhost:8000/transactions?type=expense"

# 8. Filter by date range

curl "http://localhost:8000/transactions?start_date=2024-01-01&end_date=2024-02-28"

# 9. Search + filter + sort

curl "http://localhost:8000/transactions?search=office&category=Supplies&sort_by=amount&order=asc"

# 9b. Sort by personal flag (personal first)

curl "http://localhost:8000/transactions?sort_by=is_personal&order=desc"

# 10. Get single transaction

curl http://localhost:8000/transactions/550e8400-e29b-41d4-a716-446655440000

# 11. Create transaction

curl -X POST http://localhost:8000/transactions \
 -H "Content-Type: application/json" \
 -d '{
"description": "Office supplies purchase",
"amount": 150.50,
"type": "expense",
"category": "Supplies",
"transaction_date": "2024-02-27",
"is_personal": false
}'

# 12. Create income transaction

curl -X POST http://localhost:8000/transactions \
 -H "Content-Type: application/json" \
 -d '{
"description": "Client payment received",
"amount": 5000.00,
"type": "income",
"category": "Revenue",
"transaction_date": "2024-02-27",
"is_personal": false
}'

# 13. Create personal expense (will include warning)

curl -X POST http://localhost:8000/transactions \
 -H "Content-Type: application/json" \
 -d '{
"description": "Personal medical expense",
"amount": 200.00,
"type": "expense",
"category": "Personal",
"transaction_date": "2024-02-27",
"is_personal": true
}'

# 14. Update transaction

curl -X PUT http://localhost:8000/transactions/550e8400-e29b-41d4-a716-446655440000 \
 -H "Content-Type: application/json" \
 -d '{
"amount": 175.50,
"description": "Updated office supplies"
}'

# 15. Delete transaction

curl -X DELETE http://localhost:8000/transactions/550e8400-e29b-41d4-a716-446655440000

# 16. Export to CSV

curl "http://localhost:8000/transactions/export/csv" \
 --output transactions.csv

# 17. Export to CSV with filters

curl "http://localhost:8000/transactions/export/csv?category=Supplies&type=expense&start_date=2024-01-01" \
 --output supplies_expenses.csv

# 18. Export to PDF

curl "http://localhost:8000/transactions/export/pdf" \
 --output report.pdf

# 19. Export to PDF with date range

curl "http://localhost:8000/transactions/export/pdf?start_date=2024-01-01&end_date=2024-02-28" \
 --output january_february_report.pdf

# 20. Complex query: search + multiple filters + sorting

curl "http://localhost:8000/transactions?search=office&category=Supplies&type=expense&start_date=2024-01-01&sort_by=amount&order=desc&page=1&page_size=25"

# ============================================================

# PYTHON EXAMPLES

# ============================================================

"""
import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Get all transactions

response = requests.get(f"{BASE_URL}/transactions")
transactions = response.json()
print(json.dumps(transactions, indent=2))

# Create a transaction

payload = {
"description": "New office furniture",
"amount": 500.00,
"type": "expense",
"category": "Office Equipment",
"transaction_date": str(date.today()),
"is_personal": False
}
response = requests.post(f"{BASE_URL}/transactions", json=payload, headers=HEADERS)
created = response.json()
transaction_id = created["data"]["id"]
print(f"Created transaction: {transaction_id}")

# Update transaction

update_payload = {
"amount": 550.00
}
response = requests.put(
f"{BASE_URL}/transactions/{transaction_id}",
json=update_payload,
headers=HEADERS
)
updated = response.json()
print(json.dumps(updated["data"], indent=2))

# Search transactions

response = requests.get(
f"{BASE_URL}/transactions",
params={"search": "office"}
)
results = response.json()
print(f"Found {results['total_count']} transactions")

# Filter by date range

response = requests.get(
f"{BASE_URL}/transactions",
params={
"start_date": "2024-01-01",
"end_date": "2024-02-28",
"sort_by": "amount",
"order": "desc"
}
)
filtered = response.json()
print(f"Total expense for Jan-Feb: {sum(t['amount'] for t in filtered['data'] if t['type'] == 'expense')}")

# Export to CSV

response = requests.get(f"{BASE_URL}/transactions/export/csv")
with open("transactions.csv", "wb") as f:
f.write(response.content)
print("Exported to transactions.csv")

# Export to PDF

response = requests.get(f"{BASE_URL}/transactions/export/pdf")
with open("report.pdf", "wb") as f:
f.write(response.content)
print("Exported to report.pdf")

# Delete transaction

response = requests.delete(f"{BASE_URL}/transactions/{transaction_id}")
result = response.json()
print(result["message"])
"""

# ============================================================

# COMMON FILTER COMBINATIONS

# ============================================================

# All expenses in February

curl "http://localhost:8000/transactions?type=expense&start_date=2024-02-01&end_date=2024-02-29&sort_by=amount&order=desc"

# Income-only transactions

curl "http://localhost:8000/transactions?type=income&sort_by=transaction_date&order=desc"

# Specific category

curl "http://localhost:8000/transactions?category=Utilities"

# Personal expenses (potential tax issues)

curl "http://localhost:8000/transactions?category=Personal&type=expense"

# Recent large expenses

curl "http://localhost:8000/transactions?type=expense&sort_by=amount&order=desc&page_size=5"

# Search for vendor

curl "http://localhost:8000/transactions?search=amazon"

# Monthly summary (February)

curl "http://localhost:8000/transactions/export/csv?start_date=2024-02-01&end_date=2024-02-29"

# ============================================================

# ERROR HANDLING EXAMPLES

# ============================================================

# Invalid transaction ID (404)

curl http://localhost:8000/transactions/invalid-id

# Missing required field on create

curl -X POST http://localhost:8000/transactions \
 -H "Content-Type: application/json" \
 -d '{
"description": "Missing required fields"
}'

# Invalid amount (must be positive)

curl -X POST http://localhost:8000/transactions \
 -H "Content-Type: application/json" \
 -d '{
"description": "Invalid amount",
"amount": -100,
"type": "expense",
"category": "Test",
"transaction_date": "2024-02-27"
}'

# Invalid type (must be income or expense)

curl -X POST http://localhost:8000/transactions \
 -H "Content-Type: application/json" \
 -d '{
"description": "Invalid type",
"amount": 100,
"type": "transfer",
"category": "Test",
"transaction_date": "2024-02-27"
}'
