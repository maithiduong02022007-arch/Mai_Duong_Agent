"""
Hệ thống AI Agent CRM - Công ty Minh An
Luồng tự động: Tiếp nhận email -> Trích xuất -> Tra bảng giá & Tồn kho -> Kiểm tra chiết khấu -> Soạn đề xuất & Email.
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# ==========================================
# 1. DỮ LIỆU GIẢ LẬP (MASTER DATA)
# ==========================================

PRICE_CATALOG = {
    "LAP-DELL-5520": {"name": "Laptop Dell Latitude 5520 i7/16GB/512GB", "unit_price": 22_500_000, "category": "Thiết bị"},
    "SRV-DELL-R740": {"name": "Server Dell PowerEdge R740", "unit_price": 85_000_000, "category": "Thiết bị"},
    "SW-CISCO-C9200": {"name": "Switch Cisco Catalyst C9200L 24 Ports", "unit_price": 28_000_000, "category": "Thiết bị"},
    "SVC-SETUP-NW": {"name": "Dịch vụ Cài đặt & Triển khai Hạ tầng Mạng", "unit_price": 15_000_000, "category": "Dịch vụ"},
    "SVC-MAINT-1Y": {"name": "Dịch vụ Bảo trì CNTT Doanh nghiệp trọn gói 1 năm", "unit_price": 36_000_000, "category": "Dịch vụ"}
}

INVENTORY_STATUS = {
    "LAP-DELL-5520": {"available_qty": 25, "lead_time_days_if_out": 7},
    "SRV-DELL-R740": {"available_qty": 2, "lead_time_days_if_out": 21},
    "SW-CISCO-C9200": {"available_qty": 10, "lead_time_days_if_out": 14},
    "SVC-SETUP-NW": {"available_qty": 999, "lead_time_days_if_out": 2},
    "SVC-MAINT-1Y": {"available_qty": 999, "lead_time_days_if_out": 1}
}

DISCOUNT_APPROVAL_THRESHOLD = 0.10  # > 10% bắt buộc chuyển Trưởng phòng duyệt


# ==========================================
# 2. CÁC HÀM CÔNG CỤ (TOOLS FOR AGENT)
# ==========================================

def lookup_catalog_and_price(product_code: str) -> Optional[Dict[str, Any]]:
    """Tra cứu bảng giá chuẩn mới nhất, tránh tình trạng nhân viên dùng giá cũ."""
    return PRICE_CATALOG.get(product_code)


def check_inventory_and_lead_time(product_code: str, requested_qty: int) -> Dict[str, Any]:
    """Kiểm tra tồn khả dụng và thời gian giao hàng thực tế."""
    inv = INVENTORY_STATUS.get(product_code, {"available_qty": 0, "lead_time_days_if_out": 30})
    is_in_stock = inv["available_qty"] >= requested_qty
    lead_time = 3 if is_in_stock else inv["lead_time_days_if_out"]
    return {
        "available_qty": inv["available_qty"],
        "is_in_stock": is_in_stock,
        "estimated_lead_time_days": lead_time
    }


# ==========================================
# 3. AI AGENT XỬ LÝ YÊU CẦU (OPPORTUNITY PROCESSOR)
# ==========================================

class MinhAnAIAgent:
    def __init__(self, sales_rep_name: str = "Nguyễn Văn Nam"):
        self.sales_rep_name = sales_rep_name

    def process_incoming_request(self, raw_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent thực hiện chuỗi hành động:
        1. Phân tích nội dung (Extract line items, requested discount, budget, timeline)
        2. Validate & Tra cứu giá, tồn kho
        3. Phân luồng duyệt theo thẩm quyền
        4. Tạo hồ sơ cơ hội & Bản nháp phản hồi
        """
        customer_name = raw_request.get("customer_name")
        email = raw_request.get("customer_email")
        content = raw_request.get("request_text")
        requested_discount = raw_request.get("requested_discount_rate", 0.0)
        customer_budget = raw_request.get("budget")
        desired_deadline_days = raw_request.get("desired_deadline_days")

        # Giả lập bóc tách hạng mục (thực tế gọi LLM parse ra JSON các mã sản phẩm)
        extracted_items = raw_request.get("items", [])

        # Kiểm tra tính đầy đủ thông tin (Completeness check)
        missing_info = []
        if not customer_budget:
            missing_info.append("Chưa có thông tin ngân sách dự kiến của khách hàng")
        if not desired_deadline_days:
            missing_info.append("Chưa rõ thời hạn bàn giao/triển khai mong muốn")

        # Tra cứu giá & tồn kho từng hạng mục
        detailed_items = []
        total_list_price = 0
        max_required_lead_time = 0

        for item in extracted_items:
            code = item["product_code"]
            qty = item["quantity"]
            
            cat_info = lookup_catalog_and_price(code)
            if not cat_info:
                continue

            inv_info = check_inventory_and_lead_time(code, qty)
            subtotal = cat_info["unit_price"] * qty
            total_list_price += subtotal
            
            if inv_info["estimated_lead_time_days"] > max_required_lead_time:
                max_required_lead_time = inv_info["estimated_lead_time_days"]

            detailed_items.append({
                "product_code": code,
                "product_name": cat_info["name"],
                "quantity": qty,
                "unit_price": cat_info["unit_price"],
                "subtotal": subtotal,
                "in_stock": inv_info["is_in_stock"],
                "lead_time_days": inv_info["estimated_lead_time_days"]
            })

        # Tính tổng sau chiết khấu
        discount_amount = total_list_price * requested_discount
        final_total = total_list_price - discount_amount

        # Kiểm tra thẩm quyền chiết khấu
        requires_manager_approval = requested_discount > DISCOUNT_APPROVAL_THRESHOLD
        
        # Kiểm tra cảnh báo tiến độ
        timeline_warning = False
        if desired_deadline_days and desired_deadline_days < max_required_lead_time:
            timeline_warning = True

        # Quyết định trạng thái phê duyệt theo sơ đồ quy trình
        if requires_manager_approval:
            approval_status = "Chờ Trưởng phòng duyệt (Chiết khấu > 10%)"
            action_needed = "Gửi email cho Trưởng phòng phê duyệt"
        else:
            approval_status = "Đủ thẩm quyền (Tự động duyệt)"
            action_needed = "Tạo báo giá trên Google Docs"

        # Soạn bản nháp email phản hồi khách hàng
        draft_email = self._generate_customer_email(
            customer_name=customer_name,
            detailed_items=detailed_items,
            final_total=final_total,
            requested_discount=requested_discount,
            max_lead_time=max_required_lead_time,
            timeline_warning=timeline_warning,
            desired_deadline=desired_deadline_days,
            missing_info=missing_info
        )

        return {
            "opportunity_profile": {
                "customer_name": customer_name,
                "customer_email": email,
                "items": detailed_items,
                "total_list_price": total_list_price,
                "requested_discount_rate": f"{requested_discount * 100:.1f}%",
                "final_amount": final_total,
                "budget": customer_budget,
                "feasible_lead_time_days": max_required_lead_time,
                "timeline_warning": timeline_warning,
                "missing_info": missing_info
            },
            "workflow_decision": {
                "requires_manager_approval": requires_manager_approval,
                "approval_status": approval_status,
                "next_step": action_needed
            },
            "draft_email_to_customer": draft_email
        }

    def _generate_customer_email(self, customer_name, detailed_items, final_total, 
                                 requested_discount, max_lead_time, timeline_warning, 
                                 desired_deadline, missing_info) -> str:
        """Tự động sinh email phản hồi chuyên nghiệp."""
        rows_list = []
        for item in detailed_items:
            stock_str = "Sẵn sàng" if item["in_stock"] else f"Đặt hàng ~{item['lead_time_days']} ngày"
            rows_list.append(
                f"  - {item['product_name']} x {item['quantity']} cái: {item['subtotal']:,} VND (Tồn kho: {stock_str})"
            )
        item_rows = "\n".join(rows_list)
        
        lead_time_notice = f"Thời gian triển khai & bàn giao dự kiến: {max_lead_time} ngày làm việc."
        if timeline_warning:
            lead_time_notice += f" (Lưu ý: Quý khách đề xuất {desired_deadline} ngày, tuy nhiên do thiết bị cần thời gian cấu hình & nhập kho đảm bảo chất lượng, Minh An kiến nghị mốc {max_lead_time} ngày)."

        missing_note = ""
        if missing_info:
            missing_note = "\n\nĐể hoàn thiện hồ sơ dự án tối ưu nhất, Minh An xin phép xác nhận thêm:\n" + "\n".join([f"  * {info}" for info in missing_info])

        email_body = f"""Kính gửi Quý khách {customer_name},

Cảm ơn Quý khách đã quan tâm đến giải pháp thiết bị và dịch vụ công nghệ của Công ty Minh An.

Chúng tôi đã tiếp nhận yêu cầu và lập dự toán chi tiết cho các hạng mục sau:
{item_rows}

- Tổng dự toán (đã áp dụng chiết khấu {requested_discount*100:.1f}%): {int(final_total):,} VND (Chưa gồm VAT).
- {lead_time_notice}{missing_note}

Bản báo giá chính thức chi tiết kèm thông số kỹ thuật đã được tạo và gửi kèm đường link bên dưới để Quý khách tiện tra cứu.

Rất mong có cơ hội hợp tác cùng Quý công ty!

Trân trọng,
{self.sales_rep_name} - Phòng Kinh doanh Công ty Minh An
"""
        return email_body


