from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.static_folder = 'static'

# 数据库连接配置
# ys数据库
DATABASE_URL = 'postgresql://postgres:092179@localhost/dormitory_notification_system'
# DATABASE_URL = 'postgresql://postgres:123456@localhost/dormitory_notification_system'
# 数据库连接配置
# DATABASE_URL = 'postgresql://postgres:Tlycsjq5200%40@localhost/dormitory_notification_system'

# 欢迎页面路由
@app.route('/')
def welcome():
    return render_template('welcome.html')


# 用户登录和身份验证
# 在 app.py 中
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # 初始化错误消息为None
    user_info = None  # Initialize user_info to None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 连接数据库，并查询用户信息
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, role, password, is_admin, is_approved FROM users WHERE username=%s", (username,))
        # 使用 rowcount 判断是否找到用户
        if cursor.rowcount > 0:
            user_id, role, stored_password, is_admin, is_approved = cursor.fetchone()

            # 检查用户是否被管理员批准
            if not is_approved:
                error = "Your account is not approved yet. Please wait for an administrator to approve your account."
                conn.close()
                return render_template('login.html', error=error)

            # 检查密码是否正确
            if password == stored_password:
                # 根据用户角色进一步查询对应的表验证身份
                if role == 'student':
                    cursor.execute("SELECT * FROM students WHERE student_id=%s", (user_id,))
                    user_info = cursor.fetchone()

                elif role == 'teacher':
                    cursor.execute("SELECT * FROM teachers WHERE teacher_id=%s", (user_id,))
                    user_info = cursor.fetchone()

                elif role == 'dorm_manager':
                    cursor.execute("SELECT * FROM dorm_managers WHERE manager_id=%s", (user_id,))
                    user_info = cursor.fetchone()
                elif role == 'admins':
                    cursor.execute("SELECT * FROM admins WHERE user_id=%s", (user_id,))
                    user_info = cursor.fetchone()
                conn.close()

                if user_info:
                    # 如果验证通过，设置用户会话信息
                    session['user'] = {'id': user_id, 'username': username, 'role': role, 'is_admin': is_admin}
                    # 根据角色跳转到对应的主页
                    if role == 'student':
                        return redirect(url_for('student_home'))
                    elif role == 'teacher':
                        return redirect(url_for('teacher_home'))
                    elif role == 'dorm_manager':
                        return redirect(url_for('dorm_manager_home'))
                    else:  # 添加管理员条件检查
                        # 管理员登录
                        print("12343435")
                        session['user'] = {'id': user_id, 'username': username, 'role': role, 'is_admin': is_admin}
                        return redirect(url_for('admin_dashboard'))
            else:
                error = "Incorrect password. Please try again."
        else:
            error = "Username not found. Please try again."

        conn.close()

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        is_admin = request.form.get('is_admin') == 'on'
        is_approved = False

        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone() is not None:
                return render_template('register.html', error="Username already exists. Please choose a different username.")

            if role == 'student':
                dorm_room = request.form.get('dorm_room')
                cursor.execute("SELECT dormitory_id FROM dormitories WHERE dormitory_id = %s", (dorm_room,))
                dormitory_exists = cursor.fetchone()
                if not dormitory_exists:
                    cursor.execute("INSERT INTO dormitories (dormitory_id) VALUES (%s)", (dorm_room,))

            cursor.execute(
                "INSERT INTO users (username, password, role, is_approved, is_admin) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (username, password, role, is_approved, is_admin))
            user_id = cursor.fetchone()[0]

            if role == 'student':
                cursor.execute("INSERT INTO students (student_id, name) VALUES (%s, %s)", (user_id, username))
                cursor.execute("INSERT INTO student_dormitories (student_id, dormitory_id) VALUES (%s, %s)", (user_id, dorm_room))
            elif role == 'teacher':
                cursor.execute("INSERT INTO teachers (teacher_id, name) VALUES (%s, %s)", (user_id, username))
            elif role == 'dorm_manager':
                cursor.execute("INSERT INTO dorm_managers (manager_id, name) VALUES (%s, %s)", (user_id, username))

            conn.commit()

        except psycopg2.errors.UniqueViolation as e:
            conn.rollback()
            return render_template('register.html', error="Username already exists. Please choose a different username.")
        except Exception as e:
            conn.rollback()
            return render_template('register.html', error=str(e))
        finally:
            if conn:
                conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# 登出
@app.route('/logout',methods=['GET', 'POST'])
def logout():
    # 清除用户的会话数据
    session.pop('user', None)

    # 重定向到登录页面
    return redirect(url_for('login'))


# 用户注销
@app.route('/cancel_account',methods=['GET', 'POST'])
def cancel_account():
    if 'user' in session:
        user_id = session['user']['id']
        user_role = session['user']['role']

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # 根据用户角色删除相关联的信息
        if user_role == 'teacher':
            cursor.execute("DELETE FROM teacher_notifications WHERE teacher_id=%s", (user_id,))
            cursor.execute("DELETE FROM teachers WHERE teacher_id=%s", (user_id,))
        elif user_role == 'dorm_manager':
            cursor.execute("DELETE FROM dorm_manager_notifications WHERE manager_id=%s", (user_id,))
            cursor.execute("DELETE FROM dorm_managers WHERE manager_id=%s", (user_id,))
        elif user_role == 'student':
            cursor.execute("DELETE FROM student_dormitories WHERE student_id=%s", (user_id,))
            cursor.execute("DELETE FROM students WHERE student_id=%s", (user_id,))

        # 删除用户帐户
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))

        conn.commit()
        conn.close()

        # 清除用户的会话数据
        session.pop('user', None)

        # 重定向到登录页面
        return redirect(url_for('login'))

    return redirect(url_for('login'))



