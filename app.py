from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
import sys
import os

# 将上级目录添加到Python路径中，以便导入fuc模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fuc
import datetime
import base64
import dotenv
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename

dotenv.load_dotenv()  # 默认加载当前目录下的 .env 文件

app = Flask(__name__)
# 使用强随机密钥（实际应用中应从环境变量读取）
app.secret_key = os.getenv('SECRET_KEY', 'default-unsecure-key-fix-me-in-production-1234567890') 
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 200)) * 1024 * 1024  # 限制上传文件大小为200MB

# Initialize CSRF
csrf = CSRFProtect(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# 静态文件路由
@app.route('/static/<path:filename>')
def static_files(filename):
    static_dir = os.path.join(app.root_path, 'static')
    return send_from_directory(static_dir, filename)

# 首页路由
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('main'))
    return redirect(url_for('login'))

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = fuc.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT s_name,s_phone_num,s_sex,place,password FROM users WHERE s_name = ?", (username,))
            resultset = cursor.fetchall()
            if len(resultset) == 0:
                flash('用户不存在', 'error')
            else:
                db_password = resultset[0][4]
                # 检查密码（支持哈希和明文迁移）
                is_valid = False
                if db_password.startswith('pbkdf2:sha256:') or db_password.startswith('scrypt:'):
                    is_valid = check_password_hash(db_password, password)
                else:
                    # 兼容存量明文密码
                    if password == db_password:
                        is_valid = True
                        # 自动升级为哈希密码
                        try:
                            new_hash = generate_password_hash(password)
                            cursor.execute("UPDATE users SET password = ? WHERE s_name = ?", (new_hash, username))
                            conn.commit()
                        except Exception as e:
                            print(f"升级密码哈希失败: {str(e)}")

                if is_valid:
                    session['username'] = username
                    session['user_info'] = {
                        'name': resultset[0][0],
                        'phone': resultset[0][1],
                        'sex': resultset[0][2],
                        'place': resultset[0][3]
                    }
                    conn.close()
                    # 更新用户在线状态
                    fuc.update_user_status(username, True)
                    return redirect(url_for('main'))
                else:
                    flash('密码不正确！', 'error')
            conn.close()
        except Exception as e:
            flash(f'登录时发生错误: {str(e)}', 'error')
    
    return render_template('login.html')

# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        phone = request.form['phone']
        place = request.form['place']
        sex = request.form['sex']
        
        if not name or not password or not phone or not place or not sex:
            flash('请填写所有字段', 'error')
            return render_template('register.html')
            
        if password != password_confirm:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')
            
        try:
            conn = fuc.get_db_connection()
            cursor = conn.cursor()
            # 使用 generate_password_hash 对密码进行加密
            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO users(s_name,s_phone_num,s_sex,place,password) VALUES (?,?,?,?,?)", 
                          (name, phone, sex, place, hashed_password))
            conn.commit()
            conn.close()
            flash('注册成功！', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'注册时发生错误: {str(e)}', 'error')
    
    return render_template('register.html')

# 主页面
@app.route('/main')
def main():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_info = session['user_info']
    return render_template('main.html', user_info=user_info)

# 发送漂流瓶
@app.route('/send_bottle', methods=['POST'])
def send_bottle():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    msg = request.form['message']
    is_persistent = request.form.get('is_persistent', '0')
    
    if not msg:
        return jsonify({'success': False, 'message': '请输入消息内容'})
        
    if len(msg) > 100:
        return jsonify({'success': False, 'message': '消息不能超过100字'})
    
    try:
        d = datetime.datetime.today()
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mm(name,msg,time,is_persistent) VALUES (?,?,?,?)", 
                      (session['username'], msg, d.strftime("%Y-%m-%d %H:%M:%S"), is_persistent))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '发送成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送消息时发生错误: {str(e)}'})

