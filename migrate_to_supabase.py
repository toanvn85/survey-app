import os
import json
import sqlite3
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Đường dẫn đến file SQLite
SQLITE_DB_PATH = "data/survey.db"

# Kết nối Supabase
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def migrate_data():
    """Di chuyển dữ liệu từ SQLite sang Supabase"""
    
    # Kết nối đến SQLite
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Không tìm thấy database SQLite tại {SQLITE_DB_PATH}")
        return
    
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Migrate users
    try:
        print("Migrating users...")
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        for user in users:
            print(f"  Migrating user {user['email']}...")
            
            # Kiểm tra xem user đã tồn tại trên Supabase chưa
            existing = supabase.table('users').select('*').eq('email', user['email']).execute()
            if existing.data:
                print(f"  User {user['email']} đã tồn tại, bỏ qua.")
                continue
                
            # Thêm user mới vào Supabase
            registration_date = datetime.now().isoformat()
            
            supabase.table('users').insert({
                'email': user['email'],
                'password': user['password'],
                'role': user['role'],
                'first_login': bool(user['first_login']),
                'full_name': user.get('full_name', ''),
                'class': user.get('class', ''),
                'registration_date': registration_date
            }).execute()
    except Exception as e:
        print(f"Lỗi khi migrate users: {e}")
    
    # Migrate questions
    try:
        print("Migrating questions...")
        cursor.execute("SELECT * FROM questions")
        questions = cursor.fetchall()
        
        for question in questions:
            print(f"  Migrating question ID {question['id']}...")
            
            # Kiểm tra trùng lặp bằng nội dung câu hỏi
            existing = supabase.table('questions').select('*').eq('question', question['question']).execute()
            if existing.data:
                print(f"  Question '{question['question']}' đã tồn tại, bỏ qua.")
                continue
            
            # Thêm câu hỏi mới
            supabase.table('questions').insert({
                'question': question['question'],
                'type': question['type'],
                'answers': question['answers'],
                'correct': question['correct'],
                'score': question['score']
            }).execute()
    except Exception as e:
        print(f"Lỗi khi migrate questions: {e}")
    
    # Migrate submissions
    try:
        print("Migrating submissions...")
        cursor.execute("SELECT * FROM submissions")
        submissions = cursor.fetchall()
        
        for submission in submissions:
            print(f"  Migrating submission ID {submission['id']}...")
            
            # Chuyển đổi timestamp thành ISO format
            timestamp = datetime.fromtimestamp(submission['timestamp']).isoformat()
            
            # Thêm submission mới
            supabase.table('submissions').insert({
                'user_email': submission['user_email'],
                'timestamp': timestamp,
                'responses': submission['responses'],
                'score': submission['score']
            }).execute()
    except Exception as e:
        print(f"Lỗi khi migrate submissions: {e}")
    
    print("Migration completed!")
    conn.close()

if __name__ == "__main__":
    migrate_data()