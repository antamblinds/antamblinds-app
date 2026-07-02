import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="An Tam Blinds Cloud", layout="wide")
st.header("🏠 AN TAM BLINDS - HỆ THỐNG OCR & BÁO GIÁ")

# Lấy mã API của Jimmy
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# Hàm tính M2 theo quy tắc Jimmy (Min 1.5m2)
def calculate_details(w_mm, h_mm, type_blind):
    w_m = float(w_mm) / 1000
    h_m = float(h_mm) / 1000
    area = w_m * h_m
    final_area = max(area, 1.5) # Quy tắc 1.5m2
    
    price_unit = 65 if "Vertical" in type_blind else 60
    total = final_area * price_unit
    return round(final_area, 2), round(total, 2)

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.sidebar.title("MENU HÀNH ĐỘNG")
    task = st.sidebar.radio("CHỌN LOẠI FILE:", ["📝 Ghi Sổ Đo -> Excel", "🧾 Lưu Invoice/Receipt -> PDF"])

    # --- PHẦN 1: XỬ LÝ SỔ ĐO (EXCEL) ---
    if task == "📝 Ghi Sổ Đo -> Excel":
        blind_type = st.sidebar.selectbox("Loại màn:", ["Roller Blinds ($60/m2)", "Vertical Blinds ($65/m2)"])
        img_file = st.camera_input("CHỤP SỔ ĐO")
        
        if img_file:
            with st.spinner('AI đang đọc số đo...'):
                img = PIL.Image.open(img_file)
                prompt = "Read address and measurements. Return format: ADDRESS: [address] DATA: [Location | Width | Height]"
                response = model.generate_content([prompt, img])
                
                # Hiển thị kết quả AI đọc
                st.write("### 🔍 AI đã đọc được:")
                st.info(response.text)
                
                # Tách dữ liệu
                addr_name = "Khach_Hang_An_Tam"
                rows = []
                lines = response.text.split('\n')
                for line in lines:
                    if "ADDRESS:" in line:
                        addr_name = line.split("ADDRESS:")[1].strip().replace(" ", "_").replace(",", "")
                    elif "|" in line:
                        p = line.split("|")
                        if len(p) >= 3:
                            loc = p[0].strip()
                            w = re.findall(r'\d+', p[1])[0]
                            h = re.findall(r'\d+', p[2])[0]
                            m2, money = calculate_details(w, h, blind_type)
                            rows.append({
                                "Vị trí": loc,
                                "Ngang (mm)": w,
                                "Cao (mm)": h,
                                "Loại màn": blind_type,
                                "M2 (Min 1.5)": m2,
                                "Thành tiền ($$)": money
                            })
                
                if rows:
                    df = pd.DataFrame(rows)
                    st.table(df)
                    st.write(f"**💰 Tổng cộng: $${df['Thành tiền ($)'].sum()}**")
                    
                    # Tạo file Excel
                    out_excel = BytesIO()
                    with pd.ExcelWriter(out_excel, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    st.download_button(
                        label=f"📥 TẢI EXCEL [{addr_name}.xlsx]",
                        data=out_excel.getvalue(),
                        file_name=f"{addr_name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    # --- PHẦN 2: XỬ LÝ INVOICE & RECEIPTS (PDF) ---
    else:
        # Cho phép Jimmy nhập tên khách để đặt tên file PDF cho dễ nhớ
        pdf_name = st.text_input("Nhập tên khách/Địa chỉ (để đặt tên file PDF):", "Invoice_Receipt")
        inv_img = st.camera_input("CHỤP INVOICE HOẶC RECEIPT")
        
        if inv_img:
            with st.spinner('Đang tạo file PDF chất lượng cao...'):
                # Dùng FPDF tạo PDF từ ảnh
                pdf = FPDF()
                pdf.add_page()
                # Mở ảnh và lấy kích thước
                img_pil = PIL.Image.open(inv_img)
                # Lưu tạm ảnh để PDF đọc
                img_path = "temp_inv.jpg"
                img_pil.save(img_path)
                # Chèn ảnh vào PDF (scale vừa trang A4)
                pdf.image(img_path, x=10, y=10, w=190)
                pdf_output = pdf.output(dest='S').encode('latin-1')
                
                st.success("✅ Đã chuyển đổi thành PDF thành công!")
                st.download_button(
                    label=f"📥 TẢI FILE PDF [{pdf_name}.pdf]",
                    data=pdf_output,
                    file_name=f"{pdf_name}.pdf",
                    mime="application/pdf"
                )

else:
    st.error("Chưa cấu hình API Key trong Secrets nha Jimmy!")
