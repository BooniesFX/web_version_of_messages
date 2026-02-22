# 实时视频会议功能 - 实施计划

## [x] Task 1: 数据库设计与初始化
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 创建会议表 (meetings) 存储会议基本信息
  - 创建会议参与者表 (meeting_participants) 存储参会者信息
  - 创建会议聊天记录表 (meeting_chat_messages) 存储会议内聊天（保存30天）
  - 创建会议录制表 (meeting_recordings) 存储录制文件信息
  - 在 fuc.py 中添加数据库初始化代码
  - 添加定时任务清理超过30天的聊天记录
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - [x] `programmatic` TR-1.1: 数据库表成功创建，包含所有必要字段
  - [x] `programmatic` TR-1.2: 表关系正确，外键约束有效
  - [x] `programmatic` TR-1.3: 初始化函数可重复执行不报错
  - [x] `programmatic` TR-1.4: 录制表包含文件路径、时长、大小等字段
- **Notes**: 参考现有表结构（groups, group_members 等）保持一致性

## Task 2: 后端 API - 会议管理接口
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 实现创建会议 API (POST /create_meeting)
  - 实现获取会议列表 API (GET /meetings)
  - 实现获取会议详情 API (GET /meeting/<id>)
  - 实现更新会议状态 API (POST /update_meeting_status)
  - 实现结束会议 API (POST /end_meeting)
  - 实现获取历史会议列表 API (GET /meeting_history)
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-10, AC-11
- **Test Requirements**:
  - `programmatic` TR-2.1: 创建会议接口返回正确的会议ID和状态
  - `programmatic` TR-2.2: 获取会议列表只返回当前用户相关的会议
  - `programmatic` TR-2.3: 更新会议状态验证权限（仅管理员可更新）
  - `programmatic` TR-2.4: 结束会议后状态变为 ended
  - `programmatic` TR-2.5: 历史会议列表包含已结束会议和回放信息
- **Notes**: 需要验证用户是否为聊天参与者才能创建会议

## Task 3: 后端 API - 会议参与者管理
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 实现加入会议 API (POST /join_meeting)
  - 实现离开会议 API (POST /leave_meeting)
  - 实现获取参会者列表 API (GET /meeting_participants/<id>)
  - 实现管理员控制 API (关闭摄像头/麦克风) (POST /control_participant)
- **Acceptance Criteria Addressed**: AC-3, AC-6, AC-7
- **Test Requirements**:
  - `programmatic` TR-3.1: 加入会议验证会议状态和时间
  - `programmatic` TR-3.2: 获取参会者列表包含在线状态和音视频状态
  - `programmatic` TR-3.3: 管理员控制接口验证权限
  - `programmatic` TR-3.4: 控制命令通过 Socket.IO 广播给目标用户
- **Notes**: 需要与 Socket.IO 集成实现实时状态同步

## Task 4: Socket.IO 信令服务器
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 实现 WebRTC 信令事件处理 (offer, answer, ice-candidate)
  - 实现会议房间管理 (join_meeting_room, leave_meeting_room)
  - 实现参会者状态广播 (participant_joined, participant_left)
  - 实现管理员控制命令转发 (mute_audio, disable_video)
  - 实现举手状态同步 (raise_hand, lower_hand)
  - 实现会议聊天消息转发 (meeting_chat_message)
  - 实现屏幕共享信令 (screen_share_start, screen_share_stop)
- **Acceptance Criteria Addressed**: AC-5, AC-6, AC-8, AC-9
- **Test Requirements**:
  - `programmatic` TR-4.1: WebRTC 信令消息正确转发
  - `programmatic` TR-4.2: 参会者加入/离开事件广播给房间内所有用户
  - `programmatic` TR-4.3: 管理员控制命令正确转发给目标用户
  - `programmatic` TR-4.4: 举手状态变化实时同步
  - `programmatic` TR-4.5: 会议聊天消息实时广播
  - `programmatic` TR-4.6: 屏幕共享信令正确转发
- **Notes**: 参考现有的 socketio 事件处理模式

