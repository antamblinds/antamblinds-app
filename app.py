import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ TÍNH GIÁ NHANH")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# HÀM TÍNH TOÁN THEO YÊU CẦU CỦA JIMMY
def calculate_an_tam(w_mm, h_mm, item_type):
    try:
        w_m = float(w_mm) / 1000
        h_m = float(h_mm) / 1000
        
        if "Shutters" in item_type:
            area = max(w_m * h_m, 1.0) # Min 1m2
            return round(area, 2), round(area * 140, 2), "m2"
        elif "Sheer Curtains" in item_type:
            return round(w_m, 2), round(w_m * 120, 2), "meters"
        elif "Blockout Curtains" in item_type:
            return round(w_m, 2), round(w_m * 145, 2), "meters"
        elif "Vertical Blinds" in item_type:
            area = max(w_m * h_m, 1.5) # Min 1.5m2
            return round(area, 2), round(area * 65, 2), "m2"
        else: # Roller Blinds
            area = max(w_m * h_m, 1.5) # Min 1.5m2
            return round(area, 2), round(area * 60, 2), "m2"
    except:
        return 0, 0, "error"

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Tự động chọn Model để tránh lỗi NotFound
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model = genai.GenerativeModel(models[0])

        st.sidebar.title("DANH MỤC")
        task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Tính Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

        if task == "📝 Tính Sổ Đo -> Excel":
            selected_type = st.sidebar.selectbox("Chọn loại rèm:", 
                ["Roller Blinds ($60/m2)", "Vertical Blinds ($65/m2)", "Shutters ($140/m2)", "Sheer Curtains ($120/m)", "Blockout Curtains ($$145/m)"])
            
            img_file = st.camera_input("CHỤP SỔ ĐO")
            if img_file:
                with st.spinner('Đang đọc số và tính tiền...'):
                    img = PIL.Image.open(img_file)
                    # Ra lệnh AI tách từng hàng rõ ràng
                    prompt = "Read address and measurements. Return format: ADDRESS: [addr] DATA: [Location | Width | Height]"
                    res = model.generate_content([prompt, img])
                    
                    st.write("### 🔍 AI đã đọc được:")
                    st.info(res.text)
                    
                    addr = "Khach_Hang_An_Tam"
                    rows = []
                    for line in res.text.split('\n'):
                        if "ADDRESS:" in line:
                            addr = line.split("ADDRESS:")[1].strip().replace(" ", "_").replace(",", "")
                        elif "|" in line:
                            p = line.split("|")
                            if len(p) >= 3:
                                w_match = re.findall(r'\d+', p[1])
                                h_match = re.findall(r'\d+', p[2])
                                if w_match and h_match:
                                    metric, money, unit = calculate_an_tam(w_match[0], h_match[0], selected_type)
                                    rows.append({
                                        "Vị trí": p[0].strip(), "Ngang (mm)": w_match[0], "Cao (mm)": h_match[0],
                                        "Loại": selected_type, f"Đơn vị ({unit})": metric, "Thành tiền ($$)": money
                                    })
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        st.table(df)
                        st.success(f"💰 TỔNG TIỀN: ${round(df['Thành tiền ($)'].sum(), 2)}")
                        
                        # NÚT TẢI EXCEL VỀ MÁY
                        out_ex = BytesIO()
                        with pd.ExcelWriter(out_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        st.download_button(label=f"📥 TẢI EXCEL [{addr}.xlsx]", data=out_ex.getvalue(), file_name=f"{addr}.xlsx")

        else: # XỬ LÝ PDF INVOICE
            pdf_user_name = st.text_input("Nhập tên khách hàng:", "Invoice_AnTam")
            inv_img = st.camera_input("CHỤP HÓA ĐƠN")
            if inv_img:
                pdf = FPDF()
                pdf.add_page()
                img_pil = PIL.Image.open(inv_img)
                img_pil.save("temp_inv.jpg")
                pdf.image("temp_inv.jpg", x=10, y=10, w=190)
                st.download_button(label="📥 TẢI PDF VỀ MÁY", data=pdf.output(dest='S').encode('latin-1'), file_name=f"{pdf_user_name}.pdf")

    except Exception as e:
        if "429" in str(e):
            st.warning("AI đang nghỉ ngơi chút xíu. Jimmy đợi khoảng 30 giây rồi hãy nhấn chụp lại nhé!")
        else:
            st.error(f"Lỗi: {e}")
else:
    st.error("Chưa thấy mã API trong Secrets!")
