# 漂流瓶聊天程序 - 网页版 v3.0

这是一个基于Flask的全功能网页版聊天应用，集成了AI助手、实时通讯、社交网络等多种功能。

## 项目概述

漂流瓶聊天程序从最初的命令行版本(v1.1)发展而来，经过图形界面版本(v2.0)，现已演进为功能丰富的网页应用(v3.0)。本项目采用前后端分离架构，后端使用Python Flask框架，前端使用Bootstrap 5和jQuery，通过Socket.IO实现实时通信，并集成了AI助手功能。

## 版本历史

- **v1.1** - 基础命令行版本，实现基本的漂流瓶功能
- **v2.0** - 图形界面版本，新增私聊和图片功能
- **v2.0 网页版** - 基于Flask的网页版本，新增群组功能
- **v3.0** - 当前版本，新增AI功能、Mini Apps平台、实时通讯等

## 核心功能

### 1. 用户系统
- 用户注册和登录
- 密码哈希加密存储
- 用户在线状态实时显示
- 个人资料管理（头像、简介、生日等）
- 主题切换（浅色/深色/自动模式）

### 2. 漂流瓶功能
- 发送漂流瓶消息（支持永久保存选项）
- 随机接收漂流瓶
- 回复漂流瓶并建立私聊

### 3. 私聊功能
- 文本消息发送与接收
- 图片消息（支持JPG、PNG、GIF格式）
- 文件分享（支持多种文件格式）
- 语音消息录制与发送
- 消息已读/未读状态显示
- 消息撤回功能
- 实时输入状态提示

### 4. 群组功能
- 创建群组并设置群组头像
- 群组角色管理（创建者、管理员、普通成员）
- 群组邀请链接生成与分享
- 群公告发布与管理
- 群组聊天
- 成员权限管理（提升/降级/移除成员）

### 5. 朋友圈功能
- 发布动态（文本+图片）
- 点赞与取消点赞
- 评论互动

### 6. AI智能功能 ⭐ NEW
- **AI自动回复**：用户可开启AI自动回复，在忙碌时自动回复消息
- **AI好友**：添加AI助手为好友，进行智能对话
- **消息总结**：AI智能总结未读消息内容
- **回复生成**：AI帮助生成聊天回复建议
- **群组AI助手**：在群组中使用 `/AI` 命令调用AI助手

### 7. Mini Apps平台 ⭐ NEW
- **AI生成应用**：通过自然语言描述生成HTML5单页应用
- **上传自定义应用**：上传自己开发的HTML应用
- **应用管理**：查看、删除已创建的应用
- **应用分享**：与好友分享有趣的Mini应用

### 8. 实时通讯
- Socket.IO WebSocket连接
- 实时消息推送
- 在线状态同步
- 输入状态提示
- 群组实时聊天

### 9. 安全特性
- CSRF令牌保护
- 密码哈希加密（pbkdf2:sha256）
- 文件上传类型和大小限制
- SQL注入防护
- XSS攻击防护（HTML转义）
- 安全的文件名处理

## 技术栈

### 后端技术
- **Python 3.13** - 编程语言
- **Flask 2.3.2** - Web应用框架
- **Flask-SocketIO 5.3.0** - WebSocket实时通信
- **Flask-WTF 1.2.2** - 表单验证和CSRF保护
- **SQLite** - 轻量级关系数据库
- **python-dotenv 1.1.1** - 环境变量管理
- **requests 2.31.0** - HTTP客户端（用于AI API调用）

### 前端技术
- **HTML5** - 标记语言
- **CSS3** - 样式设计
- **JavaScript ES6+** - 脚本语言
- **Bootstrap 5.3.0** - UI组件库
- **jQuery 3.6.0** - JavaScript库
- **Font Awesome 6.4.0** - 图标库
- **Socket.IO 4.0.1** - WebSocket客户端

### AI集成
- 第三方AI API集成（用于智能对话和内容生成）
- 支持上下文记忆的多轮对话
- 智能提示词工程

## 数据库设计

### 核心数据表

| 表名 | 说明 |
|------|------|
| users | 用户基本信息 |
| mm | 漂流瓶消息 |
| private_text_messages | 私聊文本消息 |
| private_image_messages | 私聊图片消息 |
| groups | 群组信息 |
| group_members | 群组成员关系 |
| group_messages | 群组消息 |
| moments | 朋友圈动态 |
| moment_comments | 朋友圈评论 |
| moment_likes | 朋友圈点赞 |
| user_status | 用户在线状态 |
| user_profiles | 用户扩展资料 |
| shared_files | 共享文件记录 |
| message_withdrawals | 消息撤回记录 |
| miniapps | Mini应用记录 |

## 项目结构