## Task 5: 前端 UI - 会议预约模态框
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 main.html 中添加"+"按钮到下拉菜单
  - 创建会议预约模态框 (scheduleMeetingModal)
  - 实现日期时间选择器（开始时间、结束时间）
  - 实现2小时限制验证
  - 实现会议标题输入和参会者显示
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `human-judgment` TR-5.1: 模态框样式与现有UI风格一致
  - `human-judgment` TR-5.2: 日期时间选择器易用，有清晰的错误提示
  - `programmatic` TR-5.3: 结束时间超过2小时时显示错误提示
  - `programmatic` TR-5.4: 提交表单调用正确的API接口
- **Notes**: 使用 Bootstrap 5 的模态框组件

## Task 6: 前端 UI - 会议卡片组件
- **Priority**: P0
- **Depends On**: Task 5
- **Description**: 
  - 创建会议卡片 HTML 模板
  - 显示会议标题、时间、状态
  - 实现加入按钮（根据时间条件启用/禁用）
  - 在私聊和群聊消息列表中渲染会议卡片
- **Acceptance Criteria Addressed**: AC-2, AC-3
- **Test Requirements**:
  - `human-judgment` TR-6.1: 会议卡片样式美观，信息清晰
  - `programmatic` TR-6.2: 会议开始前10分钟加入按钮自动启用
  - `programmatic` TR-6.3: 已结束会议显示正确状态且无法加入
  - `programmatic` TR-6.4: 点击加入按钮跳转到会议页面
- **Notes**: 需要定时检查会议状态更新UI

## Task 7: 前端页面 - 视频会议主界面（桌面端）
- **Priority**: P0
- **Depends On**: Task 6
- **Description**: 
  - 创建 meeting.html 模板
  - 实现视频网格布局（自适应不同参会人数）
  - 实现本地视频预览
  - 实现远程视频流显示
  - 实现参会者信息覆盖层（用户名、状态图标）
  - 实现桌面端横屏布局
- **Acceptance Criteria Addressed**: AC-4, AC-5
- **Test Requirements**:
  - `human-judgment` TR-7.1: 视频网格布局美观，支持1-20人
  - `human-judgment` TR-7.2: 视频画面清晰，无明显延迟
  - `programmatic` TR-7.3: 本地视频正确获取并显示
  - `programmatic` TR-7.4: 远程视频流正确接收并显示
- **Notes**: 使用 CSS Grid 实现自适应视频布局

## Task 8: 前端功能 - 媒体控制
- **Priority**: P0
- **Depends On**: Task 7
- **Description**: 
  - 实现麦克风开关功能
  - 实现摄像头开关功能
  - 实现底部控制栏UI
  - 实现状态图标更新
  - 通过 Socket.IO 同步状态给其他参会者
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `programmatic` TR-8.1: 点击麦克风按钮切换音频轨道启用状态
  - `programmatic` TR-8.2: 点击摄像头按钮切换视频轨道启用状态
  - `programmatic` TR-8.3: 状态变化通过 Socket.IO 广播
  - `human-judgment` TR-8.4: 按钮图标正确反映当前状态
- **Notes**: 使用 WebRTC getUserMedia API 获取媒体流

## Task 9: 前端功能 - WebRTC 连接管理
- **Priority**: P0
- **Depends On**: Task 4, Task 8
- **Description**: 
  - 实现 RTCPeerConnection 创建和管理
  - 实现 SDP offer/answer 交换
  - 实现 ICE candidate 交换
  - 处理新参会者加入时的连接建立
  - 处理参会者离开时的连接清理
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-9.1: 新用户加入时正确创建 peer connection
  - `programmatic` TR-9.2: SDP 交换成功建立连接
  - `programmatic` TR-9.3: ICE 连接状态变化正确处理
  - `programmatic` TR-9.4: 用户离开时清理对应连接
- **Notes**: 使用 mesh 拓扑结构（每个参会者与其他所有人建立连接）

## Task 10: 前端功能 - 屏幕共享
- **Priority**: P0
- **Depends On**: Task 9
- **Description**: 
  - 实现屏幕共享按钮功能
  - 使用 getDisplayMedia API 获取屏幕流
  - 实现屏幕共享视频在网格中突出显示
  - 实现停止屏幕共享功能
  - 通过 Socket.IO 通知其他参会者屏幕共享状态
- **Acceptance Criteria Addressed**: FR-7
- **Test Requirements**:
  - `programmatic` TR-10.1: 点击屏幕共享按钮成功获取屏幕流
  - `programmatic` TR-10.2: 屏幕共享视频替换本地视频发送
  - `human-judgment` TR-10.3: 屏幕共享画面清晰，帧率稳定
  - `programmatic` TR-10.4: 停止共享后恢复正常视频
