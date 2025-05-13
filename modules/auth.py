import streamlit as st
import re
from datetime import datetime
from database_helper import get_user, update_password, register_user

def login_page():
    """Hiển thị trang đăng nhập và xử lý logic đăng nhập"""
    st.title("Hệ thống Khảo sát & Đánh giá")
    
    # Tạo hai tab: Đăng nhập và Đăng ký
    tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký học viên"])
    
    # Tab đăng nhập
    with tab1:
        st.subheader("Đăng nhập")
        
        with st.form(key="login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Mật khẩu", type="password", key="login_password")
            
            submit_button = st.form_submit_button(label="Đăng nhập", use_container_width=True)
            
            if submit_button:
                if not email or not password:
                    st.error("Vui lòng nhập đầy đủ thông tin đăng nhập")
                    return None
                
                user_info = get_user(email, password)
                if user_info:
                    return user_info
                else:
                    st.error("Email hoặc mật khẩu không đúng")
                    return None
    
    # Tab đăng ký học viên
    with tab2:
        st.subheader("Đăng ký tài khoản mới")
        
        with st.form(key="register_form"):
            full_name = st.text_input("Họ và tên", key="reg_name")
            email = st.text_input("Email", key="reg_email")
            class_name = st.text_input("Lớp", key="reg_class")
            password = st.text_input("Mật khẩu", type="password", key="reg_password")
            confirm_password = st.text_input("Xác nhận mật khẩu", type="password", key="reg_confirm")
            
            submit_button = st.form_submit_button(label="Đăng ký", use_container_width=True)
            
            if submit_button:
                # Kiểm tra dữ liệu nhập vào
                if not full_name or not email or not class_name or not password:
                    st.error("Vui lòng nhập đầy đủ thông tin đăng ký")
                    return None
                
                if password != confirm_password:
                    st.error("Mật khẩu xác nhận không khớp")
                    return None
                
                if len(password) < 8:
                    st.error("Mật khẩu phải có ít nhất 8 ký tự")
                    return None
                
                # Kiểm tra định dạng email
                if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    st.error("Email không hợp lệ")
                    return None
                
                # Tiến hành đăng ký
                success, message = register_user(email, password, full_name, class_name)
                if success:
                    st.success(f"{message} Vui lòng đăng nhập với tài khoản vừa tạo.")
                    # Auto switch to login tab
                    st.session_state.active_tab = "Đăng nhập"
                else:
                    st.error(message)
                
                return None
    
    return None

def change_password(email):
    """Trang đổi mật khẩu bắt buộc cho lần đăng nhập đầu tiên"""
    st.title("Đổi mật khẩu")
    st.info("Đây là lần đăng nhập đầu tiên, vui lòng đổi mật khẩu để tiếp tục")
    
    # Theo dõi quá trình thay đổi mật khẩu trực tiếp trong session_state
    if 'password_submitted' not in st.session_state:
        st.session_state.password_submitted = False
        
    with st.form(key="change_password_form"):
        new_password = st.text_input("Mật khẩu mới", type="password", key="new_pw")
        confirm_password = st.text_input("Xác nhận mật khẩu mới", type="password", key="confirm_pw")
        
        submit_button = st.form_submit_button(label="Cập nhật mật khẩu", use_container_width=True)
        
        if submit_button:
            st.session_state.password_submitted = True
            
            if not new_password:
                st.error("Mật khẩu không được để trống")
                return False
                
            if new_password != confirm_password:
                st.error("Mật khẩu xác nhận không khớp")
                return False
                
            if len(new_password) < 8:
                st.error("Mật khẩu phải có ít nhất 8 ký tự")
                return False
                
            # Cập nhật mật khẩu vào database
            if update_password(email, new_password):
                # Đánh dấu đã đổi mật khẩu thành công trong session
                st.session_state.force_pw_change = False
                st.session_state.password_changed = True
                st.success("Đổi mật khẩu thành công! Đang chuyển tới trang chính...")
                return True
            else:
                st.error("Có lỗi xảy ra, vui lòng thử lại")
                return False
    
    # Thêm một số thông tin hướng dẫn bên ngoài form
    st.markdown("""
    ### Lưu ý:
    - Mật khẩu phải có ít nhất 8 ký tự
    - Nên sử dụng kết hợp chữ hoa, chữ thường, số và ký tự đặc biệt
    """)
    
    # Nếu đã submit thành công trước đó, trả về True
    if st.session_state.get('password_changed', False):
        return True
        
    return False