# 在teacher_home路由中
@app.route('/teacher_home',methods=['GET', 'POST'])
def teacher_home():
    if 'user' in session:
        user_role = session['user']['role']
        user_id = session['user']['id']

        if user_role == 'teacher':
            # 查询教师关联的通知
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT notification_id, title, content, send_time, status FROM notifications WHERE notification_id IN (SELECT notification_id FROM teacher_notifications WHERE teacher_id=%s)",
                (user_id,))
            notifications = cursor.fetchall()

            conn.close()

            return render_template('teacher_home.html', user=session['user'], notifications=notifications)

    return redirect(url_for('login'))

"""
# 学生主页显示通知
@app.route('/student_home')
def student_home():
    if 'user' in session:
        user_role = session['user']['role']
        user_id = session['user']['id']

        if user_role == 'student':
            # 查询与学生关联的寝室
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT dormitory_id FROM student_dormitories WHERE student_id=%s", (user_id,))
            dormitory_id = cursor.fetchone()

            if dormitory_id:
                dormitory_id = dormitory_id[0]

                # 查询公开通知和与寝室关联的私有通知
                cursor.execute(
                    "SELECT notification_id, title, content, send_time, status FROM notifications WHERE status='public' OR notification_id IN (SELECT notification_id FROM dormitory_notifications WHERE dormitory_id=%s)",
                    (dormitory_id,))
                notifications = cursor.fetchall()
                conn.close()

                return render_template('student_home.html', user=session['user'], notifications=notifications)

    return redirect(url_for('login'))
"""

