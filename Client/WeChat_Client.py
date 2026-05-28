import os
import socket
import threading
import pickle
import struct
import tkinter as tk
import tkinter.messagebox
from tkinter import scrolledtext
from tkinter.colorchooser import askcolor
import tkinter.filedialog
from tkinter import *
from PIL import Image, ImageTk, ImageGrab

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 客户端默认配置
SERVER_IP = '127.0.0.1'
SERVER_PORT = 80
BUFFER_SIZE = 4096
socket_user = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
users_online=[]
this_user= ''
flag = 0

class Application(Frame):

    def __init__(self, master):
        """初始化方法"""
        super().__init__(master)  # 调用父类的初始化方法
        self.x = 0
        self.y = 0
        self.fgcolor = 'yellow'
        self.lastdraw = 0
        self.start_flag = False
        self.master = master
        self.pack()
        self.createWidget()

    def createWidget(self):
        """创建画图区域"""
        self.drawpad = Canvas(self, width=600, height=400, bg='#000000')
        self.drawpad.pack()
        # 创建按钮
        self.btn_start = Button(self, name='start', text='开始')
        self.btn_start.pack(side='left', padx=10)
        self.btn_pen = Button(self, name='pen', text='画笔')
        self.btn_pen.pack(side='left', padx=10)
        self.btn_rect = Button(self, name='rect', text='矩形')
        self.btn_rect.pack(side='left', padx=10)
        self.btn_clear = Button(self, name='clear', text='清屏')
        self.btn_clear.pack(side='left', padx=10)
        self.btn_erasor = Button(self, name='erasor', text='橡皮擦')
        self.btn_erasor.pack(side='left', padx=10)
        self.btn_line = Button(self, name='line', text='直线')
        self.btn_line.pack(side='left', padx=10)
        self.btn_line_arrow = Button(self, name='line_arrow', text='箭头直线')
        self.btn_line_arrow.pack(side='left', padx=10)
        self.btn_color = Button(self, name='color', text='颜色')
        self.btn_color.pack(side='left', padx=10)
        self.btn_save = Button(self, name='save', text='保存')
        self.btn_save.pack(side='left', padx=10)
        self.btn_open = Button(self, name='oped', text='打开')
        self.btn_open.pack(side='left', padx=10)
        # 绑定事件
        self.btn_line.bind('<Button-1>', self.eventManager)  # 点击按钮事件
        self.btn_line_arrow.bind('<Button-1>', self.eventManager)  # 点击按钮事件
        self.btn_rect.bind('<Button-1>', self.eventManager)  # 点击按钮事件
        self.btn_pen.bind('<Button-1>', self.eventManager)  # 点击按钮事件
        self.btn_erasor.bind('<Button-1>', self.eventManager)  # 点击按钮事件
        self.btn_clear.bind('<Button-1>', self.eventManager)  # 点击按钮事件
        self.btn_color.bind('<Button-1>', self.eventManager)  # 点击按钮事件
        self.btn_save.bind('<Button-1>', self.save)  # 点击按钮事件
        self.btn_open.bind('<Button-1>', self.Open)  # 点击按钮事件
        self.master.bind('<KeyPress-r>', self.hotKey)  # 绑定快捷键
        self.master.bind('<KeyPress-g>', self.hotKey)  # 绑定快捷键
        self.master.bind('<KeyPress-b>', self.hotKey)  # 绑定快捷键
        self.master.bind('<KeyPress-y>', self.hotKey)  # 绑定快捷键
        self.drawpad.bind('<ButtonRelease-1>', self.stopDraw)  # 左键释放按钮

    def eventManager(self, event):
        name = event.widget.winfo_name()
        print(name)
        self.start_flag = True
        if name == 'line':
            # 左键拖动
            self.drawpad.bind('<B1-Motion>', self.myline)
        elif name == 'line_arrow':
            self.drawpad.bind('<B1-Motion>', self.myline_arrow)
        elif name == 'rect':
            self.drawpad.bind('<B1-Motion>', self.myrect)
        elif name == 'pen':
            self.drawpad.bind('<B1-Motion>', self.mypen)
        elif name == 'erasor':
            self.drawpad.bind('<B1-Motion>', self.myerasor)
        elif name == 'clear':
            self.drawpad.delete('all')
        elif name == 'color':
            c = askcolor(color=self.fgcolor, title='请选择颜色')
            print(c)  # c的值 ((128.5, 255.99609375, 0.0), '#80ff00')
            self.fgcolor = c[1]
        elif name == 'save':
            self.drawpad.bind('<B1-Motion>', self.save)

    def startDraw(self, event):
        self.drawpad.delete(self.lastdraw)
        if self.start_flag:
            self.start_flag = False
            self.x = event.x
            self.y = event.y

    def stopDraw(self, event):
        self.start_flag = True
        self.lastdraw = 0

    def myline(self, event):
        self.startDraw(event)
        self.lastdraw = self.drawpad.create_line(self.x, self.y, event.x, event.y, fill=self.fgcolor)

    def myline_arrow(self, event):
        self.startDraw(event)
        self.lastdraw = self.drawpad.create_line(self.x, self.y, event.x, event.y, arrow=LAST, fill=self.fgcolor)

    def myrect(self, event):
        self.startDraw(event)
        self.lastdraw = self.drawpad.create_rectangle(self.x, self.y, event.x, event.y, outline=self.fgcolor)

    def mypen(self, event):
        self.startDraw(event)
        print('self.x=', self.x, ',self.y=', self.y)
        self.drawpad.create_line(self.x, self.y, event.x, event.y, fill=self.fgcolor)
        self.x = event.x
        self.y = event.y

    def myerasor(self, event):
        self.startDraw(event)
        print('self.x=', self.x, ',self.y=', self.y)
        self.drawpad.create_rectangle(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill='#000000')
        self.x = event.x
        self.y = event.y

    def save(self, event):  # 参数是画布的实体
        # 使用 winfo_rootx 和 winfo_rooty 获取画布在屏幕上的绝对精确坐标
        # 这可以避开窗口边框和标题栏带来的偏移问题
        self.master.update()
        x = self.drawpad.winfo_rootx()
        y = self.drawpad.winfo_rooty()
        x1 = x + self.drawpad.winfo_width()
        y1 = y + self.drawpad.winfo_height()
        
        # 截取屏幕指定区域并保存
        try:
            img = ImageGrab.grab(bbox=(x, y, x1, y1))
            img.save('sent_pic.jpg')
            tk.messagebox.showinfo('提示', '图片保存成功')
            return
        except Exception as e:
            tk.messagebox.showerror('错误', f'图片保存失败: {e}')

    def Open(self, event):
        filename = tkinter.filedialog.askopenfilename(title='导入图片',
                                                      filetypes=[('image', '*.jpg *.png *.gif')])
        if filename:
            global image

            image = Image.open(filename)
            image = image.resize((600, 400))
            image = ImageTk.PhotoImage(image)
            self.drawpad.create_image(300, 200, image=image)

    def hotKey(self, event):
        c = event.char
        if c == 'r':
            self.fgcolor = 'red'
        elif c == 'g':
            self.fgcolor = 'green'
        elif c == 'b':
            self.fgcolor = 'blue'
        elif c == 'y':
            self.fgcolor = 'yellow'

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

