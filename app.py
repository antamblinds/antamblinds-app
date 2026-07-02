import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - HỆ THỐNG TÍNH GIÁ CHUẨN")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# HÀM TÍNH TOÁN "ĐỘC QUYỀN" CỦA JIMMY
def calculate_an_tam(w_mm, h_mm, item_type):
    w_m = float(w_mm) / 1000
    h_m = float(h_mm) / 1000
    
    if "Shutters" in item_type:
        area = max(w_m * h_m, 1.0) # Quy tắc Min 1m2
        return round(area, 2), round(area * 140, 2), "m2"
    
    elif "Sheer Curtains" in item_type:
        width_only = w_m # Chỉ lấy tổng Width
        return round(width_only, 2), round(width_only * 120, 2), "meters"
        
    elif "Blockout Curtains" in item_type:
        width_only = w_m # Chỉ lấy tổng Width
        return round(width_only, 2), round(width_only * 145, 2), "meters"
        
    elif "Vertical Blinds" in item_type:
        area = max(w_m * h_m, 1.5) # Quy tắc Min 1.5m2
        return round(area, 2), round(area * 65, 2), "m2"
        
    else: # Roller Blinds
        area = max(w_m * h_m, 1.5) # Quy tắc Min 1.5m2
        return round(area, 2), round(area * 60, 2), "m2"

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN LOẠI FILE:", ["📝 Sổ Đo -> Excel", "🧾 Invoice -> PDF"])

    if task == "📝 Sổ Đo -> Excel":
        selected_type = st.sidebar.selectbox("Chọn loại mặt hàng:", 
            ["Roller Blinds ($$60/m2)", "Vertical Blinds ($65/m2)", "Shutters ($140/m2)", "Sheer Curtains ($120/m)", "Blockout Curtains ($145/m)"])
        
        img_file = st.camera_input("CHỤP SỔ ĐO")
        
        if img_file:
            with st.spinner('AI đang tính toán chi phí...'):
                img = PIL.Image.open(img_file)
                prompt = "Read address and measurements. Return format: ADDRESS: [address] DATA: [Location | Width | Height]"
                response = model.generate_content([prompt, img])
                
                st.write("### 🔍 AI đã đọc được:")
                st.info(response.text)
                
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
                            # Áp dụng tính toán
                            metric, money, unit = calculate_an_tam(w, h, selected_type)
                            rows.append({
                                "Vị trí": loc,
                                "Ngang (mm)": w,
                                "Cao (mm)": h,
                                "Loại": selected_type,
                                f"Lượng tính ({unit})": metric,
                                "Thành tiền ($$)": money
                            })
                
                if rows:
                    df = pd.DataFrame(rows)
                    st.table(df)
                    st.markdown(f"### 💰 TỔNG CỘNG: **$${round(df['Thành tiền ($)'].sum(), 2)}**")
                    
                    out_excel = BytesIO()
                    with pd.ExcelWriter(out_excel, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    st.download_button(
                        label=f"📥 TẢI FILE EXCEL [{addr_name}.xlsx]",
                        data=out_excel.getvalue(),
                        file_name=f"{addr_name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    else: # PHẦN INVOICE (PDF)
        pdf_name = st.text_input("Tên khách / Số Invoice:", "Invoice_AnTam")
        inv_img = st.camera_input("CHỤP INVOICE/RECEIPT")
        
        if inv_img:
            with st.spinner('Đang tạo PDF...'):
                pdf = FPDF()
                pdf.add_page()
                img_pil = PIL.Image.open(inv_img)
                img_path = "temp_inv.jpg"
                img_pil.save(img_path)
                pdf.image(img_path, x=10, y=10, w=190)
                pdf_output = pdf.output(dest='S').encode('latin-1')
                
                st.download_button(
                    label=f"📥 TẢI FILE PDF [{pdf_name}.pdf]",
                    data=pdf_output,
                    file_name=f"{pdf_name}.pdf",
                    mime="application/pdf"
                )
else:
    st.error("Dán mã API vào Secrets đi Jimmy!")
