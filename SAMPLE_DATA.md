# 📦 Sample Data Templates

Use these templates to create test data for your Atlas Operations Copilot.

---

## 📄 Sample PDF Content

Create a file `data/raw_pdfs/operational_playbook.pdf` with content like:

```
OPERATIONAL PLAYBOOK - Q1 2026

INCIDENT RESPONSE PROCEDURES

When a production outage occurs:
1. Check monitoring dashboard at dashboard.internal/ops
2. Page on-call engineer via PagerDuty
3. Create incident ticket in Jira (PROJECT-INC)
4. Update status page within 5 minutes

ESCALATION MATRIX

Level 1: Support Team (response time: 15 minutes)
Level 2: Engineering Team (response time: 30 minutes)
Level 3: Engineering Manager (response time: 1 hour)
Level 4: VP Engineering (critical only)

KNOWN BOTTLENECKS

- Database connection pool: max 50 connections
- API rate limit: 1000 requests/minute
- Batch processing: runs every 6 hours, takes 45 minutes
- Data pipeline: ingests 2TB/day, capacity limit at 3TB

MAINTENANCE WINDOWS

Database maintenance: Every Sunday 2-4 AM EST
Application deployments: Tuesday/Thursday 6-7 PM EST
Infrastructure updates: Last Saturday of month, 12-4 AM EST
```

---

## 📊 Sample CSV - Inventory Data

Create `data/raw_csv/inventory.csv`:

```csv
item_id,item_name,category,quantity,reorder_threshold,supplier,last_restocked,status
INV-001,Widget A,Electronics,45,50,Acme Supply,2026-04-15,low_stock
INV-002,Widget B,Electronics,230,100,Acme Supply,2026-04-20,in_stock
INV-003,Component X,Hardware,12,25,TechParts Inc,2026-03-28,critical
INV-004,Assembly Kit,Hardware,156,75,BuildCo,2026-04-25,in_stock
INV-005,Sensor Module,Electronics,8,20,SensorTech,2026-02-10,critical
INV-006,Power Supply,Electronics,95,50,PowerCorp,2026-04-22,in_stock
INV-007,Cable Pack,Accessories,340,200,CableWorld,2026-04-18,in_stock
INV-008,Mounting Bracket,Hardware,23,30,BuildCo,2026-03-15,low_stock
```

---

## 📊 Sample CSV - Performance Metrics

Create `data/raw_csv/performance_metrics.csv`:

```csv
date,service,response_time_ms,error_rate,requests_per_sec,cpu_usage,memory_usage
2026-04-28,api-gateway,145,0.02,850,45,62
2026-04-28,auth-service,89,0.01,420,32,48
2026-04-28,data-pipeline,2340,0.15,12,78,85
2026-04-28,analytics-engine,567,0.03,145,56,71
2026-04-29,api-gateway,178,0.03,920,52,68
2026-04-29,auth-service,92,0.01,450,35,51
2026-04-29,data-pipeline,2890,0.22,15,89,92
2026-04-29,analytics-engine,612,0.04,156,61,74
2026-04-30,api-gateway,134,0.01,880,43,59
2026-04-30,auth-service,85,0.00,440,31,47
2026-04-30,data-pipeline,2150,0.08,11,72,81
2026-04-30,analytics-engine,523,0.02,141,54,69
```

---

## 🗂️ Sample CRM JSON - Customer Accounts

Create `data/mock_crm/customer_accounts.json`:

