# DrawSomething - 你画我猜小游戏

一套基于 Python 原生库实现的 C/S 架构“你画我猜”小游戏，支持多人在线实时互动。

## 项目简介

本项目启发于一次游戏体验。2021年第一次接触到“你画我猜”这款小游戏，逻辑简单互动性强，很有创意，于是着手完成了本项目的最初版。最近通过AI工具，本项目得到极大的完善，实现以下核心功能：
- 支持用户注册/登录
- 在线大厅聊天与用户状态同步
- 房间创建与多人游戏
- 一人作画多人实时作答
- 图像绘制与传输

## 技术架构

### 通信模式
- **架构**：C/S 架构 (Client-Server)
- **网络**：基于 Python 原生 `socket` 库的 TCP 通信
- **协议**：自定义二进制帧协议 (解决粘包问题)
- **序列化**：使用 `pickle` 进行数据对象序列化

### 主要模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 绘图引擎 | [Client/WeChat_Client.py](Client/WeChat_Client.py#L73-L197) | 使用 `tkinter.Canvas` 实现的绘图面板 |
| 网络管理 | [Client/WeChat_Client.py](Client/WeChat_Client.py#L17-L71) | 客户端网络通信封装类 |
| 服务端 | [Server/WeChat_Server.py](Server/WeChat_Server.py#L15-L350) | 多线程服务端控制器 |

## 功能特性

### 1. 用户系统
- 账号注册与持久化存储
- 登录验证与在线状态管理
- 大厅用户列表实时更新

### 2. 大厅功能
- 实时聊天消息广播
- 房间创建与加入
- 在线用户实时显示

### 3. 游戏房间
- 房主权限管理（指定绘画人）
- 绘画人设置答案
- 玩家猜词与验证
- 图像实时传输与显示
- 房间用户状态同步

### 4. 绘图功能
- 支持画笔、直线、箭头、矩形工具
- 橡皮擦与清屏
- 颜色选择器与快捷键支持
- 图片导入与导出

## 技术难点与解决方案

### 1. 网络粘包问题
**问题**：TCP 流式传输导致多个数据包合并或拆分。
**解决**：实现了自定义的帧协议：
```python
# 发送端
data_bytes = pickle.dumps(data)
conn.sendall(struct.pack('i', len(data_bytes)) + data_bytes)

# 接收端
data_len = struct.unpack('i', conn.recv(4))[0]
data = b''
while len(data) < data_len:
    data += conn.recv(BUFFER_SIZE)
```

### 2. 多线程资源安全
**问题**：多用户并发修改房间状态、在线列表。
**解决**：使用 `threading.Lock` 保护关键资源：
```python
with self.lock:
    self.rooms[room_name]["players"].append(user)
```

### 3. Tkinter 线程安全更新
**问题**：网络线程直接修改 UI 会导致界面卡死。
**解决**：使用 `after()` 方法将 UI 操作注入主线程：
```python
self.main_window.after(0, lambda d=data: self.handle_server_msg(d))
```

### 4. 客户端收发分离
**设计**：
- 主线程处理 UI 事件
- 独立守护线程监听服务端消息
- 状态变更通过回调更新界面

## 快速开始

### 环境要求
- Python 3.6+
- 仅需标准库（`socket`, `threading`, `pickle`, `struct`, `tkinter`, `PIL`）

### 运行服务端
```bash
cd Server
python WeChat_Server.py
```

### 运行客户端
```bash
cd Client
python WeChat_Client.py
```

## 项目结构

```
DrawSomething/
├── Client/
│   ├── WeChat_Client.py  # 客户端主程序
│   ├── background.png     # 界面背景图
│   ├── my_picture1.jpg    # 测试图片
│   ├── my_picture2.jpg
│   ├── sent_pic.jpg       # 发送图片缓存
│   └── received_pic.jpg   # 接收图片缓存
└── Server/
    ├── WeChat_Server.py   # 服务端主程序
    └── usr_info.pickle    # 用户数据库
```

## 通信协议设计

### 消息格式
```python
{
    "cmd": "chat",        # 命令类型
    "user": "player1",    # 发送者
    "msg": "hello",       # 数据载荷
    ...                   # 其他字段
}
```

### 主要命令列表
| 命令 | 说明 | 发起方 |
|------|------|--------|
| `login` | 登录请求 | Client |
| `register` | 注册请求 | Client |
| `chat` | 聊天消息 | Both |
| `create_room` | 创建房间 | Client |
| `join_room` | 加入房间 | Client |
| `exit_room` | 退出房间 | Client |
| `guess` | 猜词 | Client |
| `image` | 传输绘图 | Client |
| `set_drawer` | 设置绘画人 | Client (Host) |
| `set_word` | 设置答案 | Client (Drawer) |
| `online`/`offline` | 上下线通知 | Server |

## 开发总结

### 工作完成
✅ 解决绘图工具问题（画笔、图形选择、颜色、保存）  
✅ 实现图像传输与显示  
✅ 设计大厅与房间界面切换逻辑  
✅ 实现登录验证与用户管理  
✅ 实现房间创建、加入与多人互动  
✅ 实现问答验证与游戏流程  
✅ 完善异常处理与状态同步  
✅ 规范化代码重构

### 下一步优化方向
- 使用加密传输 (TLS)
- 支持更多绘图工具与图层
- 实现房间聊天独立
- 添加游戏计分系统
- 使用更现代的 UI 框架重写 (PyQt6/Kivy)

## 许可证
本项目仅供学习交流使用, 有待提升, 欢迎PR！
