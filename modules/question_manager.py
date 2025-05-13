import streamlit as st
from database_helper import save_question, get_all_questions

def manage_questions():
    st.title("Quản lý câu hỏi")
    
    # Khi bấm Tab này, tải câu hỏi từ database
    if "db_questions" not in st.session_state:
        st.session_state.db_questions = get_all_questions()
    
    # Khởi tạo biến câu hỏi mới trong session state
    if "new_question" not in st.session_state:
        st.session_state.new_question = {
            "question": "",
            "type": "Checkbox",
            "answers": [],
            "correct": [],
            "score": 1
        }

    # Hai tab: Thêm câu hỏi mới và Xem câu hỏi đã có
    tab1, tab2 = st.tabs(["Thêm câu hỏi mới", "Danh sách câu hỏi"])
    
    with tab1:
        q = st.session_state.new_question
        q["question"] = st.text_input("Nội dung câu hỏi", value=q["question"])
        q["type"] = st.selectbox("Loại câu hỏi", ["Checkbox", "Combobox"], index=["Checkbox", "Combobox"].index(q["type"]))
        q["score"] = st.number_input("Số điểm", min_value=1, value=q["score"])

        # Quản lý danh sách đáp án
        st.subheader("Danh sách đáp án")
        new_ans = st.text_input("Thêm đáp án mới")
        if st.button("➕ Thêm đáp án", key="add_answer_btn"):
            if new_ans:
                q["answers"].append(new_ans)
                
        # Hiển thị các đáp án hiện có
        for idx, ans in enumerate(q["answers"]):
            col1, col2 = st.columns([5, 1])
            col1.write(f"{idx + 1}. {ans}")
            if col2.button("🗑️", key=f"del_ans_{idx}"):
                q["answers"].pop(idx)
                st.rerun()

        # Đáp án đúng
        correct_ans = st.text_input("Đáp án đúng (STT, phân cách bằng dấu phẩy)", 
                                  value=",".join(map(str, q["correct"])))
        if correct_ans:
            try:
                q["correct"] = list(map(int, correct_ans.split(",")))
            except:
                st.warning("Đáp án phải là số, phân cách bằng dấu phẩy")

        # Lưu câu hỏi vào database
        if st.button("🧠 Lưu câu hỏi", key="save_question_btn"):
            if not q["question"]:
                st.error("Vui lòng nhập nội dung câu hỏi")
            elif not q["answers"]:
                st.error("Vui lòng thêm ít nhất một đáp án")
            elif not q["correct"]:
                st.error("Vui lòng chỉ định ít nhất một đáp án đúng")
            else:
                # Lưu vào database
                if save_question(q):
                    # Làm mới danh sách câu hỏi
                    st.session_state.db_questions = get_all_questions()
                    # Làm mới form
                    st.session_state.new_question = {
                        "question": "",
                        "type": "Checkbox",
                        "answers": [],
                        "correct": [],
                        "score": 1
                    }
                    st.success("✅ Đã lưu câu hỏi vào hệ thống!")
                    st.rerun()
    
    with tab2:
        # Hiển thị danh sách câu hỏi từ database
        questions = st.session_state.db_questions
        
        if not questions:
            st.info("Chưa có câu hỏi nào trong hệ thống")
        else:
            st.subheader(f"Đã có {len(questions)} câu hỏi")
            
            for i, q in enumerate(questions):
                with st.expander(f"Câu {i + 1}: {q['question']}"):
                    st.write(f"**ID:** {q['id']}")
                    st.write(f"**Loại câu hỏi:** {q['type']}")
                    st.write(f"**Điểm:** {q['score']}")
                    
                    st.write("**Các đáp án:**")
                    for j, ans in enumerate(q["answers"]):
                        is_correct = (j + 1) in q["correct"]
                        st.write(f"- {j + 1}. {ans} {' ✅' if is_correct else ''}")
                        
            if st.button("🔄 Làm mới danh sách"):
                st.session_state.db_questions = get_all_questions()
                st.rerun()