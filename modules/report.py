import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from database_helper import get_all_questions, get_user_submissions, get_all_users
import json
from datetime import datetime
import numpy as np

def view_statistics():
    st.title("📊 Báo cáo & thống kê")
    
    # Lấy dữ liệu từ database
    questions = get_all_questions()
    submissions = get_user_submissions()
    students = get_all_users(role="Học viên")
    
    if not questions:
        st.warning("Chưa có dữ liệu câu hỏi nào trong hệ thống.")
        return
    
    if not submissions:
        st.warning("Chưa có ai nộp khảo sát.")
        return
    
    # Tạo tab thống kê
    tab1, tab2, tab3, tab4 = st.tabs(["Tổng quan", "Theo học viên", "Theo câu hỏi", "Danh sách học viên"])
    
    with tab1:
        st.subheader("Tổng quan kết quả")
        
        # Thống kê cơ bản
        total_submissions = len(submissions)
        avg_score = sum([s["score"] for s in submissions]) / total_submissions if total_submissions > 0 else 0
        max_score = max([s["score"] for s in submissions]) if submissions else 0
        total_users = len(set([s["user_email"] for s in submissions]))
        max_possible = sum([q["score"] for q in questions])
        
        # Hiển thị metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("📝 Tổng số bài nộp", total_submissions)
        col1.metric("👥 Số học viên đã làm", total_users)
        
        col2.metric("📊 Điểm trung bình", f"{avg_score:.2f}/{max_possible}")
        col2.metric("🏆 Điểm cao nhất", f"{max_score}/{max_possible}")
        
        col3.metric("📋 Số câu hỏi", len(questions))
        col3.metric("👨‍🎓 Tổng số học viên", len(students))
        
        # Biểu đồ điểm số theo thời gian
        st.subheader("Điểm số theo thời gian")
        
        # Chuẩn bị dữ liệu
        time_data = []
        for s in submissions:
            time_data.append({
                "timestamp": datetime.fromtimestamp(s["timestamp"]),
                "score": s["score"],
                "user": s["user_email"]
            })
        
        if time_data:
            df_time = pd.DataFrame(time_data)
            df_time = df_time.sort_values("timestamp")
            
            # Vẽ biểu đồ
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df_time["timestamp"], df_time["score"], marker='o')
            ax.set_ylabel("Điểm số")
            ax.set_xlabel("Thời gian nộp bài")
            ax.grid(True, linestyle='--', alpha=0.7)
            st.pyplot(fig)
        
        # Hiển thị phân phối điểm
        st.subheader("Phân phối điểm số")
        if submissions:
            scores = [s["score"] for s in submissions]
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(scores, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
            ax.set_xlabel("Điểm số")
            ax.set_ylabel("Số lượng bài nộp")
            ax.grid(True, linestyle='--', alpha=0.3)
            st.pyplot(fig)
    
    with tab2:
        st.subheader("Chi tiết theo học viên")
        
        # Tạo DataFrame từ dữ liệu
        user_data = []
        for s in submissions:
            # Tìm thông tin học viên
            student_info = next((student for student in students if student["email"] == s["user_email"]), None)
            full_name = student_info["full_name"] if student_info else "Không xác định"
            class_name = student_info["class"] if student_info else "Không xác định"
            
            user_data.append({
                "email": s["user_email"],
                "full_name": full_name,
                "class": class_name,
                "submission_id": s["id"],
                "timestamp": datetime.fromtimestamp(s["timestamp"]).strftime("%H:%M:%S %d/%m/%Y"),
                "score": s["score"],
                "max_score": max_possible,
                "percent": f"{(s['score']/max_possible*100):.1f}%"
            })
        
        if user_data:
            df_users = pd.DataFrame(user_data)
            
            # Lọc theo email hoặc lớp
            col1, col2 = st.columns(2)
            with col1:
                user_filter = st.selectbox(
                    "Chọn học viên để xem chi tiết:",
                    options=["Tất cả"] + sorted(list(set([u["email"] for u in user_data]))),
                    key="user_filter_tab2"
                )
            
            with col2:
                class_filter = st.selectbox(
                    "Lọc theo lớp:",
                    options=["Tất cả"] + sorted(list(set([u["class"] for u in user_data if u["class"] != "Không xác định"]))),
                    key="class_filter_tab2"
                )
            
            # Áp dụng bộ lọc
            df_filtered = df_users
            
            if user_filter != "Tất cả":
                df_filtered = df_filtered[df_filtered["email"] == user_filter]
            
            if class_filter != "Tất cả":
                df_filtered = df_filtered[df_filtered["class"] == class_filter]
            
            # Hiển thị bảng
            st.dataframe(
                df_filtered.sort_values(by="timestamp", ascending=False),
                use_container_width=True,
                hide_index=True,
                column_order=["full_name", "class", "email", "score", "percent", "timestamp"]
            )
            
            # Xem chi tiết một bài nộp cụ thể
            if user_filter != "Tất cả":
                submission_ids = df_filtered["submission_id"].tolist()
                if submission_ids:
                    selected_submission = st.selectbox(
                        "Chọn bài nộp để xem chi tiết:",
                        options=submission_ids,
                        key="submission_id_select"
                    )
                    
                    # Tìm bài nộp được chọn
                    submission = next((s for s in submissions if s["id"] == selected_submission), None)
                    if submission:
                        st.subheader(f"Chi tiết bài nộp #{selected_submission}")
                        
                        # Hiển thị câu trả lời chi tiết
                        for q in questions:
                            q_id = str(q["id"])
                            st.write(f"**Câu {q['id']}: {q['question']}**")
                            
                            # Đáp án người dùng
                            user_ans = submission["responses"].get(q_id, [])
                            expected = [q["answers"][i - 1] for i in q["correct"]]
                            
                            # Kiểm tra đúng/sai
                            is_correct = set(user_ans) == set(expected)
                            
                            # Hiển thị đáp án của người dùng
                            st.write("Đáp án của học viên:")
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
                            
                            st.divider()
    
    with tab3:
        st.subheader("Phân tích theo câu hỏi")
        
        # Thống kê tỷ lệ đúng/sai cho từng câu hỏi
        question_stats = {}
        
        for q in questions:
            q_id = str(q["id"])
            correct_count = 0
            wrong_count = 0
            skip_count = 0
            
            for s in submissions:
                user_ans = s["responses"].get(q_id, [])
                expected = [q["answers"][i - 1] for i in q["correct"]]
                
                if not user_ans:
                    skip_count += 1
                elif set(user_ans) == set(expected):
                    correct_count += 1
                else:
                    wrong_count += 1
            
            question_stats[q_id] = {
                "question": q["question"],
                "correct": correct_count,
                "wrong": wrong_count,
                "skip": skip_count,
                "total": correct_count + wrong_count + skip_count,
                "correct_rate": correct_count / (correct_count + wrong_count + skip_count) if (correct_count + wrong_count + skip_count) > 0 else 0
            }
        
        # Vẽ biểu đồ tỷ lệ đúng theo từng câu hỏi
        q_ids = list(question_stats.keys())
        correct_rates = [question_stats[q_id]["correct_rate"] * 100 for q_id in q_ids]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(q_ids, correct_rates, color='skyblue')
        
        # Thêm nhãn giá trị
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom')
        
        ax.set_ylim(0, 105)  # Giới hạn trục y từ 0-100%
        ax.set_xlabel("Câu hỏi")
        ax.set_ylabel("Tỷ lệ đúng (%)")
        ax.set_title("Tỷ lệ trả lời đúng theo từng câu hỏi")
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        st.pyplot(fig)
        
        # Chi tiết từng câu hỏi
        selected_question = st.selectbox(
            "Chọn câu hỏi để xem chi tiết:",
            options=[(f"Câu {q_id}: {question_stats[q_id]['question']}") for q_id in q_ids],
            key="question_select_tab3"
        )
        
        if selected_question:
            q_id = selected_question.split(":")[0].replace("Câu ", "").strip()
            q_data = question_stats[q_id]
            q_detail = next((q for q in questions if str(q["id"]) == q_id), None)
            
            if q_detail:
                st.write(f"**{selected_question}**")
                
                # Hiển thị thống kê
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("✅ Đúng", q_data["correct"])
                col2.metric("❌ Sai", q_data["wrong"])
                col3.metric("⏭️ Bỏ qua", q_data["skip"])
                col4.metric("📊 Tỷ lệ đúng", f"{q_data['correct_rate']*100:.1f}%")
                
                # Biểu đồ tròn thể hiện tỷ lệ
                labels = ['Đúng', 'Sai', 'Bỏ qua']
                sizes = [q_data["correct"], q_data["wrong"], q_data["skip"]]
                colors = ['#4CAF50', '#F44336', '#9E9E9E']
                
                fig, ax = plt.subplots()
                ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                st.pyplot(fig)
                
                # Hiển thị đáp án đúng
                st.write("**Đáp án đúng:**")
                for i in q_detail["correct"]:
                    st.write(f"- {q_detail['answers'][i-1]}")
    
    with tab4:
        st.subheader("Danh sách học viên")
        
        if not students:
            st.info("Chưa có học viên nào đăng ký")
        else:
            # Chuẩn bị dữ liệu
            student_data = []
            for student in students:
                # Tìm tất cả bài nộp của học viên
                student_submissions = [s for s in submissions if s["user_email"] == student["email"]]
                submission_count = len(student_submissions)
                
                # Tìm điểm cao nhất
                max_student_score = max([s["score"] for s in student_submissions]) if student_submissions else 0
                
                # Thời gian đăng ký
                registration_date = datetime.fromtimestamp(student["registration_date"]).strftime("%d/%m/%Y") if student.get("registration_date") else "N/A"
                
                student_data.append({
                    "full_name": student["full_name"],
                    "email": student["email"],
                    "class": student["class"],
                    "registration_date": registration_date,
                    "submission_count": submission_count,
                    "max_score": max_student_score,
                    "max_possible": max_possible,
                    "percent": f"{(max_student_score/max_possible*100):.1f}%" if max_possible > 0 else "N/A"
                })
            
            # Lọc theo lớp
            class_filter = st.selectbox(
                "Lọc theo lớp:",
                options=["Tất cả"] + sorted(list(set([s["class"] for s in student_data if s["class"]]))),
                key="class_filter_tab4"
            )
            
            df_students = pd.DataFrame(student_data)
            
            if class_filter != "Tất cả":
                df_students = df_students[df_students["class"] == class_filter]
            
            # Sắp xếp theo tên
            df_students = df_students.sort_values(by="full_name")
            
            # Hiển thị bảng
            st.dataframe(
                df_students,
                use_container_width=True,
                hide_index=True,
                column_order=["full_name", "class", "email", "submission_count", "max_score", "percent", "registration_date"]
            )
            
            # Thống kê theo lớp
            st.subheader("Thống kê theo lớp")
            
            # Nhóm theo lớp
            class_stats = df_students.groupby("class").agg({
                "email": "count",
                "submission_count": "sum",
                "max_score": "mean"
            }).reset_index()
            
            class_stats.columns = ["Lớp", "Số học viên", "Tổng số bài nộp", "Điểm trung bình"]
            class_stats["Điểm trung bình"] = class_stats["Điểm trung bình"].round(2)
            
            st.dataframe(
                class_stats,
                use_container_width=True,
                hide_index=True
            )
            
            # Biểu đồ số học viên theo lớp
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(class_stats["Lớp"], class_stats["Số học viên"], color='skyblue')
            ax.set_xlabel("Lớp")
            ax.set_ylabel("Số học viên")
            ax.set_title("Số học viên theo lớp")
            st.pyplot(fig)