# 学生主页显示通知
@app.route('/student_home',methods=['GET', 'POST'])
def student_home():
    if 'user' in session:
        user_role = session['user']['role']
        user_id = session['user']['id']

        if user_role == 'student':
            # 查询与学生关联的寝室
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT dormitory_id FROM student_dormitories WHERE student_id=%s", (user_id,))
            dormitory_id = cursor.fetchone()

            if dormitory_id:
                dormitory_id = dormitory_id[0]

                # 查询公开通知和与寝室关联的私有通知以及发送者信息
                cursor.execute(
                    """SELECT 
                           n.notification_id, 
                           n.title, 
                           n.content, 
                           n.send_time, 
                           n.status, 
                           COALESCE(t.name, dm.name) AS sender_name, 
                           COALESCE(t.contact_info, dm.contact_info) AS sender_contact_info, 
                           CASE WHEN t.teacher_id IS NOT NULL THEN 'teacher' 
                                WHEN dm.manager_id IS NOT NULL THEN 'dorm_manager'
                           END AS sender_role 
                       FROM notifications n
                       LEFT JOIN teacher_notifications tn ON n.notification_id = tn.notification_id
                       LEFT JOIN teachers t ON tn.teacher_id = t.teacher_id
                       LEFT JOIN dorm_manager_notifications dmn ON n.notification_id = dmn.notification_id
                       LEFT JOIN dorm_managers dm ON dmn.manager_id = dm.manager_id
                       WHERE n.status='public' OR n.notification_id IN (SELECT notification_id FROM dormitory_notifications WHERE dormitory_id=%s)""",
                    (dormitory_id,))
                notifications = cursor.fetchall()
                conn.close()

                return render_template('student_home.html', user=session['user'], notifications=notifications)

    return redirect(url_for('login'))


# 宿管人员主页显示通知
@app.route('/dorm_manager_home',methods=['GET', 'POST'])
def dorm_manager_home():
    if 'user' in session:
        user_role = session['user']['role']
        user_id = session['user']['id']

        if user_role == 'dorm_manager':
            # 查询宿管人员关联的通知
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT notification_id, title, content, send_time, status FROM notifications WHERE notification_id IN (SELECT notification_id FROM dorm_manager_notifications WHERE manager_id=%s)",
                (user_id,))
            notifications = cursor.fetchall()
            conn.close()

            return render_template('dorm_manager_home.html', user=session['user'], notifications=notifications)

    return redirect(url_for('login'))

# 发送通知
@app.route('/post_notification', methods=['GET', 'POST'])
def post_notification():
    if 'user' in session:
        user_role = session['user']['role']

        if user_role in ['teacher', 'dorm_manager']:
            title = request.form['title']
            content = request.form['content']
            public_notification = request.form.get('public_notification', 'no')

            # 根据角色插入不同的通知
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()

            if public_notification == 'yes':
                # 公开通知
                cursor.execute("INSERT INTO notifications (title, content, status) VALUES (%s, %s, 'public') RETURNING notification_id", (title, content))
                notification_id = cursor.fetchone()[0]

                # 将通知与老师或宿管人员关联
                if user_role == 'teacher':
                    cursor.execute("INSERT INTO teacher_notifications (teacher_id, notification_id) VALUES (%s, %s)", (session['user']['id'], notification_id))
                elif user_role == 'dorm_manager':
                    cursor.execute("INSERT INTO dorm_manager_notifications (manager_id, notification_id) VALUES (%s, %s)", (session['user']['id'], notification_id))

            else:
                # 寝室通知
                dorm_room = request.form.get('dorm_room')

                if not dorm_room:
                    # 处理错误，未提供寝室信息
                    # return render_template('error.html', error_message='Dormitory information is required for private notifications.')
                    return jsonify({'error': 'Dormitory information is required for private notifications.'}), 400
                # 检查寝室是否存在
                cursor.execute("SELECT * FROM dormitories WHERE dormitory_id = %s", (dorm_room,))
                if cursor.fetchone() is None:
                    # 如果寝室不存在
                    # return render_template('error.html', error_message='Dormitory does not exist.')
                    return jsonify({'error': 'Dormitory information is required for private notifications.'}), 400
                # 插入私密通知
                cursor.execute(
                    "INSERT INTO notifications (title, content, status) VALUES (%s, %s, 'private') RETURNING notification_id",
                    (title, content))
                notification_id = cursor.fetchone()[0]

                # 将通知与老师或宿管人员关联
                if user_role == 'teacher':
                    cursor.execute("INSERT INTO teacher_notifications (teacher_id, notification_id) VALUES (%s, %s)", (session['user']['id'], notification_id))
                elif user_role == 'dorm_manager':
                    cursor.execute("INSERT INTO dorm_manager_notifications (manager_id, notification_id) VALUES (%s, %s)", (session['user']['id'], notification_id))

                # 将通知与寝室关联
                cursor.execute("INSERT INTO dormitory_notifications (dormitory_id, notification_id) VALUES (%s, %s)", (dorm_room, notification_id))

            conn.commit()
            conn.close()

            if user_role == 'teacher':
                return redirect(url_for('teacher_home'))

            elif user_role == 'dorm_manager':
                return redirect(url_for('dorm_manager_home'))

    return redirect(url_for('login'))


