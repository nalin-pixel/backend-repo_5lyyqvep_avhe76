import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from database import db, create_document
from schemas import Lead

app = FastAPI(title="Il Marketing Much More API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Il Marketing Much More API is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response

# Contact form lead intake
@app.post("/api/leads")
def create_lead(lead: Lead):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        lead_id = create_document("lead", lead)
        return {"status": "ok", "id": lead_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Optional: simple list endpoint (last N leads)
class LeadOut(BaseModel):
    id: str
    name: str
    email: str
    phone: str | None = None
    message: str

@app.get("/api/leads", response_model=List[LeadOut])
def list_leads(limit: int = 10):
    from database import get_documents
    try:
        docs = get_documents("lead", limit=limit)
        # map ObjectId to str and keys
        out: List[LeadOut] = []
        for d in docs:
            out.append(LeadOut(
                id=str(d.get("_id")),
                name=d.get("name", ""),
                email=d.get("email", ""),
                phone=d.get("phone"),
                message=d.get("message", "")
            ))
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
