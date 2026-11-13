/**
 * CRM MINH AN - HỆ THỐNG TỰ ĐỘNG HÓA KẾT HỢP AI AGENT
 * Triển khai trên Google Apps Script (gắn với Google Sheets)
 */

// CẤU HÌNH HỆ THỐNG
const CONFIG = {
  GEMINI_API_KEY: "YOUR_GEMINI_API_KEY_HERE",
  GEMINI_MODEL: "gemini-3.8-flash",
  SHEET_NAME_CRM: "Yeu_Cau_CRM",
  SHEET_NAME_PRICING: "Bang_Gia_SP",
  SHEET_NAME_INVENTORY: "Ton_Kho_LeadTime",
  TEMPLATE_DOC_ID: "ID_FILE_GOOGLE_DOCS_MAU_BAO_GIA",
  FOLDER_QUOTES_ID: "ID_THU_MUC_GOOGLE_DRIVE_LUU_BAO_GIA",
  MANAGER_EMAIL: "truongphong.kd@minhan.com.vn",
  DISCOUNT_THRESHOLD: 0.10 // 10%
};

/**
 * 1. AI AGENT: Trích xuất và chuẩn hóa yêu cầu thô từ email/form
 */
function parseRequestWithAI(rawText) {
  const prompt = `
Bạn là AI Trợ lý Kinh doanh của Công ty Minh An. Hãy phân tích yêu cầu chào giá sau và trích xuất JSON:
Nội dung:
"${rawText}"

Trả về đúng JSON theo định dạng sau (không thêm văn bản ngoài JSON):
{
  "customer_name": "Tên khách hàng hoặc tên công ty",
  "customer_email": "Email nếu có",
  "budget": 0 (số tiền VNĐ nếu có, null nếu thiếu),
  "desired_deadline_days": 0 (số ngày muốn nhận, null nếu thiếu),
  "requested_discount": 0.0 (tỉ lệ chiết khấu khách đề nghị ví dụ 0.15 là 15%, 0 nếu không đề cập),
  "items": [
    {"product_code": "Mã sản phẩm tương ứng hoặc gần nhất", "product_name": "Tên sản phẩm", "quantity": 1}
  ],
  "missing_critical_info": ["thông tin thiếu nếu có như ngân sách, thông số kỹ thuật"]
}
`;

  const url = `https://generativelanguage.googleapis.com/v1beta/models/${CONFIG.GEMINI_MODEL}:generateContent?key=${CONFIG.GEMINI_API_KEY}`;
  const payload = {
    contents: [{ parts: [{ text: prompt }] }],
    generationConfig: { responseMimeType: "application/json" }
  };

  const response = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const resJson = JSON.parse(response.getContentText());
  const outputText = resJson.candidates[0].content.parts[0].text;
  return JSON.parse(outputText);
}

/**
 * 2. KIỂM TRA BẢNG GIÁ & TỒN KHO THỰC TẾ (Ngăn chặn giá cũ & hứa sai hạn)
 */
function validatePricingAndInventory(items) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const priceSheet = ss.getSheetByName(CONFIG.SHEET_NAME_PRICING);
  const invSheet = ss.getSheetByName(CONFIG.SHEET_NAME_INVENTORY);
  
  // Đọc bảng giá chuẩn
  const priceData = priceSheet.getDataRange().getValues(); // [Mã SP, Tên SP, Giá]
  const priceMap = {};
  for (let i = 1; i < priceData.length; i++) {
    priceMap[priceData[i][0]] = { name: priceData[i][1], price: Number(priceData[i][2]) };
  }

  // Đọc tồn kho & lead-time
  const invData = invSheet.getDataRange().getValues(); // [Mã SP, Tồn khả dụng, Ngày giao nếu hết]
  const invMap = {};
  for (let i = 1; i < invData.length; i++) {
    invMap[invData[i][0]] = { stock: Number(invData[i][1]), leadTimeOut: Number(invData[i][2]) };
  }

  let totalAmount = 0;
  let maxLeadTime = 0;
  const verifiedItems = [];

  items.forEach(item => {
    const pInfo = priceMap[item.product_code] || { name: item.product_name, price: 0 };
    const iInfo = invMap[item.product_code] || { stock: 0, leadTimeOut: 14 };

    const inStock = iInfo.stock >= item.quantity;
    const leadTime = inStock ? 2 : iInfo.leadTimeOut; // 2 ngày nếu sẵn kho
    if (leadTime > maxLeadTime) maxLeadTime = leadTime;

    const subtotal = pInfo.price * item.quantity;
    totalAmount += subtotal;

    verifiedItems.push({
      code: item.product_code,
      name: pInfo.name,
      quantity: item.quantity,
      unitPrice: pInfo.price,
      subtotal: subtotal,
      leadTime: leadTime
    });
  });

  return {
    verifiedItems: verifiedItems,
    totalAmount: totalAmount,
    feasibleLeadTimeDays: maxLeadTime
  };
}

/**
 * 3. TRIGGER: KHI NVKD CẬP NHẬT HOẶC AI NẠP DỮ LIỆU
 */
