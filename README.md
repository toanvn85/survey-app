# Hệ thống Khảo sát & Đánh giá

Ứng dụng Streamlit để quản lý, thực hiện và đánh giá các bài khảo sát.

## Tính năng

- Đăng nhập và phân quyền (Admin/Học viên)
- Đăng ký tài khoản học viên
- Quản lý câu hỏi (Admin)
- Làm bài khảo sát (Học viên)
- Xem thống kê kết quả (Admin)

## Cài đặt

### Yêu cầu

- Python 3.7+
- Streamlit
- Supabase account

### Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### Thiết lập biến môi trường

Tạo file `.env` với nội dung:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

## Chạy ứng dụng

```bash
streamlit run app.py
```

## Migrate dữ liệu từ SQLite (nếu có)

Để chuyển dữ liệu từ SQLite sang Supabase:

```bash
python migrate_to_supabase.py
```

## Demo

Ứng dụng demo: [https://survey-app.streamlit.app](https://survey-app.streamlit.app)

## Tài khoản mặc định

- Admin: admin@example.com / password123