# 漂流瓶聊天程序 - 网页版

这是一个基于Flask的网页版漂流瓶聊天程序，具有用户注册登录、发送接收漂流瓶、私聊、群聊、朋友圈、文件分享等多种功能。

## 功能特性

- 用户注册和登录
- 发送和接收漂流瓶消息
- 私聊功能（文本、图片、文件、语音消息）
- 群聊功能（创建群组、群成员管理、群公告）
- 朋友圈功能（发布动态、点赞、评论）
- 文件和语音消息分享
- 消息已读未读状态显示
- 用户在线状态显示
- 个人资料管理
- 主题切换（浅色/深色模式）
- 响应式网页设计，适配移动端

## 安装说明

### 环境要求

- Python 3.6+
- SQLite数据库（项目自带，无需额外安装）

### 安装步骤

1. 克隆或下载本项目到本地

2. 进入项目目录
   ```
   cd web_version_of_messages
   ```

3. 创建虚拟环境（推荐）
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

4. 安装依赖
   ```
   pip install -r requirements.txt
   ```

5. 配置环境变量（可选）
   在项目根目录创建 `.env` 文件，可配置以下参数：
   ```
   APP_IP=0.0.0.0      # 应用监听IP
   APP_PORT=5000       # 应用端口
   MAX_CONTENT_LENGTH=200  # 上传文件大小限制(MB)
   ```

## 运行程序

```
python app.py
```

程序将在 `http://localhost:5000` 上运行（具体地址取决于.env配置）。

首次运行时会自动创建SQLite数据库文件 `chat.db`。

## 使用说明

1. 访问 `http://localhost:5000` 进入登录页面
2. 如果没有账号，点击"立即注册"创建新账号
3. 登录后可以：
   - 发送漂流瓶：点击"发送漂流瓶"按钮
   - 接收漂流瓶：点击"接收漂流瓶"按钮
   - 与好友私聊：在左侧聊天列表中选择用户开始聊天
   - 创建群组：点击"创建"按钮创建新群组
   - 发布朋友圈：点击顶部"朋友圈"按钮
   - 搜索用户：在搜索框中输入用户名搜索并添加好友

## 目录结构

```
web_version_of_messages/
├── app.py                 # Flask主程序
├── requirements.txt       # 依赖包列表
├── README.md             # 说明文档
├── .env                  # 环境配置文件（需手动创建）
├── static/               # 静态文件目录
│   ├── css/              # CSS样式文件
│   ├── images/           # 图片文件
│   ├── avatars/          # 用户头像
│   ├── moments/          # 朋友圈图片
│   └── shared_files/     # 分享的文件
└── templates/            # HTML模板目录
    ├── base.html         # 基础模板
    ├── login.html        # 登录页面
    ├── register.html     # 注册页面
    ├── main.html         # 主页面
    ├── profile.html      # 个人资料页面
    ├── moments.html      # 朋友圈页面
    ├── talkroom.html     # 聊天室页面
    ├── about.html        # 关于页面
    └── download.html     # 下载页面
```

## 技术栈

- **后端**: Python, Flask, Flask-SocketIO, SQLite
- **前端**: HTML, CSS, JavaScript, Bootstrap 5, jQuery
- **数据库**: SQLite
- **实时通信**: Socket.IO

## 版本信息

- **当前版本**: v2.0 网页版
- **原始版本**: v1.1 命令行版

## 许可证

© 2025 漂流瓶开发团队. 保留所有权利.