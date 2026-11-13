"""
AI AGENT - QUY TRÌNH XỬ LÝ CƠ HỘI BÁN HÀNG B2B - MINH AN COMPANY
Mô phỏng chính xác luồng:
1. Tiếp nhận yêu cầu
2. Phân loại & Kiểm tra thông tin -> Có đủ thông tin?
   - Không -> Soạn email yêu cầu KH làm rõ/bổ sung -> Vòng lặp quay lại
   - Có -> Tạo Hồ sơ Cơ hội & Gắn người phụ trách -> Thẩm định tồn kho & giá -> Lập Báo giá & Dự thảo đề xuất
3. Kiểm tra vượt thẩm quyền / Chiết khấu đặc biệt?
   - Có -> Trưởng phòng duyệt
   - Không -> Kết thúc: Cập nhật & Theo dõi
"""

from typing import Dict, Any, List

CATALOG = {
    "LAP-DELL-5520": {"name": "Laptop Dell Latitude 5520 i7/16GB/512GB", "price": 22_500_000},
    "SRV-DELL-R740": {"name": "Server Dell PowerEdge R740 2x Intel Xeon", "price": 85_000_000},
    "SW-CISCO-C9200": {"name": "Switch Cisco Catalyst C9200L 24 Ports PoE+", "price": 28_000_000},
    "SVC-SETUP-NW": {"name": "Dịch vụ Triển khai Mạng văn phòng", "price": 15_000_000},
}

INVENTORY = {
    "LAP-DELL-5520": {"stock": 25, "lead_time_days": 2},
    "SRV-DELL-R740": {"stock": 1, "lead_time_days": 21},
    "SW-CISCO-C9200": {"stock": 10, "lead_time_days": 14},
    "SVC-SETUP-NW": {"stock": 999, "lead_time_days": 2},
}