# 登录逻辑
def usr_log_in(event=None):
    usr_name = var_usr_name.get()
    usr_pwd = var_usr_pwd.get()
    ip = var_ip.get()
    port = int(var_port.get())

    if not usr_name or not usr_pwd:
        tk.messagebox.showinfo('提示', '用户名或密码为空')
    elif any(char.isspace() for char in usr_name):
        tk.messagebox.showinfo('提示', '用户名中不能使用空格、制表符、换行')
    else:
        try:
            socket_user.connect((ip, port))
            cmd = "login"
            # 发送登录指令
            send_data(socket_user,{"cmd":cmd, "username":usr_name, "password":usr_pwd })
            print('发送完登录指令！')
            data = recv_data(socket_user)
            print(f'接收到：{data}')
            state = data[cmd]

            if state == 'success':
                global flag, this_user, users_online

                print(f'在线用户数量={len(data["users_online"])}!')
                flag = 1
                this_user = usr_name
                users_online = data["users_online"]
                users_online.append(usr_name)

                tk.messagebox.showinfo('成功', f'欢迎，{usr_name}')
                window_log_in.destroy()
            else:
                socket_user.close()
                # 重新创建 socket 以备下次尝试
                globals()['socket_user'] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if state == 'fail_null':
                    tk.messagebox.showinfo('失败', '用户名不存在，请注册')
                elif state == 'fail_error':
                    tk.messagebox.showinfo('失败', '密码错误')
                elif state == 'fail_online':
                    tk.messagebox.showinfo('失败', '该用户已在线，请勿重复登录')
        except Exception as e:
            tk.messagebox.showerror('错误', f'连接服务器失败，请核对服务器IP和POST')
            print(f'连接服务器失败: {e}')

