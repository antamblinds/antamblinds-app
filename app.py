import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO

# --- CHẾ ĐỘ TỰ ĐỘNG MỞ KÉT SẮT (SECRETS) ---
# Ưu tiên lấy mã từ Secrets trước, nếu không có mới hiện ô nhập
api_key = st.secrets.get("GEMINI_API_KEY")

st.set_page_config(page_title="An Tam Blinds Pro", layout="centered")
st.header("🏠 An Tam Blinds - Hệ Thống Tự Động")

# Nếu trong Secrets chưa có mã, mới hiện ô nhập ở bên trái
if not api_key:
    with st.sidebar:
        st.warning("Chưa tìm thấy mã trong Secrets!")
        api_key = st.text_input("Dán Google API Key vào đây để dùng tạm:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Tự động lấy bộ não AI
        raw_m = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in raw_m if "1.5-flash" in m), raw_m[0])
        model = genai.GenerativeModel(model_name)
        
        if st.secrets.get("GEMINI_API_KEY"):
            st.sidebar.success("✅ Đã kết nối tự động từ Secrets!")
        else:
            st.sidebar.info("⚠️ Đang dùng mã dán tạm thời")

        # Giao diện chính của Jimmy
        task = st.radio("Ông muốn làm gì?", ["Ghi Sổ Đo (.l.kc)", "Chụp Hóa Đơn (Invoices)"])

        if task == "Ghi Sổ Đo (.l.kc)":
            uploaded_file = st.camera_input("Chụp ảnh sổ đo rèm")
            if uploaded_file:
                with st.spinner('AI An Tam đang đọc dữ liệu sạch...'):
                    image = PIL.Image.open(uploaded_file)
                    
                    # Lệnh vắt kiệt AI để ra định dạng chuẩn của Jimmy
                    prompt = """
                    Bạn là thư ký của An Tam Blinds. Hãy đọc ảnh sổ đo và liệt kê:
                    1. Địa chỉ công trình.
                    2. Kích thước TRÌNH BÀY ĐÚNG DẠNG: Rộng/Cao.l.kc (Ví dụ: 1525/1458.l.kc)
                    3. Hướng L/R và Tên Vải.
                    Lưu ý: TUYỆT ĐỐI không ghi 'Mục 1', 'Hạng mục'. Chỉ liệt kê danh sách sạch. Trả về tiếng Việt.
                    """
                    response = model.generate_content([prompt, image])
                    st.subheader("📋 DỮ LIỆU ĐƠN HÀNG:")
                    st.code(response.text, language="text")
                    
                    # Tạo file Excel để tải về
                    df = pd.DataFrame([{"DonHang": response.text}])
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    st.download_button("📥 Tải File Excel", output.getvalue(), file_name="AnTam_DonHang.xlsx")
        else:
            st.camera_input("Chụp ảnh hóa đơn mua hàng (Invoices)")
            st.info("Khi ông chụp, ảnh sẽ hiện ra để ông lưu vào Drive.")

    except Exception as e:
        st.error(f"Lỗi: {e}")
else:
    st.warning("Jimmy ơi, hãy dán API Key vào Secrets hoặc ô bên trái để bắt đầu!")
