import streamlit as st
from modules import auth, question_manager, survey_handler, report
import time

st.set_page_config(page_title="Hệ thống Khảo sát & Đánh giá", layout="wide")

# Kiểm tra xem đã đăng nhập chưa
if 'user_email' not in st.session_state:
    # Chưa đăng nhập, hiển thị trang đăng nhập
    user_info = auth.login_page()
    
    if user_info:
        # Lưu thông tin người dùng vào session state
        st.session_state.user_email = user_info["email"]
        st.session_state.user_role = user_info["role"]
        st.session_state.force_pw_change = user_info["first_login"]
        st.session_state.full_name = user_info.get("full_name", "")
        st.session_state.class_name = user_info.get("class", "")
        
        # Rerun để refresh giao diện
        st.rerun()

# Đã đăng nhập, kiểm tra xem có cần đổi mật khẩu không
elif st.session_state.get('force_pw_change', False):
    # Hiển thị form đổi mật khẩu
    if auth.change_password(st.session_state.user_email):
        # Nếu đã đổi mật khẩu thành công, hiển thị thông báo và rerun
        st.session_state.force_pw_change = False
        with st.spinner("Đăng nhập thành công! Đang chuyển tới giao diện chính..."):
            time.sleep(1.5)
        st.rerun()

# Đã đăng nhập và không cần đổi mật khẩu, hiển thị giao diện chính
else:
    # Hiển thị sidebar
    if st.session_state.user_role == "Admin":
        sidebar_title = "Bảng điều khiển Admin"
    else:
        sidebar_title = "Bảng điều khiển Học viên"
        
    with st.sidebar:
        st.title(sidebar_title)
        st.success(f"Xin chào, {st.session_state.full_name or st.session_state.user_email}!")
        st.write(f"**Vai trò:** {st.session_state.user_role}")
        
        if st.session_state.user_role == "Học viên":
            st.write(f"**Lớp:** {st.session_state.class_name}")
        
        # Nút đăng xuất
        if st.button("Đăng xuất", use_container_width=True):
            # Xóa thông tin người dùng khỏi session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Hiển thị giao diện tương ứng với vai trò
    if st.session_state.user_role == "Admin":
        menu = st.sidebar.selectbox("Chức năng", ["Quản lý câu hỏi", "Thống kê kết quả"])
        if menu == "Quản lý câu hỏi":
            question_manager.manage_questions()
        elif menu == "Thống kê kết quả":
            report.view_statistics()
    elif st.session_state.user_role == "Học viên":
        survey_handler.survey_form(
            st.session_state.user_email,
            st.session_state.full_name,
            st.session_state.class_name
        )