# 撤回通知
@app.route('/revoke_notification/<int:notification_id>',methods=['GET', 'POST'])
def revoke_notification(notification_id):
    if 'user' in session:
        user_role = session['user']['role']
        user_id = session['user']['id']

        # 检查通知是否属于当前用户
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        if user_role == 'teacher':
            cursor.execute("SELECT * FROM teacher_notifications WHERE teacher_id=%s AND notification_id=%s",
                           (user_id, notification_id))
        elif user_role == 'dorm_manager':
            cursor.execute("SELECT * FROM dorm_manager_notifications WHERE manager_id=%s AND notification_id=%s",
                           (user_id, notification_id))

        if cursor.rowcount > 0:
            # 删除与该通知相关的 dormitory_notifications 记录
            cursor.execute("DELETE FROM dormitory_notifications WHERE notification_id=%s", (notification_id,))

            # 删除通知
            cursor.execute("DELETE FROM notifications WHERE notification_id=%s", (notification_id,))

            # 如果是教师，删除教师通知关联
            if user_role == 'teacher':
                cursor.execute("DELETE FROM teacher_notifications WHERE teacher_id=%s AND notification_id=%s",
                               (user_id, notification_id))
            # 如果是宿管人员，删除宿管人员通知关联
            elif user_role == 'dorm_manager':
                cursor.execute("DELETE FROM dorm_manager_notifications WHERE manager_id=%s AND notification_id=%s",
                               (user_id, notification_id))

            conn.commit()
            conn.close()

            return redirect(url_for(user_role + '_home'))

    return redirect(url_for('login'))

# 在 Flask 应用中添加一个新路由 /admin_dashboard，该路由将用于渲染管理员控制台。
@app.route('/admin_dashboard',methods=['GET', 'POST'])
def admin_dashboard():
    if 'user' in session and session['user'].get('is_admin', False):
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, is_approved FROM users")
        admin_data = cursor.fetchall()
        conn.close()
        print(session['user'])
        print(admin_data)
        return render_template('admin_dashboard.html', user=session['user'], admin_data=admin_data)

    else:
        return "Unauthorized", 403

# 批准或撤回用户
@app.route('/admin_approve_user/<int:user_id>', methods=['GET', 'POST'])
def admin_approve_user(user_id):
    if 'user' in session and session['user'].get('is_admin', False):
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # 查询用户并切换批准状态
        cursor.execute("SELECT is_approved FROM users WHERE id=%s", (user_id,))
        is_approved = cursor.fetchone()[0]

        # 切换批准状态
        new_approval_status = not is_approved
        cursor.execute("UPDATE users SET is_approved=%s WHERE id=%s", (new_approval_status, user_id))

        conn.commit()
        conn.close()

    return redirect(url_for('admin_dashboard'))

# 管理员注销
@app.route('/admin_logout',methods=['GET', 'POST'])
def admin_logout():
    session.clear()  # 清除会话数据
    return redirect(url_for('login'))  # 重定向到登录页面


if __name__ == '__main__':
    app.run(debug=True)