# 注册逻辑
def usr_sign_up():
    def signtowcg():
        usr_name = new_name.get()
        usr_pwd = new_pwd.get()
        usr_pwdf = new_pwd_confirm.get()

        if not usr_name or not usr_pwd:
            tk.messagebox.showinfo('提示', '用户名或密码为空')
        elif any(char.isspace() for char in usr_name):
            tk.messagebox.showerror('错误', '用户名中不能使用空格、制表符、换行')
        elif usr_pwd != usr_pwdf:
            tk.messagebox.showinfo('提示', '密码前后不一致')
        else:
            ip = var_ip.get()
            port = int(var_port.get())
            try:
                temp_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_s.connect((ip, port))
                cmd = "register"
                send_data(temp_s,{"cmd":cmd, "username":usr_name, "password":usr_pwd })
                print('发送完注册指令！')
                data = recv_data(temp_s)
                print(f'接收到：{data}')
                res = data[cmd]
                if res == 'successful':
                    tk.messagebox.showinfo('成功', '注册成功，请登录')
                elif res == 'existed':
                    tk.messagebox.showinfo('提示', '用户名已存在')
                temp_s.close()
            except Exception as e:
                tk.messagebox.showerror('错误', f'连接服务器失败: {e}')
        window_sign_up.destroy()

    window_sign_up = tk.Toplevel()
    window_sign_up.geometry('350x250+550+250')
    window_sign_up.title('注册')
    
    new_name = tk.StringVar()
    tk.Label(window_sign_up, text='用户名：').place(x=10, y=10)
    tk.Entry(window_sign_up, textvariable=new_name).place(x=150, y=10)
    
    new_pwd = tk.StringVar()
    tk.Label(window_sign_up, text='请输入密码：').place(x=10, y=50)
    tk.Entry(window_sign_up, textvariable=new_pwd, show='*').place(x=150, y=50)
    
    new_pwd_confirm = tk.StringVar()
    tk.Label(window_sign_up, text='请再次输入密码：').place(x=10, y=90)
    tk.Entry(window_sign_up, textvariable=new_pwd_confirm, show='*').place(x=150, y=90)
    
    tk.Button(window_sign_up, text='确认注册', command=signtowcg).place(x=150, y=140)


# 登录界面
window_log_in = tk.Tk()
window_log_in.title('你画我猜 - 登录')
window_log_in.configure(bg='wheat')
width = 450
height = 350
window_log_in.geometry(f'{width}x{height}+500+200')
window_log_in.resizable(width=False, height=False)
# 画布放置图片
canvas = tk.Canvas(window_log_in, width=width, height=height, highlightthickness=0)
bg_path = os.path.join(BASE_DIR, 'background.png')
imagefile = tk.PhotoImage(file=bg_path)
canvas.image = imagefile  # 保持引用，防止垃圾回收
image = canvas.create_image(0, 0, anchor='nw', image=imagefile)
canvas.pack(side='top')
height_interval = 0.12*height
height_start = 0.15*height
width_interval = 0.2*width
width_start = 0.25*width
tk.Label(window_log_in, text='服务器IP:').place(x=width_start, y=height_start)
var_ip = tk.StringVar(value=SERVER_IP)
tk.Entry(window_log_in, textvariable=var_ip).place(x=width_start+width_interval, y=height_start)

tk.Label(window_log_in, text='端口POST:').place(x=width_start, y=height_start+height_interval)
var_port = tk.StringVar(value=f'{SERVER_PORT}')
tk.Entry(window_log_in, textvariable=var_port).place(x=width_start+width_interval, y=height_start+height_interval)

tk.Label(window_log_in, text='用户名:').place(x=width_start, y=height_start+2*height_interval)
var_usr_name = tk.StringVar()
tk.Entry(window_log_in, textvariable=var_usr_name).place(x=width_start+width_interval, y=height_start+2*height_interval)

tk.Label(window_log_in, text='密码:').place(x=width_start, y=height_start+3*height_interval)
var_usr_pwd = tk.StringVar()
tk.Entry(window_log_in, textvariable=var_usr_pwd, show='*').place(x=width_start+width_interval, y=height_start+3*height_interval)

