import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
import re

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - PHẦN MỀM BÁO GIÁ NHANH")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

# HÀM TÍNH TOÁN QUY TẮC AN TAM
def calculate_an_tam(w_mm, h_mm, item_type):
    try:
        w_m = float(w_mm) / 1000
        h_m = float(h_mm) / 1000
        
        if "Shutters" in item_type:
            area = max(w_m * h_m, 1.0) # Quy tắc Min 1m2
            return round(area, 2), round(area * 140, 2), "m2"
        elif "Sheer" in item_type:
            return round(w_m, 2), round(w_m * 120, 2), "meters"
        elif "Blockout" in item_type:
            return round(w_m, 2), round(w_m * 145, 2), "meters"
        elif "Vertical" in item_type:
            area = max(w_m * h_m, 1.5) # Quy tắc Min 1.5m2
            return round(area, 2), round(area * 65, 2), "m2"
        else: # Roller Blinds
            area = max(w_m * h_m, 1.5) # Quy tắc Min 1.5m2
            return round(area, 2), round(area * 60, 2), "m2"
    except:
        return 0, 0, "error"

if api_key:
    genai.configure(api_key=api_key)
    # Tự động kết nối Model
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model = genai.GenerativeModel(models[0])
    except:
        st.error("Lỗi kết nối AI. Ông kiểm tra lại mã API nhé!")

    st.sidebar.title("DANH MỤC HÀNG")
    selected_item = st.sidebar.selectbox("Chọn mặt hàng đang tính:", 
        ["Roller ($60/m2)", "Vertical ($65/m2)", "Shutters ($140/m2)", "Sheer Curtains ($120/m)", "Blockout Curtains ($$145/m)"])
    
    st.sidebar.write("---")
    task = st.sidebar.radio("Chế độ:", ["📝 Ghi Số Đo", "🧾 Lưu Invoice (PDF)"])

    if task == "📝 Ghi Số Đo":
        img_file = st.camera_input("CHỤP SỔ ĐO")
        
        if img_file:
            if st.button("🚀 BẮT ĐẦU TÍNH TOÁN"):
                with st.spinner('Đang phân tích số liệu...'):
                    try:
                        img = PIL.Image.open(img_file)
                        # Prompt cực kỳ nghiêm ngặt để AI không ra kết quả linh tinh
                        prompt = "Read address and measurements. Return exactly this format per line: [Location] | [Width] | [Height]. Address on the first line."
                        res = model.generate_content([prompt, img])
                        
                        raw_text = res.text
                        st.subheader("🔍 Dữ liệu thô từ AI:")
                        st.info(raw_text)
                        
                        # --- BỘ LỌC DỮ LIỆU CẢI TIẾN ---
                        rows = []
                        address = "Khach_Hang_An_Tam"
                        
                        # Tìm địa chỉ
                        addr_search = re.search(r'ADDRESS:\s*(.*)', raw_text, re.IGNORECASE)
                        if addr_search:
                            address = addr_search.group(1).split('\n')[0].strip().replace(" ","_")

                        # Tìm các bộ số (bất kể định dạng nào)
                        # Tìm mọi tổ hợp có 2 hoặc 3 số mm (ví dụ: 1525 x 1458)
                        matches = re.findall(r'([^|\n,]+?)\s*[|:]?\s*(\d{3,4})\s*[xX*|]\s*(\d{3,4})', raw_text)
                        
                        for m in matches:
                            loc = m[0].strip().replace("[","").replace("]","")
                            w = m[1]
                            h = m[2]
                            metric, money, unit = calculate_an_tam(w, h, selected_item)
                            rows.append({
                                "Vị trí": loc,
                                "Ngang (mm)": w,
                                "Cao (mm)": h,
                                "Loại rèm": selected_item,
                                f"Tính theo ({unit})": metric,
                                "Thành tiền ($$)": money
                            })
                        
                        if rows:
                            df = pd.DataFrame(rows)
                            st.subheader(f"📊 BẢNG TÍNH GIÁ: {address}")
                            st.table(df)
                            total = df["Thành tiền ($$)"].sum()
                            st.success(f"💰 TỔNG CỘNG: **$${round(total, 2)}**")
                            
                            # Nút tải Excel
                            out_ex = BytesIO()
                            df.to_excel(out_ex, index=False)
                            st.download_button(label=f"📥 TẢI EXCEL [{address}]", data=out_ex.getvalue(), file_name=f"{address}.xlsx")
                        else:
                            st.warning("AI đọc được chữ nhưng không tách được số. Ông chụp rõ số đo Ngang x Cao tí nữa nhé!")
                    
                    except Exception as e:
                        st.error(f"Lỗi AI: {e}")

    else: # INVOICE PDF
        pdf_name = st.text_input("Tên khách:", "Invoice_AnTam")
        inv_img = st.camera_input("CHỤP INVOICE")
        if inv_img:
            from fpdf import FPDF
            pdf = FPDF(); pdf.add_page()
            img_p = PIL.Image.open(inv_img); img_p.save("temp.jpg")
            pdf.image("temp.jpg", x=10, y=10, w=190)
            st.download_button("📥 TẢI PDF INVOICE", pdf.output(dest='S').encode('latin-1'), f"{pdf_name}.pdf")
