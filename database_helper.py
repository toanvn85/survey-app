import os
import json
import time
import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Tải biến môi trường từ file .env (chỉ cho môi trường phát triển)
try:
    load_dotenv()
except:
    pass

# Ưu tiên lấy từ Streamlit secrets, nếu không có thì lấy từ biến môi trường
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    print(f"Loaded Supabase credentials from Streamlit secrets")
except Exception as e:
    # Fallback to environment variables
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    print(f"Loaded Supabase credentials from environment variables: {e}")

# Kiểm tra xem đã có thông tin kết nối chưa
if not supabase_url or not supabase_key:
    print("WARNING: Missing Supabase credentials. Make sure to set SUPABASE_URL and SUPABASE_KEY.")

# Kết nối đến Supabase
try:
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Successfully connected to Supabase")
    
    # Kiểm tra xem đã có bảng users chưa
    resp = supabase.table('users').select('count', count='exact').execute()
    total_users = resp.count if hasattr(resp, 'count') else 0
    print(f"Found {total_users} users in database")
    
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    # Để tránh crash ứng dụng khi chưa cấu hình, tạo mock object cho testing
    class MockSupabase:
        def table(self, name):
            return self
        def select(self, *args, **kwargs):
            return self
        def insert(self, data):
            return self
        def update(self, data):
            return self
        def eq(self, *args):
            return self
        def order(self, *args, **kwargs):
            return self
        def execute(self):
            return type('obj', (object,), {'data': [], 'count': 0})
        
    supabase = MockSupabase()

def ensure_tables_exist():
    """Đảm bảo các bảng cần thiết đã tồn tại"""
    try:
        # Tạo bảng users nếu chưa tồn tại
        supabase.table('users').select('count', count='exact').limit(1).execute()
        print("Users table exists")
    except Exception as e:
        print(f"Error checking users table: {e}")
        # Tạo bảng users
        try:
            # PostgreSQL không hỗ trợ tạo bảng qua API, nên chỉ ghi log
            print("Users table might not exist - please create it via SQL Editor")
        except:
            pass

def add_default_user_if_not_exists():
    """Thêm tài khoản admin mặc định nếu chưa có"""
    try:
        # Kiểm tra xem có admin nào không
        response = supabase.table('users').select('*').eq('role', 'Admin').execute()
        print(f"Found {len(response.data)} admin users")
        
        if len(response.data) == 0:
            print("No admin found, creating default admin user")
            # Thêm admin mặc định
            result = supabase.table('users').insert({
                'email': 'admin@example.com',
                'password': 'password123',
                'role': 'Admin',
                'first_login': True,
                'full_name': 'Quản trị viên'
            }).execute()
            print(f"Default admin created: {result.data}")
        else:
            print(f"Admin already exists: {response.data[0]['email']}")
    except Exception as e:
        print(f"Error adding default user: {e}")
        # Thử lại một lần nữa với cách khác
        try:
            print("Trying alternative method to create admin...")
            supabase.table('users').upsert({
                'email': 'admin@example.com',
                'password': 'password123',
                'role': 'Admin',
                'first_login': True,
                'full_name': 'Quản trị viên'
            }).execute()
            print("Admin created using upsert")
        except Exception as e2:
            print(f"Failed to create admin with upsert: {e2}")

def register_user(email, password, full_name, class_name):
    """Đăng ký người dùng mới với vai trò 'Học viên'"""
    try:
        # Kiểm tra xem email đã tồn tại chưa
        response = supabase.table('users').select('*').eq('email', email).execute()
        if len(response.data) > 0:
            return False, "Email này đã được đăng ký"
        
        # Thêm người dùng mới
        supabase.table('users').insert({
            'email': email,
            'password': password,
            'role': 'Học viên',
            'first_login': True,
            'full_name': full_name,
            'class': class_name,
            'registration_date': datetime.now().isoformat()
        }).execute()
        
        return True, "Đăng ký thành công"
    except Exception as e:
        print(f"Error registering user: {e}")
        return False, f"Lỗi khi đăng ký: {str(e)}"

