# Sample Data

Three clean, structured documents for testing the system end to end.

## Files

| File | Format | Content |
|---|---|---|
| `travel_policy.txt` | TXT | Company travel and reimbursement policy |
| `employees.csv` | CSV | Sample employee records (name, department, salary, leave, join date) |
| `company_policy.pdf` | PDF | Employee benefits policy (health insurance, remote work, training budget, performance reviews) |

## How to Use

1. Upload any of these files via Swagger UI (`/docs` → `POST /api/v1/upload-document`) or the Streamlit interface
2. Ask a question, for example:
   - "What is the hotel limit for international travel?"
   - "Which employee has the highest salary?"
   - "What is the annual training budget for employees?"

Expected answers and full reasoning traces for these exact questions are documented in `docs/known-limitations.md` and `docs/Capstone_Known_Limitations.docx`.
