from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
import shutil
import os
from PIL import Image
import json
import motor.motor_asyncio

app = FastAPI(title="AI Financial Data Ingestion & Extraction Service")

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
UPLOAD_DIR = "uploaded_statements"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Database Setup
MONGO_DETAILS = "mongodb://localhost:27017"
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
db = mongo_client["financial_db"]
collection = db["statements"]

# Define schemas for Gemini
class FinancialMetric(BaseModel):
    metric: str = Field(description="The financial metric name (e.g., Revenue, Net Profit, EPS)")
    value: float = Field(description="The numeric value extracted from the table")
    period: str = Field(description="The explicit timeframe or fiscal interval (Year/Quarter)")

class FinancialStatementSchema(BaseModel):
    company_name: Optional[str] = Field(None, description="Name of the company if visible, otherwise null")
    financial_data: List[FinancialMetric] = Field(default_factory=list, description="Array of structural data metrics")

# Gemini API Key
GEMINI_API_KEY = "AQ.Ab8RN6JQEqWsfioABURTnNw969gHsxblr4_60OUGpYy7ZDaY8Q"
try:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Failed to initialize Gemini AI client: {e}")

# -------------------------------------------------------------------------
# Grafana-compatible endpoint
# -------------------------------------------------------------------------
@app.get("/api/grafana-metrics")
async def get_grafana_metrics():
    cursor = collection.find({})
    documents = await cursor.to_list(length=500)

    formatted_metrics = []
    for doc in documents:
        financial_records = doc.get("financial_data", [])
        for record in financial_records:
            try:
                raw_val = record.get("value", 0.0)
                clean_val = float(str(raw_val).replace(",", "")) if raw_val is not None else 0.0
            except (ValueError, TypeError):
                clean_val = 0.0

            formatted_metrics.append({
                "id": str(doc.get("_id")),
                "source_file": doc.get("source_file"),
                "company_name": doc.get("company_name") or "Unknown Company",
                "period": record.get("period"),
                "metric": record.get("metric"),
                "value": clean_val
            })

    return formatted_metrics

# -------------------------------------------------------------------------
@app.get("/")
async def home():
    return {"message": "Server is up! Grafana stream active at /api/grafana-metrics"}

# -------------------------------------------------------------------------
@app.post("/upload-and-extract/")
async def upload_and_extract_statement(
    file: UploadFile = File(...),
    company_name: Optional[str] = Form(None)
):
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported format.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        image = Image.open(file_path)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to open image file.")

    # Updated prompt to include company name extraction
    prompt = (
        "Extract the company name (if visible) and the following metrics: "
        "Revenue, Net Profit, and EPS across rows and periods. "
        "If the company name is not visible, return 'Unknown Company'."
    )

    try:
        response = ai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FinancialStatementSchema,
            ),
        )

        extracted_json = json.loads(response.text)

        # Fallback logic for missing company name
        final_company_name = (
            company_name
            or extracted_json.get("company_name")
            or "Unknown Company"
        )

        document_to_store = {
            "source_file": file.filename,
            "company_name": final_company_name,
            "financial_data": extracted_json.get("financial_data", []),
        }

        db_result = await collection.insert_one(document_to_store)
        return {
            "status": "Success",
            "database_document_id": str(db_result.inserted_id),
            "company_name_used": final_company_name,
            "ai_extracted_data": extracted_json,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=1998, reload=True)