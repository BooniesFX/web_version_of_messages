import fuc
from werkzeug.security import generate_password_hash
import sqlite3

def migrate_passwords():
    print("开始密码批量迁移...")
    conn = fuc.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取所有用户信息
        cursor.execute("SELECT s_name, password FROM users")
        users = cursor.fetchall()
        
        total = len(users)
        migrated = 0
        skipped = 0
        
        for user in users:
            username = user['s_name']
            password = user['password']
            
            # 检查是否已经是哈希
            if password.startswith('pbkdf2:sha256:') or password.startswith('scrypt:'):
                skipped += 1
                continue
            
            # 生成哈希并更新
            hashed_password = generate_password_hash(password)
            cursor.execute("UPDATE users SET password = ? WHERE s_name = ?", (hashed_password, username))
            migrated += 1
            print(f"用户 [{username}] 密码已哈希化。")
        
        conn.commit()
        print(f"\n迁移结束。")
        print(f"总用户数: {total}")
        print(f"已转换: {migrated}")
        print(f"已跳过 (已哈希): {skipped}")
        
    except Exception as e:
        print(f"迁移过程中发生错误: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_passwords()