# 接收漂流瓶
@app.route('/receive_bottle')
def receive_bottle():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name,msg,time,is_persistent FROM mm")
        resultset = cursor.fetchall()
        l = len(resultset)
        if l <= 0:
            conn.close()
            return jsonify({'success': True, 'message': '没有捞到任何漂流瓶，请稍后再试...', 'data': None})
        else:
            import random
            pos = random.randint(0, l-1)
            sender_name = resultset[pos][0]
            msg = resultset[pos][1]
            time = resultset[pos][2]
            is_persistent = resultset[pos][3] if len(resultset[pos]) > 3 else 0
            
            # 获取用户信息
            cursor.execute("SELECT s_name,s_phone_num,s_sex,place,password FROM users WHERE s_name = ?", (sender_name,))
            user_result = cursor.fetchall()
            
            if user_result:
                user_info = {
                    'name': user_result[0][0],
                    'phone': user_result[0][1],
                    'sex': user_result[0][2],
                    'place': user_result[0][3]
                }
            else:
                user_info = None
            
            conn.close()
            
            # 注意：与GUI版本不同，Web版本不在这里删除漂流瓶
            # 而是在用户明确选择回复时才删除（如果是非永久的）
            
            return jsonify({
                'success': True,
                'data': {
                    'message': msg,
                    'sender': sender_name,
                    'time': time,
                    'is_persistent': is_persistent,
                    'sender_info': user_info
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'接收消息时发生错误: {str(e)}'})

# 回复漂流瓶
@app.route('/reply_bottle', methods=['POST'])
def reply_bottle():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        data = request.get_json()
        sender_name = data.get('sender_name')
        bottle_time = data.get('time')
        is_persistent = data.get('is_persistent', 0)
        
        if not sender_name or not bottle_time:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 如果不是永久保存的漂流瓶，则删除它
        if is_persistent == 0:
            conn = fuc.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mm WHERE time = ? and name = ?", (bottle_time, sender_name))
            conn.commit()
            conn.close()
        
        # 返回成功，前端将打开与发送者的聊天
        return jsonify({
            'success': True, 
            'message': '删除成功，准备打开聊天窗口',
            'chat_with': sender_name
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'回复漂流瓶时发生错误: {str(e)}'})

# 搜索用户
@app.route('/search_users', methods=['POST'])
def search_users():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        search_term = request.form.get('search_term', '').strip()
        
        if not search_term:
            return jsonify({'success': False, 'message': '请输入搜索关键词'})
        
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        # 搜索用户名包含搜索词的用户（排除自己）
        cursor.execute("SELECT s_name, s_phone_num, s_sex, place FROM users WHERE s_name LIKE ? AND s_name != ?",
                       (f'%{search_term}%', session['username']))
        resultset = cursor.fetchall()
        conn.close()
        
        users = []
        for row in resultset:
            users.append({
                'name': row['s_name'],
                'phone': row['s_phone_num'],
                'sex': row['s_sex'],
                'place': row['place']
            })
        
        return jsonify({'success': True, 'data': users})
    except Exception as e:
        return jsonify({'success': False, 'message': f'搜索用户时发生错误: {str(e)}'})

# 添加好友
@app.route('/add_friend', methods=['POST'])
def add_friend():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        friend_name = request.form.get('friend_name', '').strip()
        
        if not friend_name:
            return jsonify({'success': False, 'message': '用户名不能为空'})
        
        # 检查用户是否存在
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT s_name FROM users WHERE s_name = ?", (friend_name,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'message': '用户不存在'})
        
        # 检查是否已经是好友（通过检查是否有聊天记录）
        cursor.execute('''
            SELECT COUNT(*) as count FROM (
                SELECT 1 FROM private_text_messages 
                WHERE (sender_name = ? AND receiver_name = ?) OR (sender_name = ? AND receiver_name = ?)
                UNION
                SELECT 1 FROM private_image_messages 
                WHERE (sender_name = ? AND receiver_name = ?) OR (sender_name = ? AND receiver_name = ?)
            )
        ''', (session['username'], friend_name, friend_name, session['username'], 
              session['username'], friend_name, friend_name, session['username']))
        
        result = cursor.fetchone()
        conn.close()
        
        # 如果没有聊天记录，则发送一条默认消息来建立联系
        if result['count'] == 0:
            # 发送一条默认消息来建立联系
            if not fuc.send_private_message(session['username'], friend_name, "你好！我们已经是好友了，现在可以开始聊天了。"):
                return jsonify({'success': False, 'message': '添加好友失败'})
        
        return jsonify({'success': True, 'message': '添加好友成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加好友时发生错误: {str(e)}'})

# 创建群组
@app.route('/create_group', methods=['POST'])
def create_group():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        group_name = request.form.get('group_name')
        description = request.form.get('description', '')
        
        if not group_name:
            return jsonify({'success': False, 'message': '群组名称不能为空'})
            
        avatar_path = None
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                # Save avatar
                import uuid
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"group_{uuid.uuid4().hex}.{ext}"
                file_dir = os.path.join(app.root_path, 'static', 'group_avatars')
                if not os.path.exists(file_dir):
                    os.makedirs(file_dir)
                file.save(os.path.join(file_dir, filename))
                avatar_path = f"group_avatars/{filename}"
        
        group_id = fuc.create_group(session['username'], group_name, description, avatar_path)
        
        if group_id:
            return jsonify({'success': True, 'message': '创建群组成功'})
        else:
            return jsonify({'success': False, 'message': '创建群组失败，可能是群组名称已存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建群组时发生错误: {str(e)}'})

@app.route('/join_group/<token>')
def join_group_link(token):
    if 'username' not in session:
        return redirect(url_for('index'))
    
    success, message = fuc.join_group_by_token(token, session['username'])
    if success:
        # Join socket room
        # This is tricky because socket is client-side initiated.
        # We can just redirect to main and let the client reload groups.
        pass
        
    return redirect(url_for('main'))

# 获取用户群组列表
@app.route('/user_groups')
def user_groups():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        groups = fuc.get_user_groups(session['username'])
        return jsonify({'success': True, 'data': groups})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取群组列表时发生错误: {str(e)}'})

# 获取群组成员
@app.route('/group_members/<int:group_id>')
def group_members(group_id):
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        # 检查用户是否是群组成员
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM group_members WHERE group_id = ? AND user_name = ?",
            (group_id, session['username'])
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'message': '您不是该群组的成员'})
        
        members = fuc.get_group_members(group_id)
        return jsonify({'success': True, 'data': members})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取群组成员时发生错误: {str(e)}'})

# 添加群组成员
@app.route('/add_group_member', methods=['POST'])
def add_group_member():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        group_id = request.form.get('group_id', type=int)
        user_name = request.form.get('user_name', '').strip()
        
        if not group_id or not user_name:
            return jsonify({'success': False, 'message': '群组ID和用户名不能为空'})
        
        # 检查用户是否是群组成员
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role FROM group_members WHERE group_id = ? AND user_name = ?",
            (group_id, session['username'])
        )
        result = cursor.fetchone()
        
        # 只有管理员或创建者可以添加成员
        if not result or result['role'] not in ['admin', 'creator']:
            conn.close()
            return jsonify({'success': False, 'message': '只有管理员可以添加成员'})
        
        # 检查要添加的用户是否存在
        cursor.execute("SELECT s_name FROM users WHERE s_name = ?", (user_name,))
        user_result = cursor.fetchone()
        
        if not user_result:
            conn.close()
            return jsonify({'success': False, 'message': '用户不存在'})
        
        conn.close()
        
        # 添加成员
        if fuc.add_group_member(group_id, user_name):
            return jsonify({'success': True, 'message': '添加成员成功'})
        else:
            return jsonify({'success': False, 'message': '添加成员失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加群组成员时发生错误: {str(e)}'})

# 发送群组消息
@app.route('/send_group_message', methods=['POST'])
def send_group_message():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        group_id = request.form.get('group_id', type=int)
        message = request.form.get('message', '').strip()
        
        if not group_id or not message:
            return jsonify({'success': False, 'message': '群组ID和消息内容不能为空'})
        
        # 检查用户是否是群组成员
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM group_members WHERE group_id = ? AND user_name = ?",
            (group_id, session['username'])
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'message': '您不是该群组的成员'})
        
        # 发送消息
        if fuc.send_group_message(group_id, session['username'], message):
            # Real-time notification
            socketio.emit('new_group_message', {
                'group_id': group_id,
                'sender': session['username'],
                'content': message,
                'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, room=f"group_{group_id}")
            return jsonify({'success': True, 'message': '发送消息成功'})
        else:
            return jsonify({'success': False, 'message': '发送消息失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送群组消息时发生错误: {str(e)}'})

# 获取群组消息
@app.route('/group_messages/<int:group_id>')
def group_messages(group_id):
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        # 检查用户是否是群组成员
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM group_members WHERE group_id = ? AND user_name = ?",
            (group_id, session['username'])
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'message': '您不是该群组的成员'})
        
        messages = fuc.get_group_messages(group_id)
        return jsonify({'success': True, 'data': messages})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取群组消息时发生错误: {str(e)}'})