# ==========================================
# 4. CHẠY THỬ NGHIỆM 2 TÌNH HUỐNG THỰC TẾ
# ==========================================

if __name__ == "__main__":
    agent = MinhAnAIAgent(sales_rep_name="Trần Thị Mai")

    # Case 1: Chiết khấu cao (15%) -> Cần duyệt
    test_case_1 = {
        "customer_name": "Công ty Cổ phần Công nghệ TechAsia",
        "customer_email": "procurement@techasia.vn",
        "budget": 150_000_000,
        "desired_deadline_days": 10,
        "requested_discount_rate": 0.15,  # 15% > 10%
        "items": [
            {"product_code": "SRV-DELL-R740", "quantity": 1},
            {"product_code": "SW-CISCO-C9200", "quantity": 1},
            {"product_code": "SVC-SETUP-NW", "quantity": 1}
        ]
    }

    result = agent.process_incoming_request(test_case_1)
    print("=== KẾT QUẢ XỬ LÝ HỒ SƠ 1 ===")
    print(f"Khách hàng: {result['opportunity_profile']['customer_name']}")
    print(f"Tổng tiền sau CK: {result['opportunity_profile']['final_amount']:,} VND")
    print(f"Trạng thái duyệt: {result['workflow_decision']['approval_status']}")
    print(f"Bước tiếp theo: {result['workflow_decision']['next_step']}")
    print("\n--- BẢN NHÁP EMAIL TỰ ĐỘNG ---")
    print(result['draft_email_to_customer'])