- **Notes**: 同一时间只允许一人共享屏幕

## Task 11: 后端 API - 会议录制管理
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 实现开始录制 API (POST /start_recording)
  - 实现停止录制 API (POST /stop_recording)
  - 实现获取录制列表 API (GET /meeting_recordings/<meeting_id>)
  - 实现下载/播放录制 API (GET /playback/<recording_id>)
  - 集成 MediaRecorder API 或服务器端录制方案
- **Acceptance Criteria Addressed**: FR-8
- **Test Requirements**:
  - `programmatic` TR-11.1: 开始录制接口验证管理员权限
  - `programmatic` TR-11.2: 录制文件正确保存到服务器
  - `programmatic` TR-11.3: 录制信息正确记录到数据库
  - `programmatic` TR-11.4: 回放接口正确返回视频流
- **Notes**: 考虑使用客户端录制+上传或服务器端录制方案

## Task 12: 前端功能 - 录制控制与回放
- **Priority**: P0
- **Depends On**: Task 11
- **Description**: 
  - 实现录制开关按钮（仅管理员可见）
  - 实现录制状态显示（红色录制指示灯）
  - 实现会议回放页面
  - 实现视频播放器控件（播放、暂停、进度条、倍速）
  - 实现回放时同步显示聊天记录
- **Acceptance Criteria Addressed**: FR-8
- **Test Requirements**:
  - `human-judgment` TR-12.1: 录制按钮仅管理员可见
  - `human-judgment` TR-12.2: 录制状态清晰显示
  - `human-judgment` TR-12.3: 回放页面布局美观，播放流畅
  - `programmatic` TR-12.4: 回放时聊天记录同步显示
- **Notes**: 回放页面可复用会议界面布局

## Task 13: 前端功能 - 管理员控制面板
- **Priority**: P1
- **Depends On**: Task 7
- **Description**: 
  - 实现参会者列表侧边栏
  - 为管理员显示控制按钮（关闭摄像头/麦克风）
  - 实现"结束会议"按钮（仅管理员可见）
  - 实现"开关聊天窗口"按钮
  - 实现"开始/停止录制"按钮
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `human-judgment` TR-13.1: 管理员控制面板布局清晰
  - `programmatic` TR-13.2: 控制按钮仅对管理员显示
  - `programmatic` TR-13.3: 点击控制按钮发送命令到服务器
  - `programmatic` TR-13.4: 接收到控制命令后执行相应操作
- **Notes**: 需要检查当前用户是否为会议创建者

## Task 14: 前端功能 - 举手和全屏
- **Priority**: P1
- **Depends On**: Task 8
- **Description**: 
  - 实现举手按钮功能
  - 实现举手状态显示（在视频画面上显示举手图标）
  - 实现全屏切换功能
  - 实现全屏状态下的UI适配
- **Acceptance Criteria Addressed**: AC-8, AC-12
- **Test Requirements**:
  - `programmatic` TR-14.1: 点击举手按钮切换举手状态
  - `programmatic` TR-14.2: 举手状态通过 Socket.IO 广播
  - `programmatic` TR-14.3: 全屏API调用成功
  - `human-judgment` TR-14.4: 全屏模式下视频布局正确适配
- **Notes**: 使用 Fullscreen API 实现全屏功能

## Task 15: 前端功能 - 会议聊天（持久化）
- **Priority**: P1
- **Depends On**: Task 4
- **Description**: 
  - 实现会议聊天侧边栏/浮动窗口
  - 实现消息输入和发送
  - 实现消息列表显示
  - 实现系统消息显示（用户加入/离开、举手等）
  - 实现聊天窗口开关功能
  - 实现历史聊天记录加载（从数据库读取）
- **Acceptance Criteria Addressed**: AC-9, FR-5
- **Test Requirements**:
  - `programmatic` TR-15.1: 发送消息保存到数据库
  - `programmatic` TR-15.2: 接收到消息正确显示在列表中
  - `programmatic` TR-15.3: 系统消息正确显示
  - `programmatic` TR-15.4: 历史聊天记录可正确加载（30天内）
  - `human-judgment` TR-15.5: 聊天界面美观，滚动正常
