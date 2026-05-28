import socket
import threading
import pickle
import struct
import os

def get_host_ip():
    """
    查询本机局域网IP地址
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def get_public_ip():
    """
    查询本机公网IP地址
    """
    try:
        import urllib.request
        # 使用一个可靠的 API 获取公网 IP
        return urllib.request.urlopen('http://ident.me', timeout=3).read().decode('utf8')
    except:
        return "无法获取（可能无公网访问权限或网络受限）"

#监听物理网卡上的所有局域网/公网 IP
HOST = '0.0.0.0'
PORT = 80
BUFFER_SIZE = 4096

print(f"服务器正在启动...")
print(f"========================================")
print(f"1.1. 局域网连接请使用 IP: {get_host_ip()}")
print(f"1.2. 跨局域网连接（需内网穿透/公网IP）请使用 IP: {get_public_ip()}")
print(f"2. 端口: {PORT}")
print(f"========================================")

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'usr_info.pickle')
# 全局数据
conn_users = []
conn_ad = {}
conn_so = {}
rooms = {}    # {房间名: {"host":"", "drawer": user, "word": "", "players": [socket列表]}}
lock = threading.Lock()

def load_users():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, 'rb') as f:
                return pickle.load(f)
        except:
            # 如果文件为空或损坏
            print(f"{DB_PATH}文件为空或损坏!")
            return {}
    return {}

def save_users(users):
    with open(DB_PATH, 'wb') as f:
        pickle.dump(users, f)

def send_data(conn, data):
    """发送数据（解决粘包）"""
    data_bytes = pickle.dumps(data)
    conn.sendall(struct.pack('i', len(data_bytes)) + data_bytes)

def recv_data(conn):
    """接收数据（解决粘包）"""
    data_len = struct.unpack('i', conn.recv(4))[0]
    data = b''
    while len(data) < data_len:
        packet = conn.recv(min(data_len - len(data), BUFFER_SIZE))
        if not packet:
            return None
        data += packet
    return pickle.loads(data)

def validate_logon(conn, ad):
    authenticated = False
    data = recv_data(conn)
    print(f"接收到登录消息{data}")
    cmd = data["cmd"]
    this_username = data["username"]
    password = data["password"]
    users = load_users()
    try:
        if cmd == 'login':
            if len(users)==0:
                print("用户库中没有数据")
            elif this_username not in users:
                send_data(conn, {cmd:"fail_null"})
                print(f"用户[{this_username}]不存在, 用户库[{users}]")
            elif this_username in users and users[this_username] != password:
                send_data(conn, {cmd:"fail_error"})
                print(f"用户[{this_username}]密码错误")
            elif this_username in users and users[this_username] == password:
                authenticated = True
        elif cmd == 'register':
            if len(users)==0 or this_username not in users:
                users[this_username] = password
                save_users(users)
                send_data(conn, {cmd:"success"})
                print(f"用户[{this_username}]完成注册")
            elif this_username in users:
                send_data(conn, {cmd:"existed"})
                print(f"用户[{this_username}]重名")
    except Exception as e:
        print(f"验证出错: {e}")
        conn.close()
        print(f"关闭socket")
        return False,this_username

    if authenticated:
        if this_username in conn_users:
            send_data(conn, {cmd:"fail_online"})
            conn.close()
            print(f"用户[{this_username}]在线，不允许重复登录")
            return False,this_username
        else:
            # 向客户端发送在线用户列表
            send_data(conn, {cmd:"success","users_online":conn_users})
            print(f"本用户[{this_username}]已成功验证登录")
            # 转发
            for item in conn_users:
                send_data(conn_so[item],{"cmd":"online","user":this_username})
            # 进入聊天阶段
            conn_users.append(this_username)
            conn_ad[this_username] = ad
            conn_so[this_username] = conn
            print(f"当前在线用户[{conn_users}]")
            return True,this_username
    else:
        conn.close()
        print(f"已关闭socket")
        return False,this_username

def tcp_task(conn, ad):
    # 登录验证阶段
    is_passed, this_username = validate_logon(conn, ad)
    if not is_passed:
        return

    this_roomname = None
    try:
        while True:
            data = recv_data(conn)
            if not data:
                break

            cmd = data.get("cmd")
            print(f"收到指令: {cmd}")
            # 上线
            if cmd == "online":
                user1 = data.get("user")
                # 接收
                send_data(conn, {"cmd":cmd, "user":user1,"users_online": conn_users})
            # 下线
            elif cmd == "offline":
                user1 = data.get("user")
                if user1 == this_username:
                    print(f"本用户{user1} has been offline!")
                    # 转发
                    conn_users.remove(this_username)
                    conn_ad.pop(this_username)
                    conn_so.pop(this_username)
                    for item in conn_users:
                        send_data(conn_so[item], {
                            "cmd": cmd,
                            "user":user1,
                            "users_online": conn_users}) # 建议顺便把更新后的列表发过去
                    print(f"当前在线用户：{conn_users}")
                    break
                else:
                    # 接收
                    send_data(conn, {"cmd": cmd, "user": user1, "users_online": conn_users})
            # 1. 聊天
            elif cmd == "chat":
                user_sender = data.get("user")
                msg = data["msg"]
                if user_sender == this_username:
                    # 确认
                    send_data(conn, {"cmd": cmd, "user":user_sender, "msg":msg})
                    # 转发
                    for item in conn_users:
                        if item != this_username:
                            send_data(conn_so[item],{"cmd":cmd, "user":user_sender, "msg":msg})
                    print(f'已转发本用户[{user_sender}]的消息[{msg}]')
                else:
                    # 接收
                    send_data(conn, {"cmd":cmd, "user": user_sender, "msg":msg})
            # 2. 创建房间
            elif cmd == "create_room":
                room_name = data["room"]
                user_name = data.get("user")
                with lock:
                    if user_name == this_username:
                        if room_name not in rooms:
                            # 创建
                            rooms[room_name] = {
                                "host": data["host"],
                                "drawer": data["drawer"],
                                "word": "",
                                "players": data["players"]
                            }
                            # 确认
                            send_data(conn, {"cmd":cmd, "user": user_name, "state":"success", "room":room_name})
                            # 转发
                            for item in conn_users:
                                if item != user_name:
                                    send_data(conn_so[item], {"cmd": cmd, "user": user_name, "room": room_name})
                            this_roomname = room_name
                            print(f'本用户[{user_name}]创建的房间[{room_name}], {rooms}')
                        else:
                            # 确认
                            send_data(conn, {"cmd":cmd, "user": user_name, "state":"failure_existed", "room":room_name})
                            print(f"用户[{user_name}] 创建房间[{room_name}]失败：房间已存在")
                    else:
                        # 接收
                        send_data(conn, {"cmd": cmd, "user": user_name, "room": room_name})
            # 3. 加入房间
            elif cmd == "join_room":
                room_name = data["room"]
                user_name = data.get("user")
                with lock:
                    if user_name == this_username:
                        if room_name in rooms:
                            this_roomname = room_name
                            # 发本用户
                            send_data(conn, {
                                "cmd":cmd,
                                "user":this_username,
                                "room":room_name,  # 补上 room 字段
                                "state":"success",
                                "host":rooms[room_name]["host"],
                                "drawer":rooms[room_name]["drawer"],
                                "players":rooms[room_name]["players"]
                            })
                            # 转发其他用户
                            for item in rooms[room_name]["players"]:
                                send_data(conn_so[item], {"cmd":cmd,"user":this_username, "room":room_name})
                            rooms[room_name]["players"].append(this_username)
                            print(f"本用户[{this_username}]加入了房间[{room_name}], {rooms}")
                        else:
                            # 发本用户
                            send_data(conn, {"cmd":cmd, "user":this_username, "room":room_name,  "state":"failure_absent"})
                            print(f"本用户[{this_username}]未能加入房间[{room_name}]：房间不存在")
                    else:
                        # 发本用户
                        send_data(conn, {"cmd": cmd, "user": user_name, "room": room_name})
                        print(f"用户[{user_name}]加入房间[{room_name}]")
            # 5. 进入房间
            if this_roomname:
                if cmd == "guess":
                    player1 = data.get("player")
                    word1 = data.get("word")
                    reply = ""
                    answer = rooms[this_roomname]["word"]
                    if player1 == this_username:
                        if len(answer) == 0:
                            # 确认
                            send_data(conn, {"cmd": cmd, "player":player1, "reply": reply})
                            print(f"绘画人[{player1}]未设置答案！")
                        else:
                            if word1 == answer:
                                reply = "true"
                            else:
                                reply = "false"
                            # 确认
                            send_data(conn, {"cmd": cmd, "player":player1, "reply": reply})
                            # 转发
                            for item in rooms[this_roomname]["players"]:
                                if item != player1:
                                    send_data(conn_so[item], {
                                        "cmd": cmd,
                                        "player": this_username,
                                        "reply": reply
                                    })
                            print(f"玩家[{player1}]的回答判断为[{reply}]")
                    else:
                        # 接收
                        send_data(conn, {"cmd": cmd, "player":player1, "reply": reply})
                elif cmd == 'image':
                    player1 = data.get("player")
                    image1 = data.get("image")
                    if player1 == this_username:
                        # 确认
                        send_data(conn, {"cmd": cmd, "player": player1})
                        # 转发
                        if this_roomname and this_roomname in rooms:
                            for item in rooms[this_roomname]["players"]:
                                if item != player1:
                                    send_data(conn_so[item], {"cmd": cmd, "player": player1, "image": image1})
                            print(f'已转发来自玩家[{player1}] 的图片到房间[{this_roomname}]')
                    else:
                        # 接收
                        send_data(conn, {"cmd": cmd, "player": player1, "image": image1})
                elif cmd == "set_drawer":
                    player1 = data.get("player")
                    drawer1 = data["drawer"]
                    room1 = data["room"]
                    if player1 == this_username:
                        rooms[this_roomname]["drawer"] = drawer1
                        # 清除
                        rooms[this_roomname]["word"] = ""
                        # 确认
                        send_data(conn, {"cmd": cmd, "player": player1, "drawer":drawer1, "room": room1})
                        # 转发
                        for item in rooms[this_roomname]["players"]:
                            if item != this_username:
                                send_data(conn_so[item], {"cmd":cmd, "player": player1, "drawer":drawer1, "room":room1})
                        print(f"用户[{this_username}] 已设置用户[{drawer1}]为绘画人")
                    else:
                        # 接收
                        send_data(conn, {"cmd": cmd, "player": player1, "drawer": drawer1, "room": room1})
                elif cmd == "set_word":
                    player1 = data.get("player")
                    if player1 == this_username:
                        word1 = data["word"]
                        rooms[this_roomname]["word"] = word1
                        # 确认
                        send_data(conn, {"cmd":cmd, "player":player1, "word":word1})
                        # 转发
                        for item in rooms[this_roomname]["players"]:
                            if item != this_username:
                                send_data(conn_so[item], {"cmd": cmd, "player": player1})
                        print(f"用户[{player1}] 已设置答案为[{word1}]")
                    else:
                        # 接收
                        send_data(conn,{"cmd":cmd, "player":player1})
                elif cmd == "exit_room":
                    player1 = data.get("player")
                    rooms[this_roomname]["players"].remove(player1)
                    if player1 == this_username:
                        # 转发
                        if player1 == rooms[this_roomname]["host"]:
                            for item in rooms[this_roomname]["players"]:
                                send_data(conn_so[item], {
                                    "cmd":"delete_room", "host":player1, "room":this_roomname
                                })
                            rooms.pop(this_roomname)
                            print(f"发送出：房间{this_roomname} 已注销!")
                        else:
                            for item in rooms[this_roomname]["players"]:
                                send_data(conn_so[item], {
                                    "cmd":cmd, "player":player1, "room":this_roomname
                                })
                            print(f"发送出：本玩家[{player1}] has left!")
                        this_roomname = None
                    else:
                        # 接收
                        send_data(conn, {"cmd":cmd,"player":player1,"room":this_roomname})
                elif cmd == "delete_room":
                    host1 = data.get("host")
                    room1 = data.get("room")
                    # 接收
                    send_data(conn,{"cmd":cmd, "host":host1, "room":room1})
                    print(f"接收到：房主[{host1}]注销了房间[{room1}]")
    except Exception as e:
        print(f"用户[{this_username}]的线程因通信错误而退出: {e}")

    finally:
        # 断开连接清理
        with lock:
            if this_roomname in rooms:
                if this_username in rooms[this_roomname]["players"]:
                    rooms[this_roomname]["players"].remove(this_username)
                if this_username == rooms[this_roomname]["host"]:
                    for item in rooms[this_roomname]["players"]:
                        send_data(conn_so[item], {
                            "cmd": "delete_room", "host": this_username,"room":this_roomname })
                    rooms.pop(this_roomname)
                    print(f"无连接，房主[{this_username}]的房间[{this_roomname}] 已注销!")
                else:
                    for item in rooms[this_roomname]["players"]:
                        send_data(conn_so[item], {
                            "cmd":"exit_room", "player":this_username,"room":this_roomname })
            if this_username in conn_users:
                conn_users.remove(this_username)
                conn_ad.pop(this_username)
                conn_so.pop(this_username)
                # 向客户端发送在线用户列表
                for item in conn_users:
                    send_data(conn_so[item], {
                                "cmd": "offline",
                                "user": this_username })
        conn.close()
        print(f"本用户[{this_username}]退出, 其他在线用户[{conn_users}]")


def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(10)
    # print(f"服务端开始运行，请在客户端输入IP和端口（{HOST}，{PORT}），等待客户端连接...")
    print("=====服务端系统日志=====")

    while True:
        client_sock, client_add = s.accept()
        print(f"接收到一个用户请求，地址[{client_add}]")
        t = threading.Thread(target=tcp_task, args=(client_sock, client_add))
        t.start()
        print(f"已建立该用户的监听线程")

if __name__ == "__main__":
    start_server()