class B2BOpportunityAgent:
    def __init__(self, assigned_rep: str = "Nguyễn Văn Nam"):
        self.assigned_rep = assigned_rep

    def run_pipeline(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        print("\n--- BƯỚC 1: TIẾP NHẬN YÊU CẦU ---")
        customer_name = raw_input.get("customer_name")
        print(f"Khách hàng: {customer_name}")

        print("\n--- BƯỚC 2: PHÂN LOẠI & KIỂM TRA THÔNG TIN ---")
        items = raw_input.get("items", [])
        budget = raw_input.get("budget")
        deadline = raw_input.get("deadline_days")
        contact = raw_input.get("contact")

        # Kiểm tra điều kiện "Có đủ thông tin?"
        missing = []
        if not items: missing.append("Danh mục sản phẩm / số lượng")
        if not budget: missing.append("Khoảng ngân sách dự kiến")
        if not deadline: missing.append("Thời hạn triển khai mong muốn")
        if not contact: missing.append("Thông tin người liên hệ")

        if missing:
            print(f"[RẼ NHÁNH: KHÔNG] Phát hiện thiếu thông tin: {', '.join(missing)}")
            clarification_email = self.generate_clarification_email(customer_name, missing)
            return {
                "step": "Yêu cầu KH làm rõ / bổ sung",
                "sufficient_info": False,
                "missing_fields": missing,
                "action": "Gửi email đề nghị khách hàng bổ sung",
                "clarification_email": clarification_email
            }

        print("[RẼ NHÁNH: CÓ] Đủ thông tin tiếp nhận B2B!")

        print("\n--- BƯỚC 3: TẠO HỒ SƠ CƠ HỘI & GẮN NGƯỜI PHỤ TRÁCH ---")
        opp_id = f"OPP-MA-{hash(customer_name) % 10000:04d}"
        print(f"Mã Hồ sơ Cơ hội: {opp_id} | Phụ trách: {self.assigned_rep}")

        print("\n--- BƯỚC 4: THẨM ĐỊNH TỒN KHO & GIÁ (NVKD & VẬN HÀNH) ---")
        total_list = 0
        max_lead_time = 0
        verified_items = []

        for it in items:
            code = it["code"]
            qty = it["qty"]
            cat = CATALOG.get(code, {"name": "Thiết bị tùy biến", "price": 10_000_000})
            inv = INVENTORY.get(code, {"stock": 0, "lead_time_days": 30})
            
            subtotal = cat["price"] * qty
            total_list += subtotal
            if inv["lead_time_days"] > max_lead_time:
                max_lead_time = inv["lead_time_days"]

            verified_items.append({
                "code": code,
                "name": cat["name"],
                "qty": qty,
                "unit_price": cat["price"],
                "subtotal": subtotal,
                "in_stock": inv["stock"] >= qty
            })

        print("\n--- BƯỚC 5: LẬP BÁO GIÁ & DỰ THẢO ĐỀ XUẤT ---")
        requested_discount = raw_input.get("discount_rate", 0.0)
        discount_amount = total_list * requested_discount
        final_amount = total_list - discount_amount

        # Kiểm tra vượt thẩm quyền (> 10%)
        requires_manager = requested_discount > 0.10

        if requires_manager:
            print(f"[RẼ NHÁNH: CÓ] Chiết khấu {requested_discount*100:.1f}% vượt thẩm quyền NVKD (10%)!")
            print("Chuyển Trưởng phòng phê duyệt chiết khấu đặc biệt...")
            approval_status = "Chờ Trưởng phòng duyệt"
        else:
            print(f"[RẼ NHÁNH: KHÔNG] Chiết khấu {requested_discount*100:.1f}% đúng thẩm quyền NVKD.")
            approval_status = "Đủ thẩm quyền (Tự động duyệt)"

        print("\n--- BƯỚC 6: KẾT THÚC: CẬP NHẬT & THEO DÕI ---")
        print(f"Deal {opp_id} đã được lưu vào hệ thống CRM. Tự động hẹn lịch follow-up sau 48h.")

        return {
            "step": "Kết thúc: Cập nhật & Theo dõi",
            "opportunity_id": opp_id,
            "sufficient_info": True,
            "assigned_rep": self.assigned_rep,
            "total_list_price": total_list,
            "final_amount": final_amount,
            "discount_rate": requested_discount,
            "requires_manager_approval": requires_manager,
            "approval_status": approval_status,
            "items": verified_items
        }

    def generate_clarification_email(self, customer_name: str, missing_fields: List[str]) -> str:
        fields_str = "\n".join([f"  - {f}" for f in missing_fields])
        return f"""Kính gửi Quý khách {customer_name},

Cảm ơn Quý công ty đã gửi yêu cầu chào giá đến Minh An Company.

Để đội ngũ kỹ thuật và kinh doanh lập phương án tối ưu nhất, Minh An xin phép nhờ Quý khách xác nhận bổ sung thêm:
{fields_str}

Sau khi nhận đủ thông tin, Minh An sẽ lập tức chuyển hồ sơ sang bộ phận Vận hành thẩm định kho và gửi Báo giá chính thức trong vòng 2 giờ làm việc.

Trân trọng,
Bộ phận Hỗ trợ Khách hàng - Minh An Company
"""

if __name__ == "__main__":
    agent = B2BOpportunityAgent(assigned_rep="Nguyễn Văn Nam")
    
    # Test Nhánh 1: Thiếu thông tin
    print("================ KỊCH BẢN 1: THIẾU THÔNG TIN ================")
    req_incomplete = {"customer_name": "Công ty TNHH Á Châu"}
    res1 = agent.run_pipeline(req_incomplete)
    print("\nEmail làm rõ đã tạo:\n" + res1["clarification_email"])

    # Test Nhánh 2: Đầy đủ thông tin & Vượt thẩm quyền chiết khấu
    print("\n================ KỊCH BẢN 2: ĐỦ THÔNG TIN & CK 15% ================")
    req_complete = {
        "customer_name": "Công ty Cổ phần TechAsia",
        "contact": "procurement@techasia.vn",
        "budget": 200_000_000,
        "deadline_days": 14,
        "discount_rate": 0.15,
        "items": [
            {"code": "SRV-DELL-R740", "qty": 1},
            {"code": "SW-CISCO-C9200", "qty": 1}
        ]
    }
    res2 = agent.run_pipeline(req_complete)
    print(f"\nKết quả: {res2['approval_status']} | Tổng tiền: {res2['final_amount']:,} VNĐ")

