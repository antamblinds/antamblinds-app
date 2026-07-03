import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import re

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="An Tam Blinds Pro", layout="wide")
st.header("🏠 AN TAM BLINDS - HỆ THỐNG TỰ ĐỘNG CHUYÊN NGHIỆP")

api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

def main():
    if not api_key:
        st.error("Jimmy ơi, dán API Key vào Secrets nha!")
        return

    # CẤU HÌNH AI
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.sidebar.title("DANH MỤC")
    task = st.sidebar.radio("CHỌN VIỆC:", ["📝 Ghi Sổ Đo -> Excel", "🧾 Lưu Invoice -> PDF"])

    # --- PHẦN 1: GHI SỔ ĐO (THEO ĐÚNG HÌNH ÔNG GỬI) ---
    if task == "📝 Ghi Sổ Đo -> Excel":
        st.subheader("📝 CHỤP SỔ ĐO (AI TỰ TÍNH DIỆN TÍCH & ĐẶT TÊN THEO ĐỊA CHỈ)")
        img_file = st.camera_input("CHỤP TỜ GIẤY ĐO", key="cam_sodo")
        
        if img_file:
            with st.spinner('AI đang bóc tách số liệu và tính toán Diện tích...'):
                try:
                    img = PIL.Image.open(img_file)
                    prompt = "Identify address and measurements. For each door: Location | Width | Height | Notes. Address on top."
                    res = model.generate_content([prompt, img])
                    raw = res.text
                    
                    # 🎯 TÌM ĐỊA CHỈ ĐỂ ĐẶT TÊN FILE
                    f_name = "Khach_An_Tam"
                    addr_match = re.search(r'(Address:|Địa chỉ:|Dia chi:)\s*(.*)', raw, re.IGNORECASE)
                    if addr_match:
                        f_name = addr_match.group(2).split('\n')[0].strip().replace(" ","_").replace(",","")

                    # 🎯 TẠO BẢNG THEO ĐÚNG HÌNH ẢNH MẪU
                    rows = []
                    lines = raw.split('\n')
                    don_gia_mac_dinh = 100 # Ông có thể sửa số này
                    
                    for line in lines:
                        match = re.search(r'(\d{3,4})\s*[xX*/-]\s*(\d{3,4})', line)
                        if match:
                            w_mm = int(match.group(1))
                            h_mm = int(match.group(2))
                            # Bóc vị trí và ghi chú
                            loc = line.split(match.group(0))[0].strip().replace("-","").replace(".","")
                            notes = line.split(match.group(0))[1].strip().replace("(","").replace(")","").replace(" ","")
                            
                            # Tính diện tích (m2)
                            dien_tich = round((w_mm / 1000) * (h_mm / 1000), 2)
                            # Quy tắc Min 1.5m2 cho Roller/Vertical (Ông có thể bỏ nếu muốn tính thực tế)
                            dien_tich_tinh_tien = max(dien_tich, 1.5) 
                            thanh_tien = round(dien_tich_tinh_tien * don_gia_mac_dinh, 2)
                            
                            rows.append({
                                "Vị trí": loc if loc else "Cửa",
                                "Rộng (mm)": w_mm,
                                "Cao (mm)": h_mm,
                                "Kích thước gốc": f"{w_mm}/{h_mm}.{notes}",
                                "Diện tích thực": dien_tich,
                                "Diện tích tính tiền": dien_tich_tinh_tien,
                                "Đơn giá": don_gia_mac_dinh,
                                "Thành tiền": thanh_tien,
                                "Ghi chú": notes
                            })
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        st.table(df) # Hiện bảng đẹp như hình ông gửi
                        
                        out_ex = BytesIO()
                        with pd.ExcelWriter(out_ex, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        
                        st.download_button(
                            label=f"📥 TẢI EXCEL: {f_name}.xlsx",
                            data=out_ex.getvalue(),
                            file_name=f"{f_name}.xlsx"
                        )
                    else:
                        st.warning("AI không thấy số đo mm. Ông chụp rõ hơn nhé!")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    # --- PHẦN 2: LƯU INVOICE (QUÉT TÊN CÔNG TY CẤP HÀNG) ---
    else:
        st.subheader("🧾 CHỤP INVOICE (AI TỰ ĐẶT TÊN FILE THEO NHÀ CUNG CẤP)")
        inv_img = st.camera_input("CHỤP HÓA ĐƠN/BIÊN LAI", key="cam_inv")
        
        if inv_img:
            with st.spinner('AI đang tìm tên công ty trên hóa đơn...'):
                try:
                    img = PIL.Image.open(inv_img)
                    # Prompt bắt AI tìm tên Supplier
                    res_inv = model.generate_content(["Find only the Supplier/Company Name on this receipt. Be concise.", img])
                    supplier_name = res_inv.text.strip().replace(" ","_").replace(".","")
                    if not supplier_name or len(supplier_name) > 30: # Phòng khi AI nói dài dòng
                        supplier_name = "Invoice_AnTam"
                    
                    st.success(f"✅ Đã tìm thấy Nhà cung cấp: {supplier_name}")
                    
                    # TẠO PDF
                    pdf = FPDF(); pdf.add_page()
                    img.save("temp_inv.jpg")
                    pdf.image("temp_inv.jpg", x=10, y=10, w=190)
                    
                    st.download_button(
                        label=f"📥 TẢI PDF: {supplier_name}.pdf",
                        data=pdf.output(dest='S').encode('latin-1'),
                        file_name=f"{supplier_name}.pdf"
                    )
                except Exception as e_pdf:
                    st.error(f"Lỗi: {e_pdf}")

if __name__ == "__main__":
    main()