tk.Button(window_log_in, text='登录', command=usr_log_in).place(x=1.1*width_start, y=1.2*height_start+4*height_interval)
tk.Button(window_log_in, text='注册', command=usr_sign_up).place(x=1.1*width_start+width_interval, y=1.2*height_start+4*height_interval)
tk.Button(window_log_in, text='退出', command=window_log_in.destroy).place(x=1.1*width_start+2*width_interval, y=1.2*height_start+4*height_interval)

window_log_in.bind('<Return>', usr_log_in)
window_log_in.mainloop()

this_roomname = None
host = ""
drawer = ""
word = ""
players = []
if flag:
    try:
        def safe_update(widget, action, *args, **kwargs):
            """安全地更新处于 DISABLED 状态的 Tkinter 控件"""
            widget.config(state=tk.NORMAL)
            if action == "insert":
                widget.insert(*args, **kwargs)
            elif action == "delete":
                widget.delete(*args, **kwargs)
            widget.config(state=tk.DISABLED)
            if action == "insert":
                widget.see(tk.END)

        def send_text(event=None):
            msg = textbox_chat.get()
            if msg:
                cmd = "chat"
                send_data(socket_user,{"cmd":cmd,"user":this_user,"msg":msg})
                print(f'{this_user}[我]发送消息：{msg}')
            else:
                tk.messagebox.showinfo('提示', '请先输入文本')

        def create_room():
            room_name = text_room_name.get()
            if not room_name:
                tk.messagebox.showerror('错误', '房间名为空')
            elif any(char.isspace() for char in room_name):
                tk.messagebox.showerror('错误', '房间名中不能使用空格、制表符、换行')
            else:
                cmd = "create_room"
                send_data(socket_user,{"cmd":cmd,"user":this_user,"room":room_name,"host": this_user,
                            "drawer": this_user,"players": [this_user]})

        def join_room():
            room_name = text_room_name.get()
            if not room_name:
                tk.messagebox.showerror('错误', '房间名为空')
            elif any(char.isspace() for char in room_name):
                tk.messagebox.showerror('错误', '房间名中不能使用空格、制表符、换行')
            else:
                cmd = "join_room"
                send_data(socket_user,{"cmd":cmd,"user":this_user,"room":room_name})

        def guess_word():
            word1 = text_guess.get()
            if word1:
                word1=word1.strip()
                cmd = "guess"
                send_data(socket_user, {"cmd":cmd, "player":this_user, "word":word1})
            else:
                tk.messagebox.showerror('错误', '内容为空')

        def send_image():
            if os.path.exists('sent_pic.jpg'):
                with open('sent_pic.jpg', 'rb') as f:
                    picBytes = f.read()
                cmd = "image"
                send_data(socket_user, {"cmd": cmd, "player": this_user, "image": picBytes})
            else:
                tk.messagebox.showinfo('提示', '请先您先进行绘图并保存')

        def set_drawer():
            global host, players
            if this_user == host:
                drawer1 = text_drawer.get()
                if drawer1:
                    drawer1 = drawer1.strip()
                    if any(char.isspace() for char in drawer1):
                        tk.messagebox.showinfo('提示', '内容中不能使用空格、制表符、换行')
                    else:
                        if drawer1 == drawer:
                            tk.messagebox.showinfo('提示', f"{drawer1}已是绘画人")
                        else:
                            if drawer1 in players:
                                cmd = "set_drawer"
                                send_data(socket_user,{"cmd":cmd,"player":this_user,"drawer":drawer1,"room":this_roomname})
                            else:
                                tk.messagebox.showinfo('提示', f'当前不存在玩家[{drawer1}]')
                else:
                    tk.messagebox.showinfo('提示', '内容为空')
            else:
                tk.messagebox.showinfo('提示', '仅由房主指定绘画人')

        def set_word():
            global drawer
            if this_user == drawer:
                word1 = text_word.get()
                if word1:
                    if any(char.isspace() for char in word1):
                        tk.messagebox.showerror('错误', '内容中不能使用空格、制表符、换行')
                    else:
                        cmd = "set_word"
                        send_data(socket_user,{"cmd":cmd, "player":this_user, "word":word1})
                else:
                    tk.messagebox.showerror('错误', '内容为空')
            else:
                tk.messagebox.showerror('错误', '仅由绘画人设置答案')

        def exit_room():
            global this_roomname, host, drawer, word, players
            cmd = "exit_room"
            send_data(socket_user,{"cmd":cmd,"player":this_user,"room":this_roomname})
            # 清空图片

            # 清空消息
            safe_update(st_room_user_online, "delete", 1.0, tk.END)
            safe_update(msgbox_room, "delete", 1.0, tk.END)
            this_roomname = None
            host = ""
            drawer = ""
            word = ""
            players = []
            window_chat.after(0, refresh_ui)
            print(f"本用户退出了房间")

        def read_server(sock):
            print("进入接收监听线程")
            global this_roomname, host, drawer, word, players
            try:
                while True:
                    data = recv_data(socket_user)
                    if not data:
                        print("无数据，线程退出")
                        break # 断开连接则退出

                    cmd = data.get("cmd")
                    if not cmd: continue
                    print(f"收到指令: {cmd}")

                    # --- 1. 处理通用指令 ---
                    if cmd == "offline":
                        user1 = data.get("user")
                        if user1 in users_online:
                            users_online.remove(user1)
                        if not this_roomname:
                            safe_update(msgbox_hall, "insert", tk.END, f"系统：{user1} 下线了\n")
                            # 更新大厅的在线用户
                            safe_update(st_hall_user_online, "delete", 1.0, tk.END)
                            safe_update(st_hall_user_online, "insert", tk.END, f"{this_user}[我]\n")
                            for item in users_online:
                                if item != this_user:
                                    safe_update(st_hall_user_online, "insert", tk.END, f"{item}\n")
                        print(f"接收到：用户{user1} 下线了")
                        print(f"当前在线用户：{data.get("users_online","不存在")}")
                    elif cmd == "online":
                        user1 = data.get("user")
                        if user1 not in users_online:
                            users_online.append(user1)
                        if not this_roomname:
                            safe_update(msgbox_hall, "insert", tk.END, f"系统：{user1} 上线了\n")
                            # 更新大厅的在线用户
                            safe_update(st_hall_user_online, "delete", 1.0, tk.END)
                            safe_update(st_hall_user_online, "insert", tk.END, f"{this_user}[我]\n")
                            for item in users_online:
                                if item != this_user:
                                    safe_update(st_hall_user_online, "insert", tk.END, f"{item}\n")
                        print(f"接收到：用户{user1} 上线了")
                        print(f"当前在线用户：{data.get("users_online","不存在")}")
                    elif cmd == "join_room":
                        user1 = data.get("user")
                        room1 = data.get("room")
                        if user1 == this_user:
                            state1 = data.get("state")
                            if state1 == "success":
                                this_roomname = room1
                                host = data.get("host")
                                drawer = data.get("drawer")
                                players = data.get("players")
                                players.append(user1)

                                # 切换至房间界面
                                window_chat.after(0, refresh_ui)
                                print(f"本用户{user1}已加入房间[{this_roomname}]")
                            else:
                                window_chat.after(0, lambda: tk.messagebox.showerror('错误', f'房间[{room1}]不存在'))
                                print(f"房间[{room1}]不存在")
                        else:
                            players.append(user1)
                            safe_update(msgbox_room, "insert", tk.END, f"系统：玩家[{user1}]加入了房间\n", "left")
                            # 更新房间的在线用户
                            safe_update(st_room_user_online, "delete", 1.0, tk.END)
                            for item in players:
                                if item == host:
                                    safe_update(st_room_user_online, "insert", tk.END, f"{item}[房主]\n")
                                else:
                                    safe_update(st_room_user_online, "insert", tk.END, f"{item}\n")
                            print(f"用户{user1}已加入房间[{room1}]")

                    # --- 2. 处理大厅/房间逻辑 ---
                    if not this_roomname:
                        if cmd == "chat":
                            user1 = data.get("user", "未知用户")
                            msg1 = data["msg"]
                            if user1 == this_user:
                                # 使用 "right" 标签直接插入内容，实现右对齐
                                safe_update(msgbox_hall, "insert", tk.END, f"{msg1} :{user1}\n", "right")
                                textbox_chat.set('') # 重置内容
                                print(f'本用户[{user1}]成功发送消息[{msg1}]')
                            else:
                                safe_update(msgbox_hall, "insert", tk.END, f"{user1}: {msg1}\n", "left")
                                print(f'已接受用户[{user1}]的消息[{msg1}]')
                        elif cmd == "create_room":
                            user1 = data.get("user", "未知用户")
                            room1 = data["room"]
                            if user1 == this_user:
                                state1 = data.get("state")
                                if state1 == "success":
                                    this_roomname = room1
                                    host = this_user
                                    drawer = this_user
                                    players = [this_user]
                                    # 切换至房间界面
                                    window_chat.after(0, refresh_ui)
                                    print(f"房间[{room1}]创建成功")
                                else:
                                    window_chat.after(0, lambda: tk.messagebox.showerror('错误', '该房间名已存在'))
                                    print(f"房间[{room1}]创建失败")
                            else:
                                safe_update(msgbox_hall, "insert", tk.END, f"系统：用户[{user1}]创建了房间[{room1}]\n", "left")
                    else:
                        if cmd == "guess":
                            player1 = data.get("player", "未知用户")
                            reply = data["reply"]
                            if len(reply) == 0:
                                window_chat.after(0, lambda: tk.messagebox.showinfo('提示', '绘画人未设置答案'))
                            else:
                                reply_text = "正确！" if reply == "true" else "错误"
                                if player1 == this_user:
                                    if player1 == drawer:
                                        safe_update(msgbox_room, "insert", tk.END, f"系统：绘画人[{player1}]回答{reply_text}\n", "right")
                                    else:
                                        safe_update(msgbox_room, "insert", tk.END,
                                                    f"系统：玩家[{player1}]回答{reply_text}\n", "right")
                                    print(f'本用户[{player1}]回答[{reply_text}]')
                                else:
                                    safe_update(msgbox_room, "insert", tk.END, f"系统：玩家[{player1}]回答{reply_text}\n", "left")
                                    print(f'用户[{player1}]回答[{reply_text}]')
                        elif cmd == 'image':
                            player1 = data.get("player", "未知用户")
                            if player1 == this_user:
                                safe_update(msgbox_room, "insert", tk.END, f"系统：图片已发送！\n", "right")
                                # 打印调试信息
                                print(f"服务端确认：图片已发送成功")
                            else:
                                picBytes = data.get("image")
                                if picBytes:
                                    with open('received_pic.jpg', 'wb') as f:
                                        f.write(picBytes)
                                    safe_update(msgbox_room, "insert", tk.END, f"系统：收到绘画人[{player1}]的图片，点击“展示图片”查看！\n", "left")
                                    print(f"已接收并保存来自[{player1}]的图片")
                        elif cmd == "set_drawer":
                            player1 = data.get("player")
                            drawer1 = data.get("drawer")
                            label_drawer.config(text=f"绘画人：{drawer1}")
                            if player1 == this_user:
                                if drawer1 == this_user:
                                    window_chat.after(0, lambda: tk.messagebox.showinfo('提示',
                                                                                        f"您指定了自己为绘画人"))
                                else:
                                    window_chat.after(0, lambda: tk.messagebox.showinfo('提示',
                                                                                        f"您已不是绘画人"))
                                drawer = drawer1
                                window_chat.after(0, refresh_ui) # 更新为绘画人界面
                            else:
                                if drawer1 == this_user:
                                    window_chat.after(0, lambda: tk.messagebox.showinfo('提示',
                                                                                        f"您被房主指定为绘画人"))
                                else:
                                    if drawer == this_user:
                                        window_chat.after(0, lambda: tk.messagebox.showinfo('提示',
                                                                                            f"您已不是绘画人"))
                                if drawer != this_user and drawer1 != this_user:
                                    safe_update(msgbox_room, "insert", tk.END, f"系统: 玩家[{drawer1}]被房主指定为绘画人\n", "left")
                                    drawer = drawer1
                                else:
                                    drawer = drawer1
                                    window_chat.after(0, refresh_ui)  # 更新为绘画人界面
                            print(f"玩家[{drawer}]已被设置为绘画人")
                        elif cmd == "set_word":
                            player1 = data.get("player")
                            if player1 == this_user:
                                word1 = data.get("word")
                                safe_update(msgbox_room, "insert", tk.END, f"系统：答案[{word1}]设置成功\n", "right")
                                print(f"答案已被重置为[{word1}]")
                            else:
                                safe_update(msgbox_room, "insert", tk.END, f"系统：绘画人[{player1}]设置了答案\n", "left")
                                print(f"答案已被重置")
                        elif cmd == "exit_room":
                            player_exit = data["player"]
                            room1 = data.get("room")
                            if player_exit in players:
                                players.remove(player_exit)
                            # 更新房间的在线用户
                            safe_update(st_room_user_online, "delete", 1.0, tk.END)
                            for item in players:
                                tag = "[房主]" if item == host else ""
                                safe_update(st_room_user_online, "insert", tk.END, f"{item}{tag}\n")
                            safe_update(msgbox_room, "insert", tk.END, f"系统：玩家[{player_exit}]退出了房间\n")
                            print(f"玩家[{player_exit}]退出了房间[{room1}]")
                        elif cmd == "delete_room":
                            host1 = data["host"]
                            room1 = data["room"]
                            window_chat.after(0, lambda: tk.messagebox.showinfo('提示', f"房主[{host1}]注销了房间[{room1}]"))
                            # 清空图片

                            # 清空消息
                            safe_update(st_room_user_online, "delete", 1.0, tk.END)
                            safe_update(msgbox_room, "delete", 1.0, tk.END)
                            this_roomname = None
                            host = ""
                            drawer = ""
                            word = ""
                            players = []
                            window_chat.after(0, refresh_ui)
                            print(f"房主[{host1}]注销了房间[{room1}]")
            except Exception as e:
                import traceback
                print(f"接收监听线程异常退出: {e}")
                traceback.print_exc()

        def display_image():
            if this_user == drawer:
                if os.path.exists('sent_pic.jpg'):
                    img = Image.open('sent_pic.jpg')
                    img.show()
                else:
                    tk.messagebox.showinfo('提示', '请先您先进行绘图并保存')
            else:
                if os.path.exists('received_pic.jpg'):
                    img = Image.open('received_pic.jpg')
                    img.show()
                else:
                    tk.messagebox.showinfo('提示', '暂未收到绘画人的图片')

        def game():
            tk.messagebox.showinfo(message='请准备做画！')
            '''
            1.创建出游戏界面
            2.游戏界面执行保存
            '''
            root = tk.Toplevel()
            root.title('绘图窗口')
            Application(master=root)

        window_chat = tk.Tk()
        # 不允许改变窗口大小
        window_chat.resizable(False, False)

        def refresh_ui():
            """根据当前状态刷新界面"""
            # 清空当前窗口所有组件
            for widget in window_chat.winfo_children():
                widget.destroy()

            window_chat.title(f'你画我猜 - 用户[{this_user}]')
            width = 550
            height = 400
            height_start = 0.05 * height
            width_start = 0.05 * width

            window_chat.geometry(f'{width}x{height}+500+200')
            window_chat.configure(bg='wheat')
            
            # 画布放置背景图
            canvas = tk.Canvas(window_chat, width=width, height=height, highlightthickness=0)
            bg_path = os.path.join(BASE_DIR, 'background.png')
            imagefile = tk.PhotoImage(file=bg_path)
            canvas.image = imagefile 
            canvas.create_image(width, 0, anchor='ne', image=imagefile)
            canvas.pack(side='top')

            global msgbox_hall, textbox_chat, st_hall_user_online, text_room_name
            global msgbox_room, text_guess, st_room_user_online, text_drawer, text_word, label_drawer

            if not this_roomname:
                # 大厅界面逻辑...
                width_box = 340
                tk.Label(window_chat, text="大厅消息框", font=("宋体", 12)).place(x=width_start, y=height_start,
                                                                                  width=width_box, height=20)
                msgbox_hall = scrolledtext.ScrolledText(window_chat, font=("宋体", 10))
                msgbox_hall.place(x=width_start, y=height_start + 20, width=width_box, height=300)
                msgbox_hall.tag_configure("right", justify='right')
                msgbox_hall.tag_configure("left", justify='left')
                msgbox_hall.config(state=tk.DISABLED)

                height_box=360
                textbox_chat = tk.StringVar()
                tk.Entry(window_chat, textvariable=textbox_chat).place(x=width_start, y=height_box, width=280, height=25)
                tk.Button(window_chat, text='发送', command=send_text).place(x=width_start+280, y=height_box, width=60, height=25)

                width_text = 0.7*width
                tk.Label(window_chat, text="大厅在线用户", font=("宋体", 10)).place(x=width_text, y=height_start, width=100, height=20)
                st_hall_user_online = scrolledtext.ScrolledText(window_chat, font=("宋体", 10))
                st_hall_user_online.place(x=width_text, y=height_start + 20, width=100, height=0.4 * height)
                st_hall_user_online.config(state=tk.DISABLED)
                for item in users_online:
                    if item == this_user:
                        safe_update(st_hall_user_online, "insert", tk.END, f"{item}[我]\n")
                    else:
                        safe_update(st_hall_user_online, "insert", tk.END, f"{item}\n")
        
                height_button = 220
                tk.Label(window_chat, text="房间名：", font=("宋体", 10)).place(x=width_text, y=height_button, width=60, height=20)
                text_room_name = tk.StringVar()
                tk.Entry(window_chat, textvariable=text_room_name).place(x=width_text+60, y=height_button, width=80, height=20)
                tk.Button(window_chat, text='创建房间', command=create_room).place(x=width_text, y=height_button + 20, width=60)
                tk.Button(window_chat, text='加入房间', command=join_room).place(x=width_text+60, y=height_button + 20, width=60)
            else:
                # 房间界面逻辑...
                width_box = 340
                tk.Label(window_chat, text=f"房间[{this_roomname}]消息框", font=("宋体", 12)).place(x=width_start, y=height_start, width=width_box, height=20)
                msgbox_room = scrolledtext.ScrolledText(window_chat, font=("宋体", 10))
                msgbox_room.place(x=width_start, y=height_start + 20, width=width_box, height=300)
                msgbox_room.tag_configure("right", justify='right')
                msgbox_room.tag_configure("left", justify='left')
                msgbox_room.config(state=tk.DISABLED)

                height_box=360
                width_box=width_start
                tk.Button(window_chat, text='展示图片', command=display_image).place(x=width_box, y=height_box, width=80, height=25)
                width_box=width_start+100
                text_guess = tk.StringVar()
                tk.Entry(window_chat, textvariable=text_guess).place(x=width_box, y=height_box, width=80, height=25)
                tk.Button(window_chat, text='猜词', command=guess_word).place(x=width_box+80, y=height_box, width=60, height=25)

                width_text = 0.7 * width
                tk.Label(window_chat, text="房间在线用户", font=("宋体", 10)).place(x=width_text, y=height_start, width=100, height=20)
                st_room_user_online = scrolledtext.ScrolledText(window_chat, font=("宋体", 10))
                st_room_user_online.place(x=width_text, y=height_start + 20, width=100, height=150)
                st_room_user_online.config(state=tk.DISABLED)
                for item in players:
                    if item == host:
                        safe_update(st_room_user_online, "insert", tk.END, f"{item}[房主]\n")
                    else:
                        safe_update(st_room_user_online, "insert", tk.END, f"{item}\n")


                height_button = 200
                tk.Label(window_chat, text=f"房主：{host}", font=("宋体", 10)).place(x=width_text, y=height_button, width=100, height=20)
                label_drawer = tk.Label(window_chat, text=f"绘画人：{drawer}", font=("宋体", 10))
                label_drawer.place(x=width_text, y=height_button+20, width=100, height=20)

                if this_user == host:
                    height_button = 250
                    text_drawer = tk.StringVar()
                    tk.Entry(window_chat, textvariable=text_drawer).place(x=width_text, y=height_button, width=80, height=20)
                    tk.Button(window_chat, text='设定绘画人', command=set_drawer).place(x=width_text+80, y=height_button, width=80, height=20)
                if this_user == drawer:
                    height_button = 270
                    text_word = tk.StringVar()
                    tk.Entry(window_chat, textvariable=text_word).place(x=width_text, y=height_button, width=80, height=20)
                    tk.Button(window_chat, text='设定词语', command=set_word).place(x=width_text+80, y=height_button, width=80, height=20)
                    height_button = 300
                    tk.Button(window_chat, text='进行绘图', command=game).place(x=width_text, y=height_button, width=80, height=25)
                    tk.Button(window_chat, text='发送图片', command=send_image).place(x=width_text + 80, y=height_button, width=80, height=25)
                height_button=360
                tk.Button(window_chat, text='退出房间', command=exit_room).place(x=width_text, y=height_button, width=80, height=25)
        # 初始加载大厅界面
        refresh_ui()

        threading.Thread(target=read_server, args=(socket_user,), daemon=True).start()
        # window_chat.bind('<Return>', send_text)
        window_chat.mainloop()
    except Exception as e:
        tk.messagebox.showerror('错误', f'连接服务器失败: {e}')
    finally:
        send_data(socket_user,{"cmd":"offline","user":this_user})
        socket_user.close()
