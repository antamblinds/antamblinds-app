import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH GIAO DIỆN CHUẨN
st.set_page_config(page_title="An Tam Blinds Master", layout="wide")

# Lấy mã API (Mã AQ)
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

def main():
    st.header("🏠 AN TAM BLINDS - HỆ THỐNG TỰ ĐỘNG")
    
    if not api_key:
        st.error("Jimmy ơi, ông chưa dán mã API vào Secrets kìa!")
        return

    # Cấu hình AI
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # MENU BÊN TRÁI RÕ RÀNG
    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN VIỆC CẦN LÀM:", ["📝 Ghi Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"], key="main_task")

    # --- PHẦN 1: GHI SỔ ĐO (XUẤT EXCEL THEO ĐỊA CHỈ) ---
    if task == "📝 Ghi Sổ Đo -> Excel":
        st.subheader("📝 CHỤP SỔ ĐO (AI tự động bóc số & đặt tên file)")
        # Đặt key riêng biệt để không bị lẫn với Invoice
        img_file = st.camera_input("ĐƯA SỔ ĐO VÀO CAMERA", key="cam_sodo")
        
        if img_file:
            with st.spinner('AI đang đọc và đặt tên file...'):
                try:
                    img = PIL.Image.open(img_file)
                    # Prompt ép AI lấy đúng địa chỉ để làm tên file
                    prompt = "Identify address and measurements. Format: ADDRESS: [addr] DATA: [Location | Width | Height]"
                    res = model.generate_content([prompt, img])
                    raw_text = res.text
                    
                    st.success("✅ AI ĐÃ ĐỌC XONG!")
                    st.text_area("Nội dung AI thấy:", raw_text, height=100)
                    
                    # 🎯 XỬ LÝ TÊN FILE THEO ĐỊA CHỈ
                    file_name = "Khach_Hang_An_Tam"
                    addr_match = re.search(r'ADDRESS:\s*(.*)', raw_text, re.IGNORECASE)
                    if addr_match:
                        # Lấy địa chỉ làm tên file, bỏ dấu phẩy/khoảng trắng cho sạch
                        file_name = addr_match.group(1).split('\n')[0].strip().replace(" ","_").replace(",","")
                    
                    # 🎯 CHUYỂN DỮ LIỆU SANG BẢNG EXCEL
                    rows = []
                    matches = re.findall(r'([^|\n]+?)\s*[|:/xX]\s*(\d{3,4})\s*[|/xX]\s*(\d{3,4})', raw_text)
                    for m in matches:
                        rows.append({"Vị trí": m[0].strip(), "Ngang (mm)": m[1], "Cao (mm)": m[2]})
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        st.table(df)
                        
                        # NÚT TẢI EXCEL (TÊN FILE LÀ ĐỊA CHỈ)
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        
                        st.download_button(
                            label=f"📥 TẢI FILE EXCEL: {file_name}.xlsx",
                            data=output.getvalue(),
                            file_name=f"{file_name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="btn_excel"
                        )
                    else:
                        st.warning("AI đọc được chữ nhưng không thấy số đo mm. Ông chụp gần lại tí nhé!")
                except Exception as e:
                    if "429" in str(e):
                        st.error("AI mệt rồi (429), ông đợi 30 giây rồi chụp lại phát nữa nhé!")
                    else:
                        st.error(f"Lỗi: {e}")

    # --- PHẦN 2: LƯU INVOICE (XUẤT PDF) ---
    else:
        st.subheader("🧾 CHỤP INVOICE (Chuyển sang PDF)")
        cust_name = st.text_input("Nhập tên khách/Địa chỉ để đặt tên file PDF:", "Invoice_AnTam", key="pdf_name_input")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN", key="cam_invoice")
        
        if inv_img:
            with st.spinner('Đang tạo file PDF...'):
                pdf = FPDF()
                pdf.add_page()
                img_p = PIL.Image.open(inv_img)
                img_p.save("temp_inv.jpg")
                pdf.image("temp_inv.jpg", x=10, y=10, w=190)
                
                st.download_button(
                    label=f"📥 TẢI FILE PDF: {cust_name}.pdf",
                    data=pdf.output(dest='S').encode('latin-1'),
                    file_name=f"{cust_name}.pdf",
                    mime="application/pdf",
                    key="btn_pdf"
                )

if __name__ == "__main__":
    main()