- **Notes**: 会议聊天消息保存30天

## Task 16: 前端功能 - 会议列表与历史记录
- **Priority**: P1
- **Depends On**: Task 2
- **Description**: 
  - 创建"所有视频会议"页面/模态框（从"+"菜单进入）
  - 显示所有可加入的会议
  - 显示历史会议列表（已结束）
  - 历史会议显示录制状态和回放按钮
  - 历史会议显示聊天记录查看按钮
  - 按时间排序显示会议
  - 区分不同状态的会议（待开始/进行中/已结束）
- **Acceptance Criteria Addressed**: AC-3, FR-8
- **Test Requirements**:
  - `programmatic` TR-16.1: 正确获取并显示用户的所有会议
  - `programmatic` TR-16.2: 会议按开始时间排序
  - `programmatic` TR-16.3: 历史会议显示录制和回放信息
  - `human-judgment` TR-16.4: 会议列表界面清晰，易于导航
- **Notes**: 作为独立页面实现，可从"+"菜单访问

## Task 17: 前端页面 - 视频会议界面（移动端）
- **Priority**: P0
- **Depends On**: Task 7
- **Description**: 
  - 实现移动端竖屏布局
  - 实现可滑动的视频网格
  - 实现底部控制栏（简化版）
  - 实现底部弹出式聊天窗口
  - 实现抽屉式参会者列表
  - 适配触摸操作（按钮大小、手势）
- **Acceptance Criteria Addressed**: FR-9
- **Test Requirements**:
  - `human-judgment` TR-17.1: 移动端布局美观，操作便捷
  - `human-judgment` TR-17.2: 视频网格滑动流畅
  - `human-judgment` TR-17.3: 控制栏按钮大小适合触摸
  - `human-judgment` TR-17.4: 聊天窗口和参会者列表交互自然
- **Notes**: 使用响应式设计和移动端优化CSS

## Task 18: 会议状态自动更新
- **Priority**: P1
- **Depends On**: Task 2
- **Description**: 
  - 实现定时检查会议状态（使用 setInterval 或类似机制）
  - 到达开始时间自动将会议状态改为 active
  - 到达结束时间自动将会议状态改为 ended
  - 通知所有参会者状态变化
- **Acceptance Criteria Addressed**: AC-11
- **Test Requirements**:
  - `programmatic` TR-18.1: 定时任务正确运行
  - `programmatic` TR-18.2: 会议状态在正确时间点更新
  - `programmatic` TR-18.3: 状态变化通知发送到客户端
- **Notes**: 考虑使用后端定时任务或前端轮询

## Task 19: 错误处理和用户体验优化
- **Priority**: P2
- **Depends On**: Task 7, Task 9
- **Description**: 
  - 实现摄像头/麦克风权限被拒绝的处理
  - 实现设备不可用时的降级方案（仅音频）
  - 实现网络断开检测和重连
  - 添加加载状态和错误提示
  - 优化移动端触摸体验
- **Acceptance Criteria Addressed**: NFR-4
- **Test Requirements**:
  - `human-judgment` TR-19.1: 权限被拒绝时显示友好的提示信息
  - `human-judgment` TR-19.2: 网络问题时显示连接状态提示
  - `human-judgment` TR-19.3: 移动端操作流畅，按钮大小合适
- **Notes**: 参考现有应用的错误处理模式

## Task 20: 集成测试和调试
- **Priority**: P0
- **Depends On**: All above tasks
- **Description**: 
  - 进行端到端功能测试
  - 测试多人同时参会场景
  - 测试管理员控制功能
  - 测试会议状态转换
  - 测试屏幕共享功能
  - 测试录制和回放功能
  - 测试移动端适配
  - 修复发现的bug
- **Acceptance Criteria Addressed**: All ACs
- **Test Requirements**:
  - `human-judgment` TR-20.1: 完整功能流程测试通过
  - `human-judgment` TR-20.2: 多人会议音视频质量可接受
  - `human-judgment` TR-20.3: 屏幕共享功能正常
  - `human-judgment` TR-20.4: 录制和回放功能正常
  - `human-judgment` TR-20.5: 移动端界面和操作正常
  - `programmatic` TR-20.6: 所有API接口返回正确结果
- **Notes**: 需要至少3个测试用户进行多人测试
