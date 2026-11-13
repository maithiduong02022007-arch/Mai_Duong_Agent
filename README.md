# MINH AN TECHNOLOGY - AI AGENT CRM (LOCALHOST)

Hệ thống AI Agent tự động hóa xử lý 180 yêu cầu/tuần cho 6 Nhân viên Kinh doanh theo đúng sơ đồ CRM Minh An.

---

## 🚀 Cách 1: Chạy Ngay Trên Localhost (Không Cần Cài Đặt Thêm - 1 Click)

Windows đã tích hợp sẵn PowerShell, bạn chỉ cần:

1. Click đúp vào file **`run.bat`** trong thư mục này.
2. Trình duyệt sẽ tự động mở trang web quản trị tại: **`http://localhost:8080`**
3. Trên giao diện, bạn có thể:
   - Chọn các **Kịch bản mẫu nhanh (Case 1, Case 2, Case 3)** hoặc dán email của khách.
   - Nhấn **"KÍCH HOẠT AI AGENT PHÂN TÍCH"**.
   - Trải nghiệm toàn bộ luồng:
     - Tự động bóc tách và đối soát giá niêm yết + tồn khả dụng.
     - Luồng duyệt Trưởng phòng khi chiết khấu $> 10\%$ với nút **Đồng ý / Từ chối**.
     - Xuất bản Báo giá (Docs) và Bản nháp Email phản hồi khách hàng.

---

## 🐍 Cách 2: Chạy Backend bằng Python (FastAPI)

Nếu bạn có môi trường Python:

```bash
# 1. Cài thư viện
pip install -r requirements.txt

# 2. Khởi động FastAPI server
python -m uvicorn app_fastapi:app --reload --port 8000
```
Truy cập Swagger API Docs tại: `http://localhost:8000/docs`

---

## ☁️ Cách 3: Tích hợp vào Google Sheets & Gmail Thực Tế

Xem file **`minh_an_apps_script.js`** để copy trực tiếp vào Google Sheets Script Editor theo sơ đồ ban đầu.