# 获取群公告
@app.route('/get_group_announcement/<int:group_id>')
def get_group_announcement(group_id):
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM groups WHERE id = ?", (group_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({'success': True, 'announcement': result['description']})
        else:
            return jsonify({'success': False, 'message': '群组不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取群公告时发生错误: {str(e)}'})

# 获取群公告

# 获取用户在群组中的角色
@app.route('/get_user_group_role/<int:group_id>')
def get_user_group_role(group_id):
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        role = fuc.get_user_group_role(session['username'], group_id)
        return jsonify({'success': True, 'role': role})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户群组角色时发生错误: {str(e)}'})

# 提升群组成员为管理员
@app.route('/promote_group_member', methods=['POST'])
def promote_group_member():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        group_id = request.form.get('group_id', type=int)
        target_user_name = request.form.get('user_name', '').strip()
        
        if not group_id or not target_user_name:
            return jsonify({'success': False, 'message': '群组ID和用户名不能为空'})
        
        if fuc.set_group_member_role(group_id, target_user_name, 'admin', session['username']):
            return jsonify({'success': True, 'message': f'已将 {target_user_name} 提升为管理员'})
        else:
            return jsonify({'success': False, 'message': '提升管理员失败，请检查权限或用户是否存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'提升管理员时发生错误: {str(e)}'})

# 降级群组成员
@app.route('/demote_group_member', methods=['POST'])
def demote_group_member():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        group_id = request.form.get('group_id', type=int)
        target_user_name = request.form.get('user_name', '').strip()
        
        if not group_id or not target_user_name:
            return jsonify({'success': False, 'message': '群组ID和用户名不能为空'})
        
        if fuc.set_group_member_role(group_id, target_user_name, 'member', session['username']):
            return jsonify({'success': True, 'message': f'已将 {target_user_name} 降级为普通成员'})
        else:
            return jsonify({'success': False, 'message': '降级成员失败，请检查权限或用户是否存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'降级成员时发生错误: {str(e)}'})

# 踢出群组成员
@app.route('/kick_group_member', methods=['POST'])
def kick_group_member():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        group_id = request.form.get('group_id', type=int)
        target_user_name = request.form.get('user_name', '').strip()
        
        if not group_id or not target_user_name:
            return jsonify({'success': False, 'message': '群组ID和用户名不能为空'})
        
        if fuc.remove_group_member(group_id, target_user_name, session['username']):
            return jsonify({'success': True, 'message': f'已将 {target_user_name} 移出群组'})
        else:
            return jsonify({'success': False, 'message': '移出成员失败，请检查权限或用户是否存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'移出成员时发生错误: {str(e)}'})

# 更新群公告
@app.route('/update_announcement', methods=['POST'])
def update_announcement():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        group_id = request.form.get('group_id', type=int)
        announcement_text = request.form.get('announcement_text', '').strip()
        
        if not group_id:
            return jsonify({'success': False, 'message': '群组ID不能为空'})
        
        if fuc.update_group_announcement(group_id, announcement_text, session['username']):
            return jsonify({'success': True, 'message': '群公告更新成功'})
        else:
            return jsonify({'success': False, 'message': '更新群公告失败，请检查权限'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新群公告时发生错误: {str(e)}'})

# 获取聊天用户列表
@app.route('/chat_users')
def chat_users():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        chat_users = fuc.get_chat_users(session['username'])
        unread_text_users = fuc.get_unread_message_users(session['username'])
        unread_image_users = fuc.get_unread_image_message_users(session['username'])
        
        # 合并未读用户列表
        unread_users = set(unread_text_users + unread_image_users)
        
        # 构造返回数据
        users_data = []
        for user in chat_users:
            users_data.append({
                'name': user,
                'has_unread': user in unread_users
            })
        
        return jsonify({'success': True, 'data': users_data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取聊天用户时发生错误: {str(e)}'})

# 获取与特定用户的聊天记录
@app.route('/chat_messages/<chat_with_user>')
def chat_messages(chat_with_user):
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        # 获取文本消息、图片消息和文件消息
        text_messages = fuc.get_private_messages(session['username'], chat_with_user)
        image_messages = fuc.get_private_image_messages(session['username'], chat_with_user)
        file_messages = fuc.get_shared_files(session['username'], chat_with_user)
        
        # 合并消息
        all_messages = []
        
        # 添加文本消息
        for msg_id, sender, receiver, message, time, is_read, is_withdrawn in text_messages:
            all_messages.append({
                'id': msg_id,
                'type': 'text',
                'sender': sender,
                'receiver': receiver,
                'content': message,
                'time': time,
                'is_read': is_read,
                'is_withdrawn': is_withdrawn
            })
        
        # 添加图片消息
        for msg_id, sender, receiver, image_data, image_type, image_size, time, is_read, is_withdrawn in image_messages:
            try:
                # 将图片数据转换为base64编码的URL
                import base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                image_url = f"data:image/{image_type};base64,{image_base64}"
                all_messages.append({
                    'id': msg_id,
                    'type': 'image',
                    'sender': sender,
                    'receiver': receiver,
                    'content': image_url,
                    'time': time,
                    'is_read': is_read,
                    'is_withdrawn': is_withdrawn
                })
            except Exception as e:
                print(f"处理图片消息时发生错误: {str(e)}")
                # 即使单个图片消息处理失败，也不影响其他消息
                continue
        
        # 添加文件消息
        for file in file_messages:
            msg_type = 'file'
            # Check if it's a voice message
            if file['file_type'] and (file['file_type'].startswith('audio/') or file['file_name'].endswith('.webm') or file['file_name'].endswith('.wav')):
                msg_type = 'voice'
                
            all_messages.append({
                'id': file['id'],
                'type': msg_type,
                'sender': file['sender_name'],
                'receiver': file['receiver_name'],
                'content': file['file_name'],
                'file_path': file['file_path'], # Ensure file_path is passed
                'time': file['send_time'],
                'is_read': file['is_read'],
                'is_withdrawn': False,
                'file_size': file['file_size'],
                'token': file.get('token')
            })
        
        # 按时间排序
        all_messages.sort(key=lambda x: x['time'])
        
        return jsonify({'success': True, 'data': all_messages})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取聊天消息时发生错误: {str(e)}'})

# 发送私聊消息
@app.route('/send_private_message', methods=['POST'])
def send_private_message():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    receiver_name = request.form['receiver']
    message = request.form['message']
    
    if not receiver_name or not message:
        return jsonify({'success': False, 'message': '接收者和消息内容不能为空'})
    
    try:
        if fuc.send_private_message(session['username'], receiver_name, message):
            # Real-time notification
            socketio.emit('new_private_message', {
                'sender': session['username'],
                'content': message,
                'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, room=receiver_name)
            
            # 创建通知
            
            return jsonify({'success': True, 'message': '发送成功'})
        else:
            return jsonify({'success': False, 'message': '发送失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送消息时发生错误: {str(e)}'})

# 发送私聊图片消息
@app.route('/send_private_image', methods=['POST'])
def send_private_image():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    receiver_name = request.form['receiver']
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '没有上传图片'})
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'success': False, 'message': '没有选择图片'})
    
    # 验证文件后缀名
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
    file_ext = os.path.splitext(image_file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({'success': False, 'message': '不支持的文件格式，仅限 JPG, PNG, GIF'})
    
    try:
        # 保存图片到临时文件
        import tempfile
        import datetime
        from werkzeug.utils import secure_filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        temp_dir = tempfile.gettempdir()
        # Use secure_filename for safety
        safe_filename = secure_filename(image_file.filename)
        temp_filename = f"temp_image_{timestamp}_{safe_filename}"
        temp_path = os.path.join(temp_dir, temp_filename)
        image_file.save(temp_path)
        
        # 获取图片类型和大小
        image_type = image_file.mimetype
        image_size = os.path.getsize(temp_path)

        # 读取图片数据
        with open(temp_path, 'rb') as f:
            image_data = f.read()
        
        # 保存图片消息到数据库
        if fuc.send_private_image_message(session['username'], receiver_name, image_data, image_type, image_size):
            # 删除临时文件
            os.remove(temp_path)
            # 创建通知
            
            return jsonify({'success': True, 'message': '发送成功'})
        else:
            # 删除临时文件
            os.remove(temp_path)
            return jsonify({'success': False, 'message': '发送失败'})
    except Exception as e:
        # 删除可能已保存的临时文件
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'success': False, 'message': f'发送图片时发生错误: {str(e)}'})

# 发送私聊语音消息
@app.route('/send_private_voice', methods=['POST'])
def send_private_voice():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    receiver_name = request.form['receiver']
    if 'voice' not in request.files:
        return jsonify({'success': False, 'message': '没有上传语音文件'})
    
    voice_file = request.files['voice']
    if voice_file.filename == '':
        return jsonify({'success': False, 'message': '没有选择语音文件'})
    
    allowed_voice_extensions = {'.wav', '.mp3', '.m4a', '.webm'}
    file_ext = os.path.splitext(voice_file.filename)[1].lower()
    if file_ext not in allowed_voice_extensions:
        return jsonify({'success': False, 'message': '不支持的音频格式，仅限 WAV, MP3, M4A, WEBM'})

    try:
        # Create file storage directory for voice messages
        voice_dir = os.path.join(app.root_path, 'static', 'shared_files', 'voice')
        if not os.path.exists(voice_dir):
            os.makedirs(voice_dir)
        
        import datetime
        from werkzeug.utils import secure_filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        safe_filename = secure_filename(voice_file.filename)
        unique_filename = f"{session['username']}_{timestamp}_{safe_filename}"
        destination_path = os.path.join(voice_dir, unique_filename)
        
        voice_file.save(destination_path)
        
        # Save relative path to database
        relative_path = os.path.join('shared_files', 'voice', unique_filename)
        
        # Assuming fuc.send_private_file_message can handle voice files
        # You might need to adjust fuc.send_private_file_message or create a new one
        if fuc.send_private_file_message(session['username'], receiver_name, relative_path, voice_file.mimetype, os.path.getsize(destination_path)):
            # Real-time notification for new file/voice message
            socketio.emit('new_private_message', {
                'sender': session['username'],
                'type': 'voice',
                'content': unique_filename, # Or a URL to the voice file
                'file_path': relative_path,
                'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, room=receiver_name)
            return jsonify({'success': True, 'message': '语音发送成功'})
        else:
            os.remove(destination_path) # Clean up if DB save fails
            return jsonify({'success': False, 'message': '语音发送失败'})
    except Exception as e:
        if 'destination_path' in locals() and os.path.exists(destination_path):
            os.remove(destination_path)
        return jsonify({'success': False, 'message': f'发送语音时发生错误: {str(e)}'})

# 退出登录
@app.route('/logout')
def logout():
    # 更新用户在线状态为离线
    if 'username' in session:
        fuc.update_user_status(session['username'], False)
    session.pop('username', None)
    session.pop('user_info', None)
    return redirect(url_for('login'))

# AI Auto-Reply Toggle
@app.route('/toggle_ai_auto_reply', methods=['POST'])
def toggle_ai_auto_reply():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        enabled = request.json.get('enabled', False)
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_ai_auto_reply = ? WHERE s_name = ?", (1 if enabled else 0, session['username']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f"AI自动回复已{'开启' if enabled else '关闭'}"})
    except Exception as e:
        return jsonify({'success': False, 'message': f'设置失败: {str(e)}'})

# Get Auto-Reply Status
@app.route('/get_ai_auto_reply_status')
def get_ai_auto_reply_status():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_ai_auto_reply FROM users WHERE s_name = ?", (session['username'],))
        result = cursor.fetchone()
        conn.close()
        
        enabled = False
        if result and result['is_ai_auto_reply'] == 1:
            enabled = True
            
        return jsonify({'success': True, 'enabled': enabled})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取状态失败: {str(e)}'})

# Summarize Unread Messages
@app.route('/summarize_unread', methods=['POST'])
def summarize_unread():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        # Get all unread messages
        unread_users = fuc.get_unread_message_users(session['username'])
        if not unread_users:
            return jsonify({'success': True, 'summary': '没有未读消息'})
            
        summary_text = "未读消息总结:\n"
        
        for sender in unread_users:
            messages = fuc.get_private_messages(sender, session['username'])
            # Filter unread
            unread_msgs = [msg for msg in messages if msg[5] == 0 and msg[2] == session['username']]
            
            if unread_msgs:
                msgs_content = "\n".join([f"{msg[3]}" for msg in unread_msgs])
                ai_summary = fuc.call_ai_api(f"请总结以下来自 {sender} 的消息:\n{msgs_content}", system_prompt="You are a helpful assistant summarizing messages.")
                summary_text += f"- 来自 {sender}: {ai_summary}\n"
        
        return jsonify({'success': True, 'summary': summary_text})
    except Exception as e:
        return jsonify({'success': False, 'message': f'总结失败: {str(e)}'})

# Generate Reply
@app.route('/generate_reply', methods=['POST'])
def generate_reply():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        chat_with = request.json.get('chat_with')
        if not chat_with:
            return jsonify({'success': False, 'message': '未指定聊天对象'})
            
        # Get history
        history = fuc.get_private_messages(session['username'], chat_with)
        context = "History:\n"
        for msg in history[-10:]:
            context += f"{msg[1]}: {msg[3]}\n"
            
        ai_reply = fuc.call_ai_api("请根据历史记录生成一个回复", system_prompt=f"You are acting as {session['username']}. Reply to {chat_with}. {context}")
        
        return jsonify({'success': True, 'reply': ai_reply})
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成回复失败: {str(e)}'})

# Add AI Friend
@app.route('/add_ai_friend', methods=['POST'])
def add_ai_friend():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
        
    try:
        # Check if AI user exists (it should)
        fuc.ensure_ai_user()
        
        # Add AI as friend (send a message)
        fuc.send_private_message(session['username'], 'AI', '你好，AI助手！')
        fuc.send_private_message('AI', session['username'], '你好！我是你的AI助手，有什么可以帮你的吗？')
        
        return jsonify({'success': True, 'message': '已添加AI为好友'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加AI好友失败: {str(e)}'})


# 个人资料页面
@app.route('/profile')
def profile_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        profile = fuc.get_user_profile(session['username'])
        return render_template('profile.html', user_info=session['user_info'], profile=profile)
    except Exception as e:
        flash(f'获取个人资料时发生错误: {str(e)}', 'error')
        return redirect(url_for('main'))

# 关于页面
@app.route('/about')
def about():
    return render_template('about.html')

# 下载程序页面
@app.route('/download')
def download():
    return render_template('download.html')

# 下载程序文件
@app.route('/download_program')
def download_program():
    import os
    import zipfile
    from flask import send_file
    
    # 创建临时zip文件在static目录下
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    zip_filename = 'drifting_bottle_v2.0.zip'
    zip_path = os.path.join(static_dir, zip_filename)
    
    # 如果zip文件已存在且不是太旧，则直接返回
    if os.path.exists(zip_path):
        import time
        # 如果文件小于1小时，直接返回
        if time.time() - os.path.getmtime(zip_path) < 3600:
            return send_file(zip_path, as_attachment=True, download_name=zip_filename)
    
    # 创建zip文件
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # 添加主要程序文件
        main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for root, dirs, files in os.walk(main_dir):
            # 跳过 __pycache__ 和 .git 目录，以及web_version_of_messages的static目录
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
            
            for file in files:
                if not file.endswith('.pyc'):  # 跳过编译文件
                    file_path = os.path.join(root, file)
                    # 跳过web_version_of_messages/static目录下的zip文件
                    if 'web_version_of_messages' in file_path and 'static' in file_path and file.endswith('.zip'):
                        continue
                    arc_path = os.path.relpath(file_path, main_dir)
                    zipf.write(file_path, arc_path)
    
    return send_file(zip_path, as_attachment=True, download_name=zip_filename)

# 朋友圈页面
@app.route('/moments')
def moments():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('moments.html', user_info=session['user_info'])

# 发布朋友圈
@app.route('/post_moment', methods=['POST'])
def post_moment():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        content = request.form.get('content', '')[:200]  # 限制200字
        # content = "test"  # 限制200字
        print(content)
        image_path = None
        
        # 处理上传的图片（只允许一张图片）
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename != '':
                # 创建图片存储目录
                image_dir = os.path.join(app.root_path, 'static', 'moments')
                if not os.path.exists(image_dir):
                    os.makedirs(image_dir)
                
                # 生成唯一的文件名
                import uuid
                from werkzeug.utils import secure_filename
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                safe_filename = secure_filename(image.filename)
                unique_filename = f"{uuid.uuid4().hex}_{timestamp}_{safe_filename}"
                destination_path = os.path.join(image_dir, unique_filename)
                
                # 保存图片
                image.save(destination_path)
                
                # 保存相对路径
                image_path = os.path.join('moments', unique_filename)
        
        # 保存到数据库
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        d = datetime.datetime.today()
        cursor.execute(
            "INSERT INTO moments(user_name, content, image_paths, post_time) VALUES (?, ?, ?, ?)",
            (session['username'], content, image_path, d.strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '发布成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'发布失败: {str(e)}'})

# 获取朋友圈列表
@app.route('/get_moments')
def get_moments():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有朋友圈，按时间倒序排列
        cursor.execute("""
            SELECT m.id, m.user_name, m.content, m.image_paths, m.post_time, u.s_phone_num, u.s_sex, u.place
            FROM moments m
            JOIN users u ON m.user_name = u.s_name
            ORDER BY m.post_time DESC
            LIMIT 50
        """)
        
        moments_data = []
        for row in cursor.fetchall():
            # 获取评论
            cursor.execute("""
                SELECT mc.user_name, mc.comment, mc.comment_time, u.s_phone_num, u.s_sex, u.place
                FROM moment_comments mc
                JOIN users u ON mc.user_name = u.s_name
                WHERE mc.moment_id = ?
                ORDER BY mc.comment_time ASC
            """, (row[0],))
            
            comments = []
            for comment_row in cursor.fetchall():
                # Mask phone number for comments
                comment_phone = comment_row[3]
                masked_comment_phone = comment_phone[:3] + "****" + comment_phone[7:] if comment_phone and len(comment_phone) == 11 else (comment_phone if comment_phone else "未知")
                comments.append({
                    'user_name': comment_row[0],
                    'comment': comment_row[1],
                    'comment_time': comment_row[2],
                    'user_info': {
                        'phone': masked_comment_phone,
                        'sex': comment_row[4],
                        'place': comment_row[5]
                    }
                })
            
            # 获取点赞数和当前用户是否已点赞
            cursor.execute("SELECT COUNT(*) FROM moment_likes WHERE moment_id = ?", (row[0],))
            like_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM moment_likes WHERE moment_id = ? AND user_name = ?", (row[0], session['username']))
            user_liked = cursor.fetchone()[0] > 0
            
            # 处理图片路径
            image_path = row[3]  # image_paths字段现在是单个路径而不是数组
            
            # Mask phone number for moment poster
            poster_phone = row[5]
            masked_poster_phone = poster_phone[:3] + "****" + poster_phone[7:] if poster_phone and len(poster_phone) == 11 else (poster_phone if poster_phone else "未知")

            moments_data.append({
                'id': row[0],
                'user_name': row[1],
                'content': row[2],
                'image_paths': image_path,  # 使用单个路径而不是数组
                'post_time': row[4],
                'user_info': {
                    'phone': masked_poster_phone,
                    'sex': row[6],
                    'place': row[7]
                },
                'comments': comments,
                'like_count': like_count,
                'user_liked': user_liked
            })
        
        conn.close()
        return jsonify({'success': True, 'data': moments_data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取朋友圈失败: {str(e)}'})

# 点赞朋友圈
@app.route('/like_moment', methods=['POST'])
def like_moment():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        moment_id = request.form.get('moment_id')
        if not moment_id:
            return jsonify({'success': False, 'message': '参数错误'})
        
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        
        # 检查是否已经点赞
        cursor.execute("SELECT id FROM moment_likes WHERE moment_id = ? AND user_name = ?", (moment_id, session['username']))
        existing_like = cursor.fetchone()
        
        if existing_like:
            # 取消点赞
            cursor.execute("DELETE FROM moment_likes WHERE id = ?", (existing_like[0],))
            action = 'unlike'
        else:
            # 点赞
            d = datetime.datetime.today()
            cursor.execute("INSERT INTO moment_likes(moment_id, user_name, like_time) VALUES (?, ?, ?)", 
                          (moment_id, session['username'], d.strftime("%Y-%m-%d %H:%M:%S")))
            action = 'like'
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'action': action})
    except Exception as e:
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})

# 评论朋友圈
@app.route('/comment_moment', methods=['POST'])
def comment_moment():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        moment_id = request.form.get('moment_id')
        comment = request.form.get('comment', '')[:200]  # 限制200字
        
        if not moment_id or not comment:
            return jsonify({'success': False, 'message': '参数错误'})
        
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        
        # 添加评论
        d = datetime.datetime.today()
        cursor.execute("INSERT INTO moment_comments(moment_id, user_name, comment, comment_time) VALUES (?, ?, ?, ?)", 
                      (moment_id, session['username'], comment, d.strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '评论成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'评论失败: {str(e)}'})

# 用户在线状态相关路由
@app.route('/update_user_status', methods=['POST'])
def update_user_status():
    """更新用户在线状态"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        is_online = request.form.get('is_online', '1') == '1'
        
        if fuc.update_user_status(session['username'], is_online):
            return jsonify({'success': True, 'message': '状态更新成功'})
        else:
            return jsonify({'success': False, 'message': '状态更新失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新状态时发生错误: {str(e)}'})

@app.route('/get_user_status/<username>')
def get_user_status(username):
    """获取用户在线状态"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        status = fuc.get_user_status(username)
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户状态时发生错误: {str(e)}'})

@app.route('/get_online_users')
def get_online_users():
    """获取在线用户列表"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        online_users = fuc.get_online_users()
        return jsonify({'success': True, 'data': online_users})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取在线用户时发生错误: {str(e)}'})

# 个人资料相关路由
@app.route('/get_user_profile')
def get_user_profile():
    """获取用户个人资料"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        profile = fuc.get_user_profile(session['username'])
        return jsonify({'success': True, 'data': profile})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取个人资料时发生错误: {str(e)}'})

@app.route('/update_user_profile', methods=['POST'])
def update_user_profile():
    """更新用户个人资料"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        # 获取表单数据
        bio = request.form.get('bio', '')
        birth_date = request.form.get('birth_date', '')
        theme_preference = request.form.get('theme_preference', 'light')
        notification_enabled = request.form.get('notification_enabled', '1') == '1'
        
        # 处理头像上传
        avatar_path = None
        if 'avatar' in request.files:
            avatar = request.files['avatar']
            if avatar and avatar.filename != '':
                # 创建头像存储目录
                avatar_dir = os.path.join(app.root_path, 'static', 'avatars')
                if not os.path.exists(avatar_dir):
                    os.makedirs(avatar_dir)
                
                # 生成唯一的文件名
                import uuid
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                unique_filename = f"{uuid.uuid4().hex}_{timestamp}{os.path.splitext(avatar.filename)[1]}"
                destination_path = os.path.join(avatar_dir, unique_filename)
                
                # 保存头像
                avatar.save(destination_path)
                
                # 保存相对路径
                avatar_path = os.path.join('avatars', unique_filename)
        
        # 更新个人资料
        if fuc.create_or_update_user_profile(
            session['username'], 
            avatar_path=avatar_path,
            bio=bio if bio else None,
            birth_date=birth_date if birth_date else None,
            theme_preference=theme_preference,
            notification_enabled=notification_enabled
        ):
            return jsonify({'success': True, 'message': '更新成功'})
        else:
            return jsonify({'success': False, 'message': '更新失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新个人资料时发生错误: {str(e)}'})

# 文件分享相关路由
@app.route('/send_file', methods=['POST'])
def send_file():
    """发送文件"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        receiver_name = request.form.get('receiver')
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        # 创建文件存储目录
        file_dir = os.path.join(app.root_path, 'static', 'shared_files')
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        
        # 生成唯一的文件名
        import uuid
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{uuid.uuid4().hex}_{timestamp}{os.path.splitext(file.filename)[1]}"
        destination_path = os.path.join(file_dir, unique_filename)
        
        # 保存文件
        file.save(destination_path)
        
        # 获取文件信息
        file_size = os.path.getsize(destination_path)
        file_type = os.path.splitext(file.filename)[1].lower()
        
        # 保存文件信息到数据库
        file_id, file_token = fuc.save_shared_file(
            session['username'],
            receiver_name,
            file.filename,
            os.path.join('shared_files', unique_filename),
            file_size,
            file_type
        )
        
        if file_id:
            # Real-time notification
            socketio.emit('new_private_message', {
                'sender': session['username'],
                'content': file.filename,
                'type': 'file',
                'file_id': file_id,
                'token': file_token,
                'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, room=receiver_name)
            return jsonify({'success': True, 'message': '发送成功'})
        else:
            # 删除已保存的文件
            if os.path.exists(destination_path):
                os.remove(destination_path)
            return jsonify({'success': False, 'message': '发送失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送文件时发生错误: {str(e)}'})

@app.route('/send_voice_message', methods=['POST'])
def send_voice_message():
    """发送语音消息"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        receiver_name = request.form.get('receiver')
        if 'audio' not in request.files:
            return jsonify({'success': False, 'message': '没有上传音频'})
        
        audio_file = request.files['audio']
        
        # 创建文件存储目录
        file_dir = os.path.join(app.root_path, 'static', 'shared_files')
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        
        # 生成唯一的文件名
        import uuid
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"voice_{uuid.uuid4().hex}_{timestamp}.webm"
        destination_path = os.path.join(file_dir, unique_filename)
        
        # 保存文件
        audio_file.save(destination_path)
        
        # 获取文件信息
        file_size = os.path.getsize(destination_path)
        file_type = 'audio/webm'
        
        # 保存文件信息到数据库 (using shared_files table)
        file_id, file_token = fuc.save_shared_file(
            session['username'],
            receiver_name,
            unique_filename,
            os.path.join('shared_files', unique_filename),
            file_size,
            file_type
        )
        
        if file_id:
            # Real-time notification
            socketio.emit('new_private_message', {
                'sender': session['username'],
                'content': unique_filename,
                'file_path': os.path.join('shared_files', unique_filename),
                'type': 'voice',
                'file_id': file_id,
                'token': file_token,
                'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, room=receiver_name)
            
            return jsonify({'success': True, 'message': '发送成功'})
        else:
            return jsonify({'success': False, 'message': '发送失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送语音时发生错误: {str(e)}'})

@app.route('/get_shared_files')
def get_shared_files():
    """获取分享的文件"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        with_user = request.args.get('with_user')
        files = fuc.get_shared_files(session['username'], with_user)
        return jsonify({'success': True, 'data': files})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取分享文件时发生错误: {str(e)}'})

@app.route('/download_file/<token>')
def download_file(token):
    """根据 Token 下载或预览分享的文件"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        from flask import send_file
        # 获取用户权限范围内的文件列表
        files = fuc.get_shared_files(session['username'])
        file_info = None
        
        # 通过 token 查找文件
        for file in files:
            if file.get('token') == token:
                file_info = file
                break
        
        # 向后兼容：如果没找到 token 且 token 是数字，按 ID 查找
        if not file_info and token.isdigit():
            file_id_int = int(token)
            for file in files:
                if file['id'] == file_id_int:
                    file_info = file
                    break
        
        if not file_info:
            return jsonify({'success': False, 'message': '文件不存在或无权限访问'})
        
        # 标记文件为已读
        fuc.mark_file_as_read(file_info['id'])
        
        # 构建文件路径
        file_path = os.path.join(app.root_path, 'static', file_info['file_path'])
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '文件不存在或已删除'})

        # 决定是否预览
        preview_mimetypes = ['image/', 'application/pdf', 'text/', 'video/', 'audio/']
        as_attachment = True
        file_type = (file_info.get('file_type') or '').lower()
        if any(file_type.startswith(m) or file_info['file_name'].lower().endswith(('.pdf', '.jpg', '.png', '.mp4', '.mp3', '.txt')) for m in preview_mimetypes):
            as_attachment = False

        response = send_file(file_path, download_name=file_info['file_name'], as_attachment=as_attachment)
        response.headers['Content-Length'] = os.path.getsize(file_path)
        return response
    except Exception as e:
        return jsonify({'success': False, 'message': f'访问文件时发生错误: {str(e)}'})

# 消息撤回相关路由
@app.route('/withdraw_message', methods=['POST'])
def withdraw_message():
    """撤回消息"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        message_id = request.form.get('message_id', type=int)
        message_type = request.form.get('message_type', 'text')
        
        if not message_id or message_type not in ['text', 'image']:
            return jsonify({'success': False, 'message': '参数错误'})
        
        success = False
        if message_type == 'text':
            success = fuc.withdraw_text_message(message_id, session['username'])
        elif message_type == 'image':
            success = fuc.withdraw_image_message(message_id, session['username'])
        
        if success:
            return jsonify({'success': True, 'message': '撤回成功'})
        else:
            return jsonify({'success': False, 'message': '撤回失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'撤回消息时发生错误: {str(e)}'})

# 设置用户主题
@app.route('/set_theme', methods=['POST'])
def set_theme():
    """设置用户主题"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    try:
        theme = request.form.get('theme', 'light')
        if theme not in ['light', 'dark', 'auto']:
            return jsonify({'success': False, 'message': '无效的主题'})
        
        # 更新用户主题偏好
        fuc.create_or_update_user_profile(
            session['username'],
            theme_preference=theme
        )
        
        return jsonify({'success': True, 'message': '主题设置成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'设置主题时发生错误: {str(e)}'})

# 定时检查未读消息并发送通知
def check_unread_messages():
    """检查所有用户的未读消息并发送通知"""
    try:
        conn = fuc.get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有用户
        cursor.execute("SELECT s_name FROM users")
        users = cursor.fetchall()
        
        for user in users:
            username = user['s_name']
            
            # 检查未读文本消息
            cursor.execute('''
                SELECT COUNT(*) as count, sender_name 
                FROM private_text_messages 
                WHERE receiver_name = ? AND is_read = 0
                GROUP BY sender_name
            ''', (username,))
            unread_text = cursor.fetchall()
            
            # 检查未读图片消息
            cursor.execute('''
                SELECT COUNT(*) as count, sender_name 
                FROM private_image_messages 
                WHERE receiver_name = ? AND is_read = 0
                GROUP BY sender_name
            ''', (username,))
            unread_image = cursor.fetchall()
            
            # 检查未读文件
            cursor.execute('''
                SELECT COUNT(*) as count, sender_name 
                FROM shared_files 
                WHERE receiver_name = ? AND is_read = 0
                GROUP BY sender_name
            ''', (username,))
            unread_files = cursor.fetchall()
        
        conn.close()
    except Exception as e:
        print(f"检查未读消息时发生错误: {str(e)}")

import threading
import time


# SocketIO Event Handlers
@socketio.on('connect')
def handle_connect():
    if 'username' in session:
        # User joins their own room for private messages
        join_room(session['username'])
        fuc.update_user_status(session['username'], True)
        emit('status_change', {'username': session['username'], 'status': 'online'}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if 'username' in session:
        fuc.update_user_status(session['username'], False)
        emit('status_change', {'username': session['username'], 'status': 'offline'}, broadcast=True)

@socketio.on('join_group')
def handle_join_group(data):
    group_id = data.get('group_id')
    if group_id:
        join_room(f"group_{group_id}")

@socketio.on('leave_group')
def handle_leave_group(data):
    group_id = data.get('group_id')
    if group_id:
        leave_room(f"group_{group_id}")

@socketio.on('typing')
def handle_typing(data):
    receiver = data.get('receiver')
    if receiver:
        emit('typing', {'sender': session.get('username')}, room=receiver)

@socketio.on('mark_group_read')
def handle_mark_group_read(data):
    message_id = data.get('message_id')
    if message_id:
        fuc.mark_group_message_read(message_id, session['username'])

# Mini Apps Configuration and Routes
MINIAPPS_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'miniapps_storage')
if not os.path.exists(MINIAPPS_STORAGE):
    os.makedirs(MINIAPPS_STORAGE)

@app.route('/miniapps')
def miniapps_list():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    apps = fuc.get_all_miniapps()
    # If using existing files that are not in DB, we should probably sync them or just ignore.
    # For now, we rely on the DB.
    
    return render_template('miniapps_list.html', apps=apps)

@app.route('/miniapps/create')
def miniapps_create():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('miniapps_create.html')

@app.route('/miniapps/upload', methods=['POST'])
def miniapps_upload():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
        
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
        
    if file and file.filename.endswith('.html'):
        filename = file.filename
        
        # Check if file exists in DB
        existing_app = fuc.get_miniapp(filename)
        if existing_app:
            flash('App with this name already exists.')
            return redirect(request.url)
            
        file.save(os.path.join(MINIAPPS_STORAGE, filename))
        
        # Create DB record
        fuc.create_miniapp_record(filename, session['username'], description="Uploaded manually")
        fuc.update_miniapp_status(filename, 'ready')
        
        flash('Mini App uploaded successfully!')
        return redirect(url_for('miniapps_list'))
    else:
        flash('Invalid file type. Please upload .html files.')
        return redirect(request.url)

def background_generate_miniapp(prompt, filename, username):
    """Background task to generate mini-app."""
    try:
        html_content = fuc.generate_miniapp_html(prompt)
        
        # Clean up code fences
        if html_content.startswith('```html'):
            html_content = html_content[7:]
        if html_content.endswith('```'):
            html_content = html_content[:-3]
        
        filepath = os.path.join(MINIAPPS_STORAGE, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        fuc.update_miniapp_status(filename, 'ready')
        print(f"Mini App '{filename}' generated successfully for {username}.")
        
        # Notify via SocketIO (optional, if user is online)
        socketio.emit('miniapp_generated', {'filename': filename, 'status': 'ready'}, room=username)
        
    except Exception as e:
        print(f"Error generating mini-app '{filename}': {str(e)}")
        fuc.update_miniapp_status(filename, 'failed')
        socketio.emit('miniapp_generated', {'filename': filename, 'status': 'failed'}, room=username)

@app.route('/miniapps/generate', methods=['POST'])
def miniapps_generate():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.json
    prompt = data.get('prompt')
    filename = data.get('filename')
    
    if not prompt or not filename:
        return jsonify({'success': False, 'message': 'Missing prompt or filename'}), 400
        
    if not filename.endswith('.html'):
        filename += '.html'
        
    # Check if exists
    existing_app = fuc.get_miniapp(filename)
    if existing_app:
        return jsonify({'success': False, 'message': 'Filename already exists. Please choose another.'}), 400
        
    # Create DB record with 'generating' status
    if fuc.create_miniapp_record(filename, session['username'], description=prompt):
        # Start background thread
        threading.Thread(target=background_generate_miniapp, args=(prompt, filename, session['username'])).start()
        return jsonify({'success': True, 'message': 'Generation started in background.'})
    else:
        return jsonify({'success': False, 'message': 'Database error.'}), 500

@app.route('/miniapps/delete/<filename>', methods=['POST'])
def miniapps_delete(filename):
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    app = fuc.get_miniapp(filename)
    if not app:
        return jsonify({'success': False, 'message': 'App not found'}), 404
        
    # Check ownership
    if app['creator_name'] != session['username']:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
    # Delete file
    try:
        filepath = os.path.join(MINIAPPS_STORAGE, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error deleting file {filename}: {str(e)}")
        
    # Delete DB record
    if fuc.delete_miniapp_record(filename):
        return jsonify({'success': True, 'message': 'App deleted successfully'})
    else:
        return jsonify({'success': False, 'message': 'Database delete failed'}), 500

@app.route('/miniapps/<path:filename>')
def serve_miniapp(filename):
    # Only serve if status is ready
    app = fuc.get_miniapp(filename)
    if not app or app['status'] != 'ready':
       # Fallback checks if file exists, but generally we should respect DB status
       # If file exists but DB says generating, it might be partial.
       pass
       
    return send_from_directory(MINIAPPS_STORAGE, filename)

if __name__ == '__main__':
    APP_IP = os.getenv('APP_IP', '127.0.0.1')  # 默认值
    APP_PORT = int(os.getenv('APP_PORT', 5000)) # 默认值
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'  # 从环境变量读取调试模式
    socketio.run(app, debug=DEBUG_MODE, host=APP_IP, port=APP_PORT)
