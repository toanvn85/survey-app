import streamlit as st
from database_helper import get_all_questions, save_submission, get_user_submissions
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
    
    # Lấy lịch sử bài làm của học viên này
    user_submissions = get_user_submissions(email)
    
    # Đếm số lần đã làm bài
    submission_count = len(user_submissions)
    
    # Kiểm tra giới hạn làm bài (tối đa 3 lần)
    MAX_ATTEMPTS = 3
    remaining_attempts = MAX_ATTEMPTS - submission_count
    
    # Hiển thị số lần làm bài và giới hạn
    if submission_count > 0:
        st.write(f"**Số lần đã làm bài:** {submission_count}/{MAX_ATTEMPTS}")
        
        # Hiển thị điểm cao nhất đã đạt được
        max_score = max([s["score"] for s in user_submissions])
        max_possible = sum([q["score"] for q in questions])
        
        st.write(f"**Điểm cao nhất đã đạt được:** {max_score}/{max_possible} ({(max_score/max_possible*100):.1f}%)")
    else:
        st.write(f"**Đây là lần làm bài đầu tiên của bạn**")
    
    # Hiển thị số lượng câu hỏi và điểm tối đa
    total_questions = len(questions)
    max_score = sum([q["score"] for q in questions])
    st.write(f"**Tổng số câu hỏi:** {total_questions}")
    st.write(f"**Điểm tối đa:** {max_score}")
    
    # Kiểm tra nếu đã đạt đến giới hạn làm bài
    if remaining_attempts <= 0:
        st.error("⚠️ Bạn đã sử dụng hết số lần làm bài cho phép (tối đa 3 lần).")
        
        # Hiển thị các lần làm bài trước đó
        if st.checkbox("Xem lịch sử các lần làm bài"):
            st.subheader("Lịch sử làm bài")
            
            for idx, s in enumerate(user_submissions):
                submission_time = datetime.fromtimestamp(s["timestamp"]).strftime("%H:%M:%S %d/%m/%Y")
                with st.expander(f"Lần {idx + 1}: Ngày {submission_time} - Điểm: {s['score']}/{max_score}"):
                    # Hiển thị chi tiết câu trả lời
                    for q in questions:
                        q_id = str(q["id"])
                        st.write(f"**Câu {q['id']}: {q['question']}**")
                        
                        # Đáp án người dùng
                        user_ans = s["responses"].get(q_id, [])
                        expected = [q["answers"][i - 1] for i in q["correct"]]
                        
                        # Kiểm tra đúng/sai
                        is_correct = set(user_ans) == set(expected)
                        
                        # Hiển thị đáp án của người dùng
                        st.write("Đáp án đã chọn:")
                        if not user_ans:
                            st.write("- Không trả lời")
                        else:
                            for ans in user_ans:
                                st.write(f"- {ans}")
                        
                        # Hiển thị kết quả
                        if is_correct:
                            st.success(f"✅ Đúng (+{q['score']} điểm)")
                        else:
                            st.error("❌ Sai (0 điểm)")
                            st.write("Đáp án đúng:")
                            for ans in expected:
                                st.write(f"- {ans}")
        
        return
    
    # Thông báo số lần còn lại
    if 0 < remaining_attempts < MAX_ATTEMPTS:
        st.warning(f"⚠️ Bạn còn {remaining_attempts} lần làm bài.")
    
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
                # Kiểm tra lại số lần làm bài (để đảm bảo không vượt quá giới hạn)
                latest_submissions = get_user_submissions(email)
                if len(latest_submissions) >= MAX_ATTEMPTS:
                    st.error("Bạn đã sử dụng hết số lần làm bài cho phép!")
                    st.session_state.submission_result = None
                else:
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
                <p><b>Số lần làm bài còn lại:</b> {MAX_ATTEMPTS - submission_count - 1}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Cập nhật lại số lần làm bài sau khi nộp thành công
        updated_submissions = get_user_submissions(email)
        updated_count = len(updated_submissions)
        remaining = MAX_ATTEMPTS - updated_count
        
        # Nút làm bài lại (nếu còn lượt)
        if remaining > 0:
            if st.button("🔄 Làm bài lại", use_container_width=True):
                st.session_state.submission_result = None
                st.rerun()
        else:
            st.warning("⚠️ Bạn đã sử dụng hết số lần làm bài cho phép.")