```json
{
  "records": [
    {
      "account_id": "ACC-001",
      "company_name": "Acme Corporation",
      "industry": "Manufacturing",
      "status": "active",
      "annual_revenue": 2500000,
      "employee_count": 450,
      "contact": {
        "name": "John Smith",
        "email": "john.smith@acme.example",
        "phone": "+1-555-0123"
      },
      "health_score": 85,
      "renewal_date": "2026-08-15",
      "product_usage": {
        "licenses": 50,
        "active_users": 42,
        "support_tickets_90d": 3
      },
      "notes": "High-priority account. Expanding team Q3. Interested in enterprise tier."
    },
    {
      "account_id": "ACC-002",
      "company_name": "TechStart Inc",
      "industry": "Technology",
      "status": "at_risk",
      "annual_revenue": 450000,
      "employee_count": 85,
      "contact": {
        "name": "Sarah Johnson",
        "email": "sarah@techstart.example",
        "phone": "+1-555-0456"
      },
      "health_score": 42,
      "renewal_date": "2026-06-01",
      "product_usage": {
        "licenses": 20,
        "active_users": 8,
        "support_tickets_90d": 12
      },
      "notes": "Declining usage. Multiple support escalations. Schedule check-in call."
    },
    {
      "account_id": "ACC-003",
      "company_name": "Global Logistics Partners",
      "industry": "Logistics",
      "status": "active",
      "annual_revenue": 5800000,
      "employee_count": 1200,
      "contact": {
        "name": "Michael Chen",
        "email": "m.chen@globallogistics.example",
        "phone": "+1-555-0789"
      },
      "health_score": 92,
      "renewal_date": "2027-01-20",
      "product_usage": {
        "licenses": 150,
        "active_users": 145,
        "support_tickets_90d": 1
      },
      "notes": "Power user. Excellent adoption. Potential case study candidate."
    },
    {
      "account_id": "ACC-004",
      "company_name": "Healthcare Solutions LLC",
      "industry": "Healthcare",
      "status": "active",
      "annual_revenue": 1200000,
      "employee_count": 230,
      "contact": {
        "name": "Dr. Emily Rodriguez",
        "email": "e.rodriguez@healthsolutions.example",
        "phone": "+1-555-0321"
      },
      "health_score": 78,
      "renewal_date": "2026-09-30",
      "product_usage": {
        "licenses": 35,
        "active_users": 32,
        "support_tickets_90d": 5
      },
      "notes": "Growing steadily. Compliance requirements need attention. Q2 review scheduled."
    }
  ]
}
```

---

## 🗂️ Sample CRM JSON - Pipeline Deals

Create `data/mock_crm/sales_pipeline.json`:

```json
[
  {
    "deal_id": "DEAL-101",
    "prospect": "DataTech Innovations",
    "stage": "negotiation",
    "deal_value": 125000,
    "probability": 75,
    "close_date": "2026-05-15",
    "owner": "Alex Thompson",
    "next_action": "Send proposal revision addressing security questions",
    "competitors": ["CompetitorA", "CompetitorB"],
    "decision_makers": [
      {"name": "CTO", "sentiment": "positive"},
      {"name": "CFO", "sentiment": "neutral"}
    ]
  },
  {
    "deal_id": "DEAL-102",
    "prospect": "Retail Giants Corp",
    "stage": "qualification",
    "deal_value": 450000,
    "probability": 30,
    "close_date": "2026-07-01",
    "owner": "Maria Garcia",
    "next_action": "Schedule technical discovery call",
    "competitors": ["CompetitorC"],
    "decision_makers": [
      {"name": "VP Operations", "sentiment": "interested"}
    ]
  },
  {
    "deal_id": "DEAL-103",
    "prospect": "FinServe Partners",
    "stage": "closed_won",
    "deal_value": 280000,
    "probability": 100,
    "close_date": "2026-04-22",
    "owner": "James Lee",
    "next_action": "Initiate onboarding process",
    "competitors": [],
    "decision_makers": [
      {"name": "CEO", "sentiment": "champion"},
      {"name": "COO", "sentiment": "positive"}
    ]
  }
]
```

---

## 🧪 Quick Test Data Setup

Run this script to create all sample files at once:

```bash
# Create sample_data_setup.sh

#!/bin/bash

# Create directories
mkdir -p data/raw_pdfs data/raw_csv data/mock_crm

# Create sample CSV files
cat > data/raw_csv/inventory.csv << 'EOF'
item_id,item_name,category,quantity,reorder_threshold,supplier,last_restocked,status
INV-001,Widget A,Electronics,45,50,Acme Supply,2026-04-15,low_stock
INV-002,Widget B,Electronics,230,100,Acme Supply,2026-04-20,in_stock
INV-003,Component X,Hardware,12,25,TechParts Inc,2026-03-28,critical
INV-004,Assembly Kit,Hardware,156,75,BuildCo,2026-04-25,in_stock
INV-005,Sensor Module,Electronics,8,20,SensorTech,2026-02-10,critical
EOF

cat > data/raw_csv/performance_metrics.csv << 'EOF'
date,service,response_time_ms,error_rate,requests_per_sec,cpu_usage,memory_usage
2026-04-28,api-gateway,145,0.02,850,45,62
2026-04-28,auth-service,89,0.01,420,32,48
2026-04-28,data-pipeline,2340,0.15,12,78,85
2026-04-29,api-gateway,178,0.03,920,52,68
2026-04-29,data-pipeline,2890,0.22,15,89,92
EOF

# Create sample CRM JSON
cat > data/mock_crm/customer_accounts.json << 'EOF'
{
  "records": [
    {
      "account_id": "ACC-001",
      "company_name": "Acme Corporation",
      "status": "active",
      "health_score": 85,
      "notes": "High-priority account. Expanding team Q3."
    },
    {
      "account_id": "ACC-002",
      "company_name": "TechStart Inc",
      "status": "at_risk",
      "health_score": 42,
      "notes": "Declining usage. Multiple support escalations."
    }
  ]
}
EOF

echo "✅ Sample data created!"
echo "📄 PDFs: Add your own to data/raw_pdfs/"
echo "📊 CSVs: data/raw_csv/"
echo "🗂️  CRM: data/mock_crm/"
```

---

## 🎯 Sample Queries to Test

Once your system is running, try these queries:

### Operational Queries
- "What are our current incident response procedures?"
- "Show me the escalation matrix"
- "What are the known bottlenecks in our system?"
- "When is the next maintenance window?"

### Inventory Queries
- "Which items are critically low in stock?"
- "What's the status of Widget A inventory?"
- "Who is the supplier for Sensor Modules?"
- "List all items below reorder threshold"

### Performance Queries
- "Which service has the highest error rate?"
- "Show me data-pipeline performance trends"
- "What's the average response time for the API gateway?"
- "Which services are under heavy load?"

### CRM Queries
- "Which accounts are at risk?"
- "Show me our highest health score customers"
- "What deals are in negotiation stage?"
- "Which customer has the most support tickets?"

### Analysis Queries (triggers structured insights)
- "Analyze operational bottlenecks and risks"
- "What are the top 3 risks we should address?"
- "Identify opportunities for improvement"
- "What actions should we take to improve system performance?"

---

## 📁 Expected File Structure

After setup:

```
data/
├── raw_pdfs/
│   └── operational_playbook.pdf  ← You create this
│
├── raw_csv/
│   ├── inventory.csv  ← Created by script
│   └── performance_metrics.csv  ← Created by script
│
├── mock_crm/
│   ├── customer_accounts.json  ← Created by script
│   └── sales_pipeline.json  ← Created by script
│
└── chroma_db/  ← Auto-created by ingestion script
    ├── chroma.sqlite3
    └── [other ChromaDB files]
```

---

## 🔍 Verify Data After Ingestion

After running `python scripts/ingest_all.py`, you should see:

```python
# Quick verification script
from config.config import load_config
from src.rag.vector_store import get_chroma_collection

config = load_config()
collection = get_chroma_collection(
    config.chroma_persist_path,
    config.collection_name
)

print(f"Total chunks in ChromaDB: {collection.count()}")

# Peek at a few records
results = collection.peek(limit=3)
for i, doc in enumerate(results['documents'], 1):
    print(f"\n{i}. {results['metadatas'][i-1]['source_file']}")
    print(f"   Type: {results['metadatas'][i-1]['source_type']}")
    print(f"   Content preview: {doc[:100]}...")
```

---

## 🎨 Customizing Your Data

### For PDFs:
- Use any PDF file (reports, SOPs, manuals)
- LlamaParse handles tables, multi-column layouts
- Best results: text-based PDFs (not scanned images)

### For CSVs:
- Any tabular data works
- First row must be column headers
- Keep rows atomic (one logical record per row)

### For CRM JSON:
- Flexible structure: list of objects or `{records: [...]}`
- Nested objects are flattened automatically
- Use descriptive field names for better retrieval

---

*Now you're ready to run ingestion! See [QUICKSTART.md](QUICKSTART.md) for next steps.*
