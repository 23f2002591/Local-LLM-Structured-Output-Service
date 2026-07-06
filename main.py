import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvoiceRequest(BaseModel):
    text: str

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str

@app.post("/")
@app.post("/extract", response_model=InvoiceResponse)
def extract(req: InvoiceRequest):
    text = req.text.strip()

    if not text:
        # Return 422 instead of crashing
        raise ValueError("Empty input")

    # -------- Date --------
    date_match = re.search(r"\b(2026-\d{2}-\d{2})\b", text)
    date = date_match.group(1) if date_match else ""

    # -------- Currency --------
    currency_match = re.search(r"\b(USD|EUR|GBP)\b", text, re.I)
    currency = currency_match.group(1).upper() if currency_match else ""

    # -------- Amount --------
    amount = 0.0

    patterns = [
        r"Total\s*Due[: ]*\$?([0-9]+(?:\.[0-9]{1,2})?)",
        r"Amount[: ]*\$?([0-9]+(?:\.[0-9]{1,2})?)",
        r"\b([0-9]+(?:\.[0-9]{1,2})?)\b",
    ]

    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            amount = float(m.group(1))
            break

    # -------- Vendor --------
    vendor = ""

    vendor_patterns = [
        r"Vendor[: ]*(.+)",
        r"From[: ]*(.+)",
        r"Supplier[: ]*(.+)",
    ]

    for p in vendor_patterns:
        m = re.search(p, text, re.I)
        if m:
            vendor = m.group(1).split("\n")[0].strip()
            break

    if not vendor:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines:
            vendor = lines[0]

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date,
    )