def get_user(email, password):
    """Kiểm tra đăng nhập và trả về thông tin người dùng"""
    try:
        print(f"Attempting login for: {email}")
        response = supabase.table('users').select('*').eq('email', email).eq('password', password).execute()
        print(f"Login response contains {len(response.data)} users")
        
        if response.data:
            user = response.data[0]
            print(f"User found: {user['email']} with role {user['role']}")
            return {
                "email": user["email"],
                "role": user["role"],
                "first_login": user.get("first_login", False),
                "full_name": user.get("full_name", ""),
                "class": user.get("class", "")
            }
        else:
            # Kiểm tra xem user có tồn tại không (để biết lỗi ở email hay password)
            user_exists = supabase.table('users').select('*').eq('email', email).execute()
            if user_exists.data:
                print(f"User exists but password is incorrect")
            else:
                print(f"No user found with email: {email}")
            return None
    except Exception as e:
        print(f"Error during login: {e}")
    return None

def update_password(email, new_password):
    """Cập nhật mật khẩu và đánh dấu đã đổi mật khẩu"""
    try:
        print(f"Updating password for {email}")
        supabase.table('users').update({
            'password': new_password,
            'first_login': False
        }).eq('email', email).execute()
        print("Password updated successfully")
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        return False

def get_all_users(role=None):
    """Lấy danh sách tất cả người dùng, có thể lọc theo vai trò"""
    try:
        if role:
            response = supabase.table('users').select('*').eq('role', role).execute()
        else:
            response = supabase.table('users').select('*').execute()
        
        users = []
        for user in response.data:
            users.append({
                "email": user["email"],
                "role": user["role"],
                "full_name": user.get("full_name", ""),
                "class": user.get("class", ""),
                "registration_date": user.get("registration_date")
            })
        return users
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

def save_question(question_data):
    """Lưu câu hỏi vào database"""
    try:
        supabase.table('questions').insert({
            'question': question_data["question"],
            'type': question_data["type"],
            'answers': json.dumps(question_data["answers"]),
            'correct': json.dumps(question_data["correct"]),
            'score': question_data["score"]
        }).execute()
        return True
    except Exception as e:
        print(f"Error saving question: {e}")
        return False

def get_all_questions():
    """Lấy tất cả câu hỏi từ database"""
    try:
        response = supabase.table('questions').select('*').execute()
        
        questions = []
        for item in response.data:
            questions.append({
                "id": item["id"],
                "question": item["question"],
                "type": item["type"],
                "answers": json.loads(item["answers"]) if isinstance(item["answers"], str) else item["answers"],
                "correct": json.loads(item["correct"]) if isinstance(item["correct"], str) else item["correct"],
                "score": item["score"]
            })
        return questions
    except Exception as e:
        print(f"Error getting questions: {e}")
        return []

def save_submission(user_email, responses):
    """Lưu một lần nộp bài của người dùng"""
    try:
        # Tính điểm
        questions = get_all_questions()
        total_score = 0
        
        for q in questions:
            q_id = q["id"]
            if str(q_id) in responses:
                user_ans = responses[str(q_id)]
                expected = [q["answers"][i - 1] for i in q["correct"]]
                
                if set(user_ans) == set(expected):
                    total_score += q["score"]
        
        # Lưu kết quả
        result = supabase.table('submissions').insert({
            'user_email': user_email,
            'responses': json.dumps(responses),
            'score': total_score,
            'timestamp': datetime.now().isoformat()
        }).execute()
        
        submission_id = result.data[0]["id"]
        submission_time = result.data[0]["timestamp"]
        
        return {
            "id": submission_id,
            "timestamp": int(datetime.fromisoformat(submission_time).timestamp()),
            "score": total_score
        }
    except Exception as e:
        print(f"Error saving submission: {e}")
        return None

def get_user_submissions(user_email=None):
    """Lấy tất cả các lần nộp bài, có thể lọc theo email"""
    try:
        if user_email:
            response = supabase.table('submissions').select('*').eq('user_email', user_email).order('timestamp', desc=True).execute()
        else:
            response = supabase.table('submissions').select('*').order('timestamp', desc=True).execute()
        
        submissions = []
        for item in response.data:
            submissions.append({
                "id": item["id"],
                "user_email": item["user_email"],
                "timestamp": int(datetime.fromisoformat(item["timestamp"]).timestamp()),
                "responses": json.loads(item["responses"]) if isinstance(item["responses"], str) else item["responses"],
                "score": item["score"]
            })
        return submissions
    except Exception as e:
        print(f"Error getting submissions: {e}")
        return []

# Khởi tạo database và thêm người dùng mặc định
try:
    print("Initializing database...")
    ensure_tables_exist()
    add_default_user_if_not_exists()
    print("Database initialization completed")
except Exception as e:
    print(f"Error in initialization: {e}")