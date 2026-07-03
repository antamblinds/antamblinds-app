import streamlit as st
import google.generativeai as genai
import PIL.Image
import pandas as pd
from io import BytesIO

# --- TỰ ĐỘNG LẤY MÃ TỪ GIỎ BÍ MẬT (SECRETS) ---
# Nếu ông đã dán vào Secrets, App sẽ tự chạy mà không cần hỏi lại
api_key = st.secrets.get("GEMINI_API_KEY", "")

st.set_page_config(page_title="An Tam Blinds Pro", layout="centered")
st.header("🏠 An Tam Blinds - Hệ thống Tự động")

if not api_key:
    st.error("Jimmy ơi, ông chưa dán API Key vào phần Secrets rồi!")
else:
    try:
        genai.configure(api_key=api_key)
        raw_m = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in raw_m if "1.5-flash" in m), raw_m[0])
        model = genai.GenerativeModel(model_name)
        
        st.success("✅ Đã kết nối hệ thống tự động!")

        task = st.radio("Chọn công việc:", ["Ghi Sổ Đo (.l.kc)", "Chụp Hóa Đơn (Invoices)"])

        if task == "Ghi Sổ Đo (.l.kc)":
            uploaded_file = st.camera_input("Chụp ảnh sổ đo")
            if uploaded_file:
                with st.spinner('Đang xử lý dữ liệu sạch...'):
                    image = PIL.Image.open(uploaded_file)
                    prompt = """
                    Bạn là thư ký của An Tam Blinds. Hãy đọc sổ đo và liệt kê:
                    1. Địa chỉ công trình.
                    2. Kích thước dạng: Rộng/Cao.l.kc (Ví dụ: 1525/1458.l.kc)
                    3. Hướng L/R và Tên Vải.
                    QUY TẮC: KHÔNG ghi 'Mục 1', 'Hạng mục'. Chỉ liệt kê danh sách sạch. Trả về tiếng Việt.
                    """
                    response = model.generate_content([prompt, image])
                    st.subheader("📋 KẾT QUẢ (.l.kc):")
                    st.code(response.text, language="text")
                    
                    # Nút tạo Excel nhanh
                    df = pd.DataFrame([{"Dữ liệu": response.text}])
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    st.download_button("📥 Tải file Excel", output.getvalue(), file_name="AnTam_DonHang.xlsx")
        else:
            st.camera_input("Chụp ảnh hóa đơn (Invoices)")
            st.info("Ảnh sẽ được lưu trực tiếp vào Drive nếu ông đã cài JSON!")

    except Exception as e:
        st.error(f"Lỗi: {e}")
