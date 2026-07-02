import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ TÍNH BÁO GIÁ")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# HÀM TÍNH TOÁN THEO QUY TẮC JIMMY
def calculate_an_tam(w_mm, h_mm, item_type):
    try:
        w_m = float(w_mm) / 1000
        h_m = float(h_mm) / 1000
        
        if "Shutters" in item_type:
            area = max(w_m * h_m, 1.0)
            return round(area, 2), round(area * 140, 2), "m2"
        elif "Sheer Curtains" in item_type:
            return round(w_m, 2), round(w_m * 120, 2), "meters"
        elif "Blockout Curtains" in item_type:
            return round(w_m, 2), round(w_m * 145, 2), "meters"
        elif "Vertical Blinds" in item_type:
            area = max(w_m * h_m, 1.5)
            return round(area, 2), round(area * 65, 2), "m2"
        else: # Roller Blinds
            area = max(w_m * h_m, 1.5)
            return round(area, 2), round(area * 60, 2), "m2"
    except:
        return 0, 0, "error"

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # --- CÁCH GỌI AI "BẤT BẠI" CHO MÃ AQ ---
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        m_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available else available[0]
        model = genai.GenerativeModel(m_name)

        st.sidebar.title("DANH MỤC")
        task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Tính Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

        if task == "📝 Tính Sổ Đo -> Excel":
            selected_type = st.sidebar.selectbox("Chọn mặt hàng:", 
                ["Roller Blinds ($60/m2)", "Vertical Blinds ($65/m2)", "Shutters ($140/m2)", "Sheer Curtains ($120/m)", "Blockout Curtains ($$145/m)"])
            
            img_file = st.camera_input("CHỤP SỔ ĐO")
            if img_file:
                with st.spinner('Đang đọc và tính tiền...'):
                    img = PIL.Image.open(img_file)
                    # Yêu cầu AI đọc đúng định dạng để tách số
                    prompt = "Read address and measurements. Return format: ADDRESS: [addr] DATA: [Location | Width | Height]"
                    res = model.generate_content([prompt, img])
                    
                    st.write("### 🔍 AI đã đọc được:")
                    st.info(res.text)
                    
                    addr_name = "Khach_Hang_An_Tam"
                    rows = []
                    lines = res.text.split('\n')
                    for line in lines:
                        if "ADDRESS:" in line:
                            addr_name = line.split("ADDRESS:")[1].strip().replace(" ", "_").replace(",", "")
                        elif "|" in line:
                            p = line.split("|")
                            if len(p) >= 3:
                                loc = p[0].strip()
                                # Tìm số mm trong chuỗi
                                w_list = re.findall(r'\d+', p[1])
                                h_list = re.findall(r'\d+', p[2])
                                if w_list and h_list:
                                    metric, money, unit = calculate_an_tam(w_list[0], h_list[0], selected_type)
                                    rows.append({
                                        "Vị trí": loc, "Ngang (mm)": w_list[0], "Cao (mm)": h_list[0],
                                        "Loại": selected_type, f"Lượng tính ({unit})": metric, "Thành tiền ($$)": money
                                    })
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        st.table(df)
                        st.markdown(f"### 💰 TỔNG CỘNG: **${round(df['Thành tiền ($)'].sum(), 2)}**")
                        
                        out_excel = BytesIO()
                        with pd.ExcelWriter(out_excel, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        st.download_button(label=f"📥 TẢI EXCEL [{addr_name}.xlsx]", data=out_excel.getvalue(), file_name=f"{addr_name}.xlsx")

        else: # HÓA ĐƠN PDF
            invoice_name = st.text_input("Tên khách hàng:", "Invoice_AnTam")
            inv_img = st.camera_input("CHỤP INVOICE/RECEIPT")
            if inv_img:
                pdf = FPDF()
                pdf.add_page()
                img_pil = PIL.Image.open(inv_img)
                img_pil.save("temp.jpg")
                pdf.image("temp.jpg", x=10, y=10, w=190)
                st.download_button(label="📥 TẢI PDF VỀ MÁY", data=pdf.output(dest='S').encode('latin-1'), file_name=f"{invoice_name}.pdf")

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
else:
    st.error("Dán mã API vào Secrets nha Jimmy!")