function onEditTrigger(e) {
  const sheet = e.source.getActiveSheet();
  if (sheet.getName() !== CONFIG.SHEET_NAME_CRM) return;

  const range = e.range;
  const row = range.getRow();
  if (row <= 1) return; // bỏ qua header

  const colDiscount = 7; // Cột Mức chiết khấu (ví dụ cột G)
  const colStatus = 8;   // Cột Trạng thái duyệt (ví dụ cột H)
  const colCreateQuote = 9; // Cột Checkbox Tạo báo giá (ví dụ cột I)

  const discountRate = parseFloat(sheet.getRange(row, colDiscount).getValue()) || 0;
  const isCreateChecked = sheet.getRange(row, colCreateQuote).getValue();

  // Kiểm tra chiết khấu > 10%
  if (discountRate > CONFIG.DISCOUNT_THRESHOLD) {
    const currentStatus = sheet.getRange(row, colStatus).getValue();
    if (currentStatus !== "Đã duyệt" && currentStatus !== "Hoàn thành (Từ chối)") {
      sheet.getRange(row, colStatus).setValue("Chờ Trưởng phòng duyệt");
      sendApprovalEmailToManager(row, discountRate);
    }
  } else {
    if (!sheet.getRange(row, colStatus).getValue()) {
      sheet.getRange(row, colStatus).setValue("Tự động duyệt (<= 10%)");
    }
  }

  // Khi tích checkbox "Tạo báo giá" (hoặc đã duyệt)
  if (isCreateChecked === true) {
    const currentStatus = sheet.getRange(row, colStatus).getValue();
    if (discountRate > CONFIG.DISCOUNT_THRESHOLD && currentStatus !== "Đã duyệt") {
      Browser.msgBox("Cảnh báo", "Chiết khấu vượt 10% cần Trưởng phòng duyệt trước khi xuất báo giá!", Browser.Buttons.OK);
      sheet.getRange(row, colCreateQuote).setValue(false);
      return;
    }
    generateGoogleDocQuotation(row);
  }
}

/**
 * 4. GỬI EMAIL DUYỆT VỚI NÚT DUYỆT / TỪ CHỐI 1-CHẠM
 */
function sendApprovalEmailToManager(rowIndex, discountRate) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME_CRM);
  const customerName = sheet.getRange(rowIndex, 2).getValue();
  const totalAmount = sheet.getRange(rowIndex, 6).getValue();
  const webAppUrl = ScriptApp.getService().getUrl();

  const approveUrl = `${webAppUrl}?action=approve&row=${rowIndex}`;
  const rejectUrl = `${webAppUrl}?action=reject&row=${rowIndex}`;

  const htmlBody = `
    <h3>YÊU CẦU PHÊ DUYỆT CHIẾT KHẤU VƯỢT THẨM QUYỀN</h3>
    <p><b>Khách hàng:</b> ${customerName}</p>
    <p><b>Tổng giá trị đơn:</b> ${Number(totalAmount).toLocaleString()} VNĐ</p>
    <p><b>Mức chiết khấu đề xuất:</b> <span style="color:red; font-weight:bold;">${(discountRate * 100).toFixed(1)}%</span> (Vượt mức 10%)</p>
    <p>Vui lòng chọn phản hồi:</p>
    <p>
      <a href="${approveUrl}" style="background:#28a745;color:white;padding:10px 15px;text-decoration:none;border-radius:5px;">ĐỒNG Ý DUYỆT</a>
      &nbsp;&nbsp;
      <a href="${rejectUrl}" style="background:#dc3545;color:white;padding:10px 15px;text-decoration:none;border-radius:5px;">TỪ CHỐI</a>
    </p>
  `;

  GmailApp.sendEmail(CONFIG.MANAGER_EMAIL, `[CẦN DUYỆT CK] Khách hàng ${customerName} - ${(discountRate*100).toFixed(1)}%`, "", { htmlBody: htmlBody });
}

/**
 * 5. WEB APP NHẬN PHẢN HỒI DUYỆT TỪ EMAIL TRƯỞNG PHÒNG
 */
function doGet(e) {
  const action = e.parameter.action;
  const row = parseInt(e.parameter.row);
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME_CRM);

  if (action === "approve") {
    sheet.getRange(row, 8).setValue("Đã duyệt");
    // Tự động tích chọn "Tạo báo giá"
    sheet.getRange(row, 9).setValue(true);
    generateGoogleDocQuotation(row);
    return ContentService.createTextOutput("ĐÃ PHÊ DUYỆT THÀNH CÔNG! Báo giá đang được tạo tự động.");
  } else if (action === "reject") {
    sheet.getRange(row, 8).setValue("Hoàn thành (Từ chối)");
    sheet.getRange(row, 9).setValue(false);
    return ContentService.createTextOutput("ĐÃ TỪ CHỐI YÊU CẦU CHIẾT KHẤU!");
  }
  return ContentService.createTextOutput("Thao tác không hợp lệ.");
}

/**
 * 6. TẠO FILE GOOGLE DOCS BÁO GIÁ & GHI URL VÀO SHEETS
 */
function generateGoogleDocQuotation(rowIndex) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME_CRM);
  const customerName = sheet.getRange(rowIndex, 2).getValue();
  const totalAmount = sheet.getRange(rowIndex, 6).getValue();
  
  // Nhân bản file mẫu
  const templateFile = DriveApp.getFileById(CONFIG.TEMPLATE_DOC_ID);
  const destFolder = DriveApp.getFolderById(CONFIG.FOLDER_QUOTES_ID);
  const newFile = templateFile.makeCopy(`Bao_Gia_Minh_An_${customerName}_${Date.now()}`, destFolder);
  const newDoc = DocumentApp.openById(newFile.getId());
  const body = newDoc.getBody();

  // Thay thế dữ liệu
  body.replaceText("{{CUSTOMER_NAME}}", customerName);
  body.replaceText("{{DATE}}", Utilities.formatDate(new Date(), "GMT+7", "dd/MM/yyyy"));
  body.replaceText("{{TOTAL_AMOUNT}}", Number(totalAmount).toLocaleString() + " VNĐ");

  newDoc.saveAndClose();

  // Dán URL vào Sheets (cột 10)
  sheet.getRange(rowIndex, 10).setValue(newFile.getUrl());
}