```
web_version_of_messages/
├── app.py                      # Flask主应用入口
├── fuc.py                      # 数据库操作和业务逻辑
├── main.py                     # 旧版本入口（已废弃）
├── migrate_passwords.py        # 密码迁移脚本
├── requirements.txt            # Python依赖列表
├── pyproject.toml              # 项目配置文件
├── README.md                   # 项目说明文档
├── .env                        # 环境配置文件（需手动创建）
├── .gitignore                  # Git忽略文件配置
├── run_tunnel.sh               # 内网穿透启动脚本
│
├── static/                     # 静态资源目录
│   ├── css/                    # CSS样式文件
│   │   └── style.css           # 主样式文件
│   ├── images/                 # 图片资源
│   ├── avatars/                # 用户头像存储
│   ├── moments/                # 朋友圈图片存储
│   ├── shared_files/           # 共享文件存储
│   │   └── voice/              # 语音消息存储
│   ├── group_avatars/          # 群组头像存储
│   └── favicon.svg             # 网站图标
│
├── templates/                  # HTML模板目录
│   ├── base.html               # 基础布局模板
│   ├── login.html              # 登录页面
│   ├── register.html           # 注册页面
│   ├── main.html               # 主页面（聊天界面）
│   ├── profile.html            # 个人资料页面
│   ├── moments.html            # 朋友圈页面
│   ├── about.html              # 关于页面
│   ├── download.html           # 下载页面
│   ├── miniapps_list.html      # Mini应用列表页面
│   └── miniapps_create.html    # Mini应用创建页面
│
├── miniapps_storage/           # Mini应用存储目录
│   ├── index.html              # 示例应用
│   └── ...                     # 其他HTML应用
│
└── .venv/                      # Python虚拟环境（不提交到Git）
```

## 安装部署

### 环境要求

- Python 3.6 或更高版本（推荐 3.13）
- 现代浏览器（Chrome、Firefox、Safari、Edge等）
- SQLite数据库（项目自带，无需额外安装）

### 安装步骤

#### 1. 获取项目代码

```bash
# 克隆项目
git clone https://github.com/BoonieBear/chatingAPP.git

# 进入项目目录
cd chatingAPP/web_version_of_messages
```

