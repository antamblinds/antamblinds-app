import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Formater", layout="wide")
st.header("🏠 AN TAM BLINDS - QUOTE FORMATER")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

def main():
    if not api_key:
        st.error("Jimmy ơi, dán API Key vào Secrets nhé!")
        return

    # TỰ DÒ MODEL ĐỂ KHÔNG LỖI 404
    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_id = next((m for m in available_models if 'flash' in m.lower()), available_models[0])
        model = genai.GenerativeModel(model_id)
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
        return

    st.sidebar.title("MENU")
    task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Ghi Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

    if task == "📝 Ghi Sổ Đo -> Excel":
        st.subheader("📝 CHỤP SỔ ĐO (Format: Width/Height.Notes)")
        img_file = st.camera_input("CHỤP TỜ GIẤY ĐO", key="cam_sodo")
        
        if img_file:
            with st.spinner('Đang đọc số...'):
                try:
                    img = PIL.Image.open(img_file)
                    # Prompt ép AI lấy đúng các thành phần
                    prompt = """Identify the address and measurements. 
                    For each dimension, extract: Location, Width, Height, and trailing notes.
                    Format exactly: ADDRESS: [addr] DATA: [Location | Width | Height | Notes]"""
                    
                    res = model.generate_content([prompt, img])
                    raw = res.text
                    
                    st.success("✅ ĐÃ ĐỌC XONG!")

                    # 🎯 TÌM ĐỊA CHỈ LÀM TÊN FILE
                    f_name = "Khach_An_Tam"
                    addr_match = re.search(r'ADDRESS:\s*(.*)', raw, re.IGNORECASE)
                    if addr_match:
                        f_name = addr_match.group(1).split('\n')[0].strip().replace(" ","_").replace(",","")
                    
                    # 🎯 XỬ LÝ DỮ LIỆU THEO PHONG CÁCH JIMMY
                    rows = []
                    matches = re.findall(r'([^|\n]+?)\s*[|]\s*(\d{3,4})\s*[|/xX*]\s*(\d{3,4})\s*[|]?\s*([^|\n]*)', raw)
                    
                    for m in matches:
                        loc = m[0].strip().replace("DATA:", "").strip()
                        w = m[1]
                        h = m[2]
                        # 💥 LÀM SẠCH GHI CHÚ: Bỏ ngoặc, bỏ khoảng trắng để gom cụm (L) kc -> Lkc
                        notes = m[3].strip().replace("(", "").replace(")", "").replace(" ", "")
                        
                        # TẠO FILE FORMAT: 1525/1458.Lkc
                        jimmy_format = f"{w}/{h}"
                        if notes:
                            jimmy_format += f".{notes}"
                        
                        rows.append({
                            "Vị trí": loc,
                            "Quote Format (Copy)": jimmy_format
                        })
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        st.table(df) # Hiện bảng 
                        
                        # XUẤT EXCEL
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        
                        st.download_button(
                            label=f"📥 TẢI EXCEL: {f_name}.xlsx",
                            data=output.getvalue(),
                            file_name=f"{f_name}.xlsx"
                        )
                    else:
                        st.warning("Không tách được số. Ông chụp gần và rõ hơn tí nhé!")
                        st.info(raw)
                except Exception as ex:
                    st.error(f"Lỗi: {ex}")

    else: # INVOICE
        st.subheader("🧾 CHỤP INVOICE (Xuất PDF)")
        pdf_n = st.text_input("Ghi tên khách/Địa chỉ:", "Invoice_AnTam")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN", key="cam_inv")
        if inv_img:
            pdf = FPDF(); pdf.add_page()
            img_p = PIL.Image.open(inv_img); img_p.save("temp.jpg")
            pdf.image("temp.jpg", x=10, y=10, w=190)
            st.download_button(f"📥 TẢI PDF: {pdf_n}", pdf.output(dest='S').encode('latin-1'), f"{pdf_n}.pdf")

if __name__ == "__main__":
    main()
