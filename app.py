"""
FastAPI Server & Vercel Entrypoint cho AI Agent Minh An CRM
Hỗ trợ chạy cả trên Vercel (FastAPI Preset) và Localhost (uvicorn app:app --reload --port 8000)
"""

from pathlib import Path
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Minh An AI Agent CRM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

# MASTER DATA
CATALOG = {
    "LAP-DELL-5520": {"name": "Laptop Dell Latitude 5520 i7/16GB/512GB", "price": 22_500_000},
    "SRV-DELL-R740": {"name": "Server Dell PowerEdge R740 2x Xeon", "price": 85_000_000},
    "SW-CISCO-C9200": {"name": "Switch Cisco Catalyst C9200L 24 Ports", "price": 28_000_000},
    "SVC-SETUP-NW": {"name": "Dịch vụ Triển khai Mạng", "price": 15_000_000},
    "SVC-MAINT-1Y": {"name": "Dịch vụ Bảo trì CNTT 1 năm", "price": 36_000_000}
}

INVENTORY = {
    "LAP-DELL-5520": {"stock": 25, "lead_time_out": 7},
    "SRV-DELL-R740": {"stock": 1, "lead_time_out": 21},
    "SW-CISCO-C9200": {"stock": 10, "lead_time_out": 14},
    "SVC-SETUP-NW": {"stock": 999, "lead_time_out": 2},
    "SVC-MAINT-1Y": {"stock": 999, "lead_time_out": 1}
}


class RequestItem(BaseModel):
    product_code: str
    quantity: int


class CustomerRequest(BaseModel):
    customer_name: str
    customer_email: str
    items: List[RequestItem]
    requested_discount_rate: float = 0.0
    desired_deadline_days: int = 7


def _read_html_file(filename: str) -> HTMLResponse:
    for candidate in [BASE_DIR / filename, BASE_DIR.parent / filename]:
        if candidate.exists():
            return HTMLResponse(content=candidate.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse(content=f"<h1>Không tìm thấy file {filename}</h1>", status_code=404)


@app.get("/", response_class=HTMLResponse)
def serve_home():
    return _read_html_file("index.html")


@app.get("/index.html", response_class=HTMLResponse)
def serve_index():
    return _read_html_file("index.html")


@app.get("/b2b_process", response_class=HTMLResponse)
@app.get("/b2b_process.html", response_class=HTMLResponse)
def serve_b2b_process():
    return _read_html_file("b2b_process.html")


@app.get("/quote_template", response_class=HTMLResponse)
@app.get("/quote_template.html", response_class=HTMLResponse)
def serve_quote_template():
    return _read_html_file("quote_template.html")


@app.get("/api")
@app.get("/api/health")
def health_check():
    return JSONResponse({"status": "ok", "service": "Minh An B2B AI Agent CRM"})


@app.post("/api/v1/process-opportunity")
def process_opportunity(req: CustomerRequest):
    total_list_price = 0
    max_lead_time = 0
    processed_items = []

    for it in req.items:
        cat = CATALOG.get(it.product_code)
        if not cat:
            continue
        inv = INVENTORY.get(it.product_code, {"stock": 0, "lead_time_out": 30})
        in_stock = inv["stock"] >= it.quantity
        lead = 2 if in_stock else inv["lead_time_out"]
        if lead > max_lead_time:
            max_lead_time = lead

        subtotal = cat["price"] * it.quantity
        total_list_price += subtotal

        processed_items.append({
            "code": it.product_code,
            "name": cat["name"],
            "quantity": it.quantity,
            "unit_price": cat["price"],
            "subtotal": subtotal,
            "in_stock": in_stock,
            "lead_time_days": lead
        })

    discount_amount = total_list_price * req.requested_discount_rate
    final_amount = total_list_price - discount_amount
    requires_approval = req.requested_discount_rate > 0.10
    timeline_warning = req.desired_deadline_days < max_lead_time

    return {
        "customer": req.customer_name,
        "email": req.customer_email,
        "items": processed_items,
        "total_list_price": total_list_price,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "feasible_lead_time_days": max_lead_time,
        "timeline_warning": timeline_warning,
        "requires_manager_approval": requires_approval,
        "approval_status": "Chờ Trưởng phòng duyệt" if requires_approval else "Đã duyệt tự động"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

