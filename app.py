import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH HUB
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - CÔNG CỤ TỰ ĐỘNG")

# Lấy mã API (Mã AQ)
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

def main():
    if not api_key:
        st.error("Jimmy ơi, ông chưa dán mã API vào Secrets kìa!")
        return

    # --- CẤU HÌNH AI (VÁ LỖI 404) ---
    try:
        genai.configure(api_key=api_key)
        # Tự động tìm model Flash khả dụng
        available_models = [m.name for m in genai.list_models() 
                           if 'generateContent' in m.supported_generation_methods 
                           and 'flash' in m.name.lower()]
        
        # Nếu tìm thấy thì dùng, không thì dùng mặc định
        model_id = available_models[0] if available_models else 'gemini-1.5-flash'
        model = genai.GenerativeModel(model_id)
    except Exception as e:
        st.error(f"Lỗi kết nối AI: {e}")
        return

    # MENU BÊN TRÁI
    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Ghi Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"], key="task_selector")

    # --- PHẦN 1: GHI SỔ ĐO ---
    if task == "📝 Ghi Sổ Đo -> Excel":
        st.subheader("📝 CHỤP SỔ ĐO (AI TỰ ĐẶT TÊN FILE THEO ĐỊA CHỈ)")
        # Camera riêng cho sổ đo
        img_file = st.camera_input("CHỤP TỜ GIẤY ĐO", key="camera_sodo")
        
        if img_file:
            with st.spinner('AI đang bóc tách số liệu và địa chỉ...'):
                try:
                    img = PIL.Image.open(img_file)
                    # Prompt ép AI lấy địa chỉ làm tên file
                    prompt = "Identify the job address and measurements. Format: ADDRESS: [addr] DATA: [Location | Width | Height]"
                    res = model.generate_content([prompt, img])
                    raw_text = res.text
                    
                    st.success("✅ ĐÃ ĐỌC XONG!")
                    st.info(raw_text)
                    
                    # 🎯 TÌM ĐỊA CHỈ ĐỂ ĐẶT TÊN FILE
                    file_name = "Khach_Hang_An_Tam"
                    addr_match = re.search(r'ADDRESS:\s*(.*)', raw_text, re.IGNORECASE)
                    if addr_match:
                        file_name = addr_match.group(1).split('\n')[0].strip().replace(" ","_").replace(",","")
                    
                    # 🎯 BÓC TÁCH SỐ ĐO
                    rows = []
                    matches = re.findall(r'([^|\n]+?)\s*[|:/xX]\s*(\d{3,4})\s*[|/xX]\s*(\d{3,4})', raw_text)
                    for m in matches:
                        rows.append({"Vị trí": m[0].strip(), "Ngang (mm)": m[1], "Cao (mm)": m[2]})
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        st.table(df)
                        
                        # XUẤT EXCEL
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        
                        # Nút tải file với tên là địa chỉ
                        st.download_button(
                            label=f"📥 TẢI FILE EXCEL: {file_name}.xlsx",
                            data=output.getvalue(),
                            file_name=f"{file_name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_excel"
                        )
                    else:
                        st.warning("AI không thấy số đo Ngang x Cao. Ông chụp gần lại tí nhé!")
                except Exception as ex:
                    st.error(f"Lỗi: {ex}")

    # --- PHẦN 2: LƯU INVOICE ---
    else:
        st.subheader("🧾 CHUYỂN INVOICE/RECEIPT SANG PDF")
        pdf_name = st.text_input("Nhập tên khách/địa chỉ để lưu file:", "Invoice_AnTam")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN", key="camera_inv")
        
        if inv_img:
            with st.spinner('Đang tạo PDF...'):
                pdf = FPDF()
                pdf.add_page()
                img_p = PIL.Image.open(inv_img)
                img_p.save("temp.jpg")
                pdf.image("temp.jpg", x=10, y=10, w=190)
                
                st.download_button(
                    label=f"📥 TẢI FILE PDF: {pdf_name}.pdf",
                    data=pdf.output(dest='S').encode('latin-1'),
                    file_name=f"{pdf_name}.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )

if __name__ == "__main__":
    main()