#### 2. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# 应用配置
APP_IP=0.0.0.0              # 监听IP地址（0.0.0.0表示所有网卡）
APP_PORT=5000               # 监听端口号
SECRET_KEY=your-secret-key  # Flask密钥（生产环境必须修改）
MAX_CONTENT_LENGTH=200      # 上传文件大小限制(MB)
```

#### 5. 初始化数据库

首次运行时会自动创建SQLite数据库文件 `chat.db` 并初始化所有表结构。

#### 6. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动（具体地址取决于配置）。

### 生产环境部署建议

1. **使用生产服务器**：
   ```bash
   pip install gunicorn eventlet
   gunicorn --worker-class eventlet -w 1 app:app
   ```

2. **使用Nginx反向代理**：
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

3. **使用HTTPS**：配置SSL证书以保护数据传输安全

4. **修改密钥**：务必修改 `SECRET_KEY` 为强随机字符串

## 使用指南

### 快速开始

1. **注册账号**：访问应用首页，点击"立即注册"创建新账号
2. **登录系统**：使用注册的用户名和密码登录
3. **体验漂流瓶**：点击"发送漂流瓶"或"接收漂流瓶"体验核心功能

### 主要功能使用

#### 漂流瓶
- 点击"发送漂流瓶"按钮，输入消息内容
- 可选择"永久保存"选项，使漂流瓶不被删除
- 点击"接收漂流瓶"随机获取一个漂流瓶
- 点击"回复"可与发送者建立私聊

#### 私聊
- 在左侧聊天列表中选择用户开始聊天
- 支持发送文本、图片、文件、语音消息
- 消息支持撤回功能
- 可查看消息已读状态

#### 群组
- 点击"创建"按钮创建新群组
- 在群组成员页面可获取邀请链接
- 群主和管理员可管理成员权限
- 群组内可使用 `/AI 问题` 调用AI助手

#### AI功能
- 在主页开启"AI自动回复"开关
- 点击机器人图标添加AI好友
- 点击魔法棒图标总结未读消息
- 在聊天界面点击魔法棒图标生成回复

#### Mini Apps
- 访问"Mini Apps"页面
- 点击"创建新应用"，输入描述让AI生成应用
- 或上传自定义HTML文件
- 点击应用名称即可运行

### 快捷操作

- **Enter键**：在聊天输入框中按Enter发送消息
- **主题切换**：点击右下角月亮/太阳图标切换深色/浅色主题

## 开发说明

### API接口

项目提供RESTful API接口，主要接口包括：

#### 用户相关
- `POST /login` - 用户登录
- `POST /register` - 用户注册
- `GET /logout` - 用户登出
- `GET /profile` - 个人资料页面
- `POST /update_user_profile` - 更新个人资料

#### 漂流瓶
- `POST /send_bottle` - 发送漂流瓶
- `GET /receive_bottle` - 接收漂流瓶
- `POST /reply_bottle` - 回复漂流瓶

#### 私聊
- `GET /chat_users` - 获取聊天用户列表
- `GET /chat_messages/<username>` - 获取聊天记录
- `POST /send_private_message` - 发送文本消息
- `POST /send_private_image` - 发送图片消息
- `POST /send_file` - 发送文件
- `POST /send_voice_message` - 发送语音消息
- `POST /withdraw_message` - 撤回消息

#### 群组
- `POST /create_group` - 创建群组
- `GET /user_groups` - 获取用户群组列表
- `GET /group_members/<group_id>` - 获取群组成员
- `POST /add_group_member` - 添加群组成员
- `GET /join_group/<token>` - 通过邀请链接加入群组
- `POST /send_group_message` - 发送群组消息

#### AI功能
- `POST /toggle_ai_auto_reply` - 切换AI自动回复
- `GET /get_ai_auto_reply_status` - 获取AI自动回复状态
- `POST /summarize_unread` - 总结未读消息
- `POST /generate_reply` - 生成回复
- `POST /add_ai_friend` - 添加AI好友

#### Mini Apps
- `GET /miniapps` - Mini应用列表页面
- `GET /miniapps/create` - 创建应用页面
- `POST /miniapps/generate` - AI生成应用
- `POST /miniapps/upload` - 上传应用
- `POST /miniapps/delete/<filename>` - 删除应用
- `GET /miniapps/<filename>` - 访问应用

### Socket.IO事件

#### 客户端事件
- `connect` - 连接到服务器
- `disconnect` - 断开连接
- `join_group` - 加入群组房间
- `leave_group` - 离开群组房间
- `typing` - 发送输入状态
- `mark_group_read` - 标记群消息已读

#### 服务器事件
- `new_private_message` - 新私聊消息通知
- `new_group_message` - 新群组消息通知
- `status_change` - 用户状态变化通知
- `typing` - 输入状态通知
- `miniapp_generated` - Mini应用生成完成通知

### 数据库操作

数据库操作函数位于 `fuc.py` 文件中，主要包括：

- `get_db_connection()` - 获取数据库连接
- `init_db()` - 初始化数据库表结构
- `update_database()` - 更新数据库结构（添加新字段/表）

### 扩展开发

#### 添加新的API接口

1. 在 `app.py` 中添加路由函数
2. 在 `fuc.py` 中实现业务逻辑
3. 更新前端JavaScript代码调用新接口

#### 添加新的数据库表

1. 在 `fuc.py` 的 `init_db()` 或 `update_database()` 函数中添加建表SQL
2. 实现相应的CRUD操作函数
3. 在业务逻辑中调用新函数

#### 添加新的Socket.IO事件

1. 在 `app.py` 中使用 `@socketio.on()` 装饰器定义事件处理函数
2. 在前端JavaScript中使用 `socket.emit()` 发送事件
3. 使用 `socket.on()` 监听服务器事件

## 安全注意事项

1. **生产环境必须修改SECRET_KEY**：使用强随机字符串
2. **文件上传限制**：默认限制200MB，可根据需要调整
3. **密码安全**：使用pbkdf2:sha256哈希存储
4. **CSRF保护**：所有POST请求都需要CSRF令牌
5. **SQL注入防护**：使用参数化查询
6. **XSS防护**：前端输出时进行HTML转义

## 性能优化建议

1. **数据库索引**：为常用查询字段添加索引
2. **静态文件缓存**：配置Web服务器缓存静态资源
3. **消息分页**：大量消息时实现分页加载
4. **图片压缩**：上传图片前进行压缩处理
5. **WebSocket连接池**：使用Redis等实现多进程消息共享

## 常见问题

### Q: 忘记密码怎么办？
A: 目前没有密码找回功能，可以联系管理员直接修改数据库中的密码字段。

### Q: 如何修改上传文件大小限制？
A: 修改 `.env` 文件中的 `MAX_CONTENT_LENGTH` 参数。

### Q: AI功能无法使用？
A: 检查网络连接，确保能访问AI API服务。

### Q: 如何备份数据？
A: 备份 `chat.db` 数据库文件和 `static/` 目录下的所有文件。

### Q: 支持多大规模用户？
A: SQLite适合中小规模应用（数百用户），大规模应用建议迁移到MySQL/PostgreSQL。

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

© 2025 漂流瓶开发团队. 保留所有权利.

本项目仅供学习和研究使用，未经授权不得用于商业用途。

## 联系方式

- GitHub: https://github.com/BoonieBear/chatingAPP
- 开发团队: FYH

## 致谢

感谢所有为本项目做出贡献的开发者！

特别感谢以下开源项目：
- Flask
- Bootstrap
- Socket.IO
- Font Awesome

---

**注意**：本项目持续更新中，如有问题或建议欢迎反馈！
