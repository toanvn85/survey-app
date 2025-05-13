import streamlit as st
from database_helper import get_all_questions, save_submission
import time
from datetime import datetime

def survey_form(email, full_name, class_name):
    st.title("Làm bài khảo sát")
    
    # Hiển thị thông tin người dùng
    st.write(f"**Người làm bài:** {full_name}")
    st.write(f"**Lớp:** {class_name}")
    st.write(f"**Email:** {email}")
    
    # Lấy danh sách câu hỏi từ database
    questions = get_all_questions()
    
    if not questions:
        st.info("Chưa có câu hỏi nào trong hệ thống.")
        return
    
    # Hiển thị số lượng câu hỏi và điểm tối đa
    total_questions = len(questions)
    max_score = sum([q["score"] for q in questions])
    st.write(f"**Tổng số câu hỏi:** {total_questions}")
    st.write(f"**Điểm tối đa:** {max_score}")
    
    # Khởi tạo biến theo dõi trạng thái nộp bài
    if "submission_result" not in st.session_state:
        st.session_state.submission_result = None
    
    # Nếu chưa nộp bài hoặc muốn làm lại
    if st.session_state.submission_result is None:
        # Tạo form để lưu trữ câu trả lời
        with st.form(key="survey_form"):
            st.subheader("Câu hỏi")
            
            # Lưu trữ câu trả lời tạm thời
            responses = {}
            
            for q in questions:
                q_id = q["id"]
                st.markdown(f"**Câu {q_id}: {q['question']}** *(Điểm: {q['score']})*")
                
                if q["type"] == "Checkbox":
                    responses[str(q_id)] = st.multiselect(
                        "Chọn đáp án", 
                        options=q["answers"], 
                        key=f"q_{q_id}"
                    )
                elif q["type"] == "Combobox":
                    selected = st.selectbox(
                        "Chọn 1 đáp án", 
                        options=[""] + q["answers"], 
                        key=f"q_{q_id}"
                    )
                    responses[str(q_id)] = [selected] if selected else []
                
                st.divider()
            
            # Nút gửi đáp án (trong form)
            submit_button = st.form_submit_button(label="📨 Gửi đáp án", use_container_width=True)
            
            if submit_button:
                # Lưu câu trả lời vào database với ID duy nhất
                result = save_submission(email, responses)
                
                if result:
                    st.session_state.submission_result = result
                    st.session_state.max_score = max_score
                    st.rerun()  # Làm mới trang để hiển thị kết quả
                else:
                    st.error("❌ Có lỗi xảy ra khi gửi đáp án, vui lòng thử lại!")
    
    # Hiển thị kết quả sau khi nộp bài
    else:
        result = st.session_state.submission_result
        max_score = st.session_state.max_score
        
        st.success(f"✅ Đã ghi nhận bài làm của bạn! (Mã nộp: {result['id']})")
        
        # Hiển thị thông tin về lần nộp này
        submit_time = datetime.fromtimestamp(result["timestamp"]).strftime("%H:%M:%S %d/%m/%Y")
        
        # Hiển thị kết quả trong một container màu xanh
        with st.container():
            st.markdown(f"""
            <div style="padding: 20px; background-color: #e6f7f2; border-radius: 10px; margin: 10px 0;">
                <h3 style="color: #2e7d64;">Thông tin bài nộp</h3>
                <p><b>Thời gian nộp:</b> {submit_time}</p>
                <p><b>Điểm số:</b> {result['score']}/{max_score}</p>
                <p><b>Tỷ lệ đúng:</b> {(result['score']/max_score*100):.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Nút làm bài lại (ngoài form)
        if st.button("🔄 Làm bài lại", use_container_width=True):
            st.session_state.submission_result = None
            st.rerun()