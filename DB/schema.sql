CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    dorm_room VARCHAR(20) DEFAULT NULL
);



-- 创建教师表
CREATE TABLE teachers (
    teacher_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_info VARCHAR(255)
);

-- 创建宿管人员表
CREATE TABLE dorm_managers (
    manager_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_info VARCHAR(255)
);

-- 创建学生表
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_info VARCHAR(255)
);

-- 创建通知表
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    send_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(10) NOT NULL  -- 可以是已读或未读
    -- 可以添加其他属性
);

-- 创建寝室表
CREATE TABLE dormitories (
    dormitory_id SERIAL PRIMARY KEY
    -- 可以添加其他属性
);

-- 创建学生寝室关联表（多对多关系）
CREATE TABLE student_dormitories (
    student_id INT REFERENCES students (student_id),
    dormitory_id INT REFERENCES dormitories (dormitory_id),
    PRIMARY KEY (student_id, dormitory_id)
);


-- 创建教师通知关联表（多对多关系）
CREATE TABLE teacher_notifications (
    teacher_id INT REFERENCES teachers(teacher_id),
    notification_id INT REFERENCES notifications(notification_id),
    PRIMARY KEY (teacher_id, notification_id)
);

-- 创建宿管人员通知关联表（多对多关系）
CREATE TABLE dorm_manager_notifications (
    manager_id INT REFERENCES dorm_managers(manager_id),
    notification_id INT REFERENCES notifications(notification_id),
    PRIMARY KEY (manager_id, notification_id)
);
-- 创建寝室通知关联表（多对多关系）
CREATE TABLE dormitory_notifications (
    dormitory_id INT REFERENCES dormitories(dormitory_id),
    notification_id INT REFERENCES notifications(notification_id),
    PRIMARY KEY (dormitory_id, notification_id)
);

-- 为实现撤回在终端

--1
-- 删除教师通知关联表的外键约束
ALTER TABLE teacher_notifications
DROP CONSTRAINT IF EXISTS teacher_notifications_notification_id_fkey;

-- 删除宿管人员通知关联表的外键约束
ALTER TABLE dorm_manager_notifications
DROP CONSTRAINT IF EXISTS dorm_manager_notifications_notification_id_fkey;


--2
-- 添加教师通知关联表的外键约束
ALTER TABLE teacher_notifications
ADD CONSTRAINT teacher_notifications_notification_id_fkey
FOREIGN KEY (notification_id)
REFERENCES notifications(notification_id)
ON DELETE CASCADE;

-- 添加宿管人员通知关联表的外键约束
ALTER TABLE dorm_manager_notifications
ADD CONSTRAINT dorm_manager_notifications_notification_id_fkey
FOREIGN KEY (notification_id)
REFERENCES notifications(notification_id)
ON DELETE CASCADE;

--更新用户表
--在users 表中添加一个 is_admin 列，表示是否为管理员，SQL 命令为：
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT false;
--在 users 表中添加一个新列 is_approved，用于标记用户是否已被管理员批准
ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT false;

-- 创建管理员表
CREATE TABLE admins (
    admin_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    additional_info VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 插入管理员数据
-- 注意：这里假设用户表中已经有一个管理员用户的记录
-- 'admin_user_id' 应该替换为该管理员用户的实际用户ID
--INSERT INTO admins (user_id, additional_info) VALUES ('admin_user_id', 'some_additional_info_for_admin');
INSERT INTO users (username, password, role, is_approved, is_admin) VALUES ('ysadmin', '123456', 'admins', true, true);


-- 插入学生表
INSERT INTO users (username, password, role, is_approved, is_admin) VALUES ('student1', 's1', 'student', true, false)
RETURNING id;
-- 用返回的用户ID插入学生表
-- 假设返回的ID存储在变量 user_id 中
INSERT INTO students (student_id, name, contact_info) VALUES (30, 'student1', 'Student Contact Info');
INSERT INTO admins (user_id, additional_info) VALUES (1, 'ysadmin');