import os
import socket
import threading
import pickle
import struct
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, colorchooser
from PIL import Image, ImageTk, ImageGrab
from typing import Optional, Dict, List, Any, Callable

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SERVER_IP = '127.0.0.1'
DEFAULT_SERVER_PORT = 80
BUFFER_SIZE = 4096

class NetworkManager:
    """Handles all network communications with the server."""
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.is_connected = False

    def connect(self, ip: str, port: int) -> bool:
        """Establishes connection to the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, port))
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Closes the connection."""
        if self.socket:
            self.socket.close()
        self.is_connected = False
        self.socket = None

    def send_data(self, data: Dict[str, Any]):
        """Sends serialized data to the server, handling packet framing."""
        if not self.socket:
            return
        try:
            data_bytes = pickle.dumps(data)
            self.socket.sendall(struct.pack('i', len(data_bytes)) + data_bytes)
        except Exception as e:
            print(f"Send data error: {e}")

    def recv_data(self) -> Optional[Dict[str, Any]]:
        """Receives data from the server, handling packet framing."""
        if not self.socket:
            return None
        try:
            header = self.socket.recv(4)
            if not header:
                return None
            data_len = struct.unpack('i', header)[0]
            data = b''
            while len(data) < data_len:
                packet = self.socket.recv(min(data_len - len(data), BUFFER_SIZE))
                if not packet:
                    return None
                data += packet
            return pickle.loads(data)
        except Exception as e:
            print(f"Receive data error: {e}")
            return None

class DrawingBoard(tk.Toplevel):
    """The drawing canvas window."""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.title('绘图窗口')
        self.x = 0
        self.y = 0
        self.fg_color = 'yellow'
        self.last_draw = 0
        self.start_flag = False
        
        self.setup_ui()

    def setup_ui(self):
        """Creates and layouts the drawing UI widgets."""
        self.draw_pad = tk.Canvas(self, width=600, height=400, bg='#000000')
        self.draw_pad.pack()

        btn_frame = tk.Frame(self)
        btn_frame.pack(side='bottom', pady=10)

        buttons = [
            ('开始', 'start', None),
            ('画笔', 'pen', self.set_tool),
            ('矩形', 'rect', self.set_tool),
            ('清屏', 'clear', self.clear_canvas),
            ('橡皮擦', 'erasor', self.set_tool),
            ('直线', 'line', self.set_tool),
            ('箭头直线', 'line_arrow', self.set_tool),
            ('颜色', 'color', self.choose_color),
            ('保存', 'save', self.save_image),
            ('打开', 'open', self.open_image),
        ]

        for text, name, cmd in buttons:
            btn = tk.Button(btn_frame, text=text, name=name)
            btn.pack(side='left', padx=5)
            if cmd:
                btn.bind('<Button-1>', cmd)

        self.draw_pad.bind('<ButtonRelease-1>', self.stop_draw)
        self.bind('<KeyPress-r>', lambda e: self.set_color('red'))
        self.bind('<KeyPress-g>', lambda e: self.set_color('green'))
        self.bind('<KeyPress-b>', lambda e: self.set_color('blue'))
        self.bind('<KeyPress-y>', lambda e: self.set_color('yellow'))

    def set_tool(self, event):
        name = event.widget.winfo_name()
        self.start_flag = True
        if name == 'line':
            self.draw_pad.bind('<B1-Motion>', self.draw_line)
        elif name == 'line_arrow':
            self.draw_pad.bind('<B1-Motion>', self.draw_line_arrow)
        elif name == 'rect':
            self.draw_pad.bind('<B1-Motion>', self.draw_rect)
        elif name == 'pen':
            self.draw_pad.bind('<B1-Motion>', self.draw_pen)
        elif name == 'erasor':
            self.draw_pad.bind('<B1-Motion>', self.draw_erasor)

    def start_draw(self, event):
        if self.last_draw:
            self.draw_pad.delete(self.last_draw)
        if self.start_flag:
            self.start_flag = False
            self.x, self.y = event.x, event.y

    def stop_draw(self, event):
        self.start_flag = True
        self.last_draw = 0

    def draw_line(self, event):
        self.start_draw(event)
        self.last_draw = self.draw_pad.create_line(self.x, self.y, event.x, event.y, fill=self.fg_color)

    def draw_line_arrow(self, event):
        self.start_draw(event)
        self.last_draw = self.draw_pad.create_line(self.x, self.y, event.x, event.y, arrow=tk.LAST, fill=self.fg_color)

    def draw_rect(self, event):
        self.start_draw(event)
        self.last_draw = self.draw_pad.create_rectangle(self.x, self.y, event.x, event.y, outline=self.fg_color)

    def draw_pen(self, event):
        self.start_draw(event)
        self.draw_pad.create_line(self.x, self.y, event.x, event.y, fill=self.fg_color)
        self.x, self.y = event.x, event.y

    def draw_erasor(self, event):
        self.start_draw(event)
        self.draw_pad.create_rectangle(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill='#000000')
        self.x, self.y = event.x, event.y

    def clear_canvas(self, event):
        self.draw_pad.delete('all')

    def choose_color(self, event):
        color = colorchooser.askcolor(color=self.fg_color, title='请选择颜色')
        if color[1]:
            self.fg_color = color[1]

    def set_color(self, color):
        self.fg_color = color

    def save_image(self, event):
        self.update()
        x = self.draw_pad.winfo_rootx()
        y = self.draw_pad.winfo_rooty()
        x1 = x + self.draw_pad.winfo_width()
        y1 = y + self.draw_pad.winfo_height()
        
        try:
            img = ImageGrab.grab(bbox=(x, y, x1, y1))
            img.save('sent_pic.jpg')
            messagebox.showinfo('提示', '图片保存成功')
        except Exception as e:
            messagebox.showerror('错误', f'图片保存失败: {e}')

    def open_image(self, event):
        filename = filedialog.askopenfilename(title='导入图片', filetypes=[('image', '*.jpg *.png *.gif')])
        if filename:
            img = Image.open(filename).resize((600, 400))
            self.photo = ImageTk.PhotoImage(img) # Keep reference
            self.draw_pad.create_image(300, 200, image=self.photo)

class ChatApp:
    """The main chat application and UI manager."""
    
    def __init__(self):
        self.network = NetworkManager()
        self.root = tk.Tk()
        self.root.withdraw() # Hide root initially
        
        # User state
        self.username = ""
        self.this_room = None
        self.host = ""
        self.drawer = ""
        self.players = []
        self.users_online = []
        
        # UI references
        self.login_window = None
        self.main_window = None
        
        self.show_login()
        self.root.mainloop()

    def show_login(self):
        """Displays the login window."""
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title('你画我猜 - 登录')
        self.login_window.geometry('450x350+500+200')
        self.login_window.resizable(False, False)
        
        canvas = tk.Canvas(self.login_window, width=450, height=350, highlightthickness=0)
        bg_path = os.path.join(BASE_DIR, 'background.png')
        try:
            self.bg_img = tk.PhotoImage(file=bg_path)
            canvas.create_image(0, 0, anchor='nw', image=self.bg_img)
        except:
            print("Background image not found")
        canvas.pack()

        # Input variables
        self.var_ip = tk.StringVar(value=DEFAULT_SERVER_IP)
        self.var_port = tk.StringVar(value=str(DEFAULT_SERVER_PORT))
        self.var_user = tk.StringVar()
        self.var_pwd = tk.StringVar()

        # Layout
        fields = [
            ('服务器IP:', self.var_ip),
            ('端口:', self.var_port),
            ('用户名:', self.var_user),
            ('密码:', self.var_pwd, '*')
        ]

        y_pos = 50
        for field in fields:
            tk.Label(self.login_window, text=field[0]).place(x=100, y=y_pos)
            entry_args = {'textvariable': field[1]}
            if len(field) > 2:
                entry_args['show'] = field[2]
            tk.Entry(self.login_window, **entry_args).place(x=200, y=y_pos)
            y_pos += 40

        tk.Button(self.login_window, text='登录', command=self.handle_login).place(x=120, y=250)
        tk.Button(self.login_window, text='注册', command=self.show_register).place(x=200, y=250)
        tk.Button(self.login_window, text='退出', command=self.root.quit).place(x=280, y=250)
        
        self.login_window.bind('<Return>', lambda e: self.handle_login())
        self.login_window.protocol("WM_DELETE_WINDOW", self.root.quit)

    def show_register(self):
        """Displays the registration window."""
        reg_win = tk.Toplevel(self.login_window)
        reg_win.title('注册')
        reg_win.geometry('350x250+550+250')

        new_name = tk.StringVar()
        new_pwd = tk.StringVar()
        new_pwd_confirm = tk.StringVar()

        tk.Label(reg_win, text='用户名：').place(x=50, y=30)
        tk.Entry(reg_win, textvariable=new_name).place(x=150, y=30)
        tk.Label(reg_win, text='密码：').place(x=50, y=70)
        tk.Entry(reg_win, textvariable=new_pwd, show='*').place(x=150, y=70)
        tk.Label(reg_win, text='确认密码：').place(x=50, y=110)
        tk.Entry(reg_win, textvariable=new_pwd_confirm, show='*').place(x=150, y=110)

        def do_register():
            u, p, pc = new_name.get().strip(), new_pwd.get(), new_pwd_confirm.get()
            if not u or not p:
                messagebox.showinfo('提示', '用户名或密码为空')
                return
            if any(char.isspace() for char in u):
                messagebox.showerror('错误', '用户名不能包含空白字符')
                return
            if p != pc:
                messagebox.showinfo('提示', '密码不一致')
                return
            
            # Temporary connection for registration
            temp_net = NetworkManager()
            if temp_net.connect(self.var_ip.get(), int(self.var_port.get())):
                temp_net.send_data({"cmd": "register", "username": u, "password": p})
                res = temp_net.recv_data()
                if res and res.get('register') == 'successful':
                    messagebox.showinfo('成功', '注册成功')
                    reg_win.destroy()
                else:
                    messagebox.showinfo('提示', '注册失败或用户名已存在')
                temp_net.disconnect()
            else:
                messagebox.showerror('错误', '无法连接到服务器')

        tk.Button(reg_win, text='确认注册', command=do_register).place(x=150, y=160)

    def handle_login(self):
        """Handles the login process."""
        u, p = self.var_user.get().strip(), self.var_pwd.get()
        ip, port = self.var_ip.get(), int(self.var_port.get())

        if not u or not p:
            messagebox.showinfo('提示', '请输入用户名和密码')
            return

        if self.network.connect(ip, port):
            self.network.send_data({"cmd": "login", "username": u, "password": p})
            res = self.network.recv_data()
            if res and res.get('login') == 'success':
                self.username = u
                self.users_online = res.get('users_online', [])
                self.users_online.append(u)
                self.login_window.destroy()
                self.show_main_window()
                threading.Thread(target=self.listen_to_server, daemon=True).start()
            else:
                self.network.disconnect()
                state = res.get('login') if res else 'unknown'
                msg = {'fail_null': '用户不存在', 'fail_error': '密码错误', 'fail_online': '用户已在线'}.get(state, '登录失败')
                messagebox.showinfo('失败', msg)
        else:
            messagebox.showerror('错误', '连接服务器失败')

    def show_main_window(self):
        """Displays the main lobby/room window."""
        self.main_window = tk.Toplevel(self.root)
        self.main_window.title(f'你画我猜 - 用户[{self.username}]')
        self.main_window.geometry('550x400+500+200')
        self.main_window.resizable(False, False)
        self.main_window.configure(bg='wheat')
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_main_ui()

    def setup_main_ui(self):
        """Sets up the UI elements for lobby or room based on state."""
        for widget in self.main_window.winfo_children():
            widget.destroy()

        canvas = tk.Canvas(self.main_window, width=550, height=400, highlightthickness=0)
        bg_path = os.path.join(BASE_DIR, 'background.png')
        try:
            self.bg_img_main = tk.PhotoImage(file=bg_path)
            canvas.create_image(550, 0, anchor='ne', image=self.bg_img_main)
        except:
            pass
        canvas.pack(side='top')

        if not self.this_room:
            self.setup_lobby_ui()
        else:
            self.setup_room_ui()

    def setup_lobby_ui(self):
        """Lobby specific UI."""
        tk.Label(self.main_window, text="大厅消息框", font=("宋体", 12)).place(x=20, y=20, width=340, height=20)
        self.msg_box = scrolledtext.ScrolledText(self.main_window, font=("宋体", 10), state=tk.DISABLED)
        self.msg_box.place(x=20, y=40, width=340, height=300)
        self.msg_box.tag_configure("right", justify='right')
        self.msg_box.tag_configure("left", justify='left')

        self.var_chat = tk.StringVar()
        tk.Entry(self.main_window, textvariable=self.var_chat).place(x=20, y=350, width=280, height=25)
        tk.Button(self.main_window, text='发送', command=self.send_chat).place(x=300, y=350, width=60, height=25)

        tk.Label(self.main_window, text="在线用户", font=("宋体", 10)).place(x=380, y=20, width=150, height=20)
        self.user_list = scrolledtext.ScrolledText(self.main_window, font=("宋体", 10), state=tk.DISABLED)
        self.user_list.place(x=380, y=40, width=150, height=150)
        self.update_user_list(self.users_online)

        self.var_room_name = tk.StringVar()
        tk.Label(self.main_window, text="房间名：").place(x=380, y=200)
        tk.Entry(self.main_window, textvariable=self.var_room_name).place(x=380, y=225, width=150)
        tk.Button(self.main_window, text='创建房间', command=self.create_room).place(x=380, y=255, width=70)
        tk.Button(self.main_window, text='加入房间', command=self.join_room).place(x=460, y=255, width=70)

    def setup_room_ui(self):
        """Room specific UI."""
        tk.Label(self.main_window, text=f"房间[{self.this_room}]消息框", font=("宋体", 12)).place(x=20, y=20, width=340, height=20)
        self.msg_box = scrolledtext.ScrolledText(self.main_window, font=("宋体", 10), state=tk.DISABLED)
        self.msg_box.place(x=20, y=40, width=340, height=300)
        self.msg_box.tag_configure("right", justify='right')
        self.msg_box.tag_configure("left", justify='left')

        tk.Button(self.main_window, text='展示图片', command=self.display_image).place(x=20, y=350, width=80, height=25)
        self.var_guess = tk.StringVar()
        tk.Entry(self.main_window, textvariable=self.var_guess).place(x=110, y=350, width=100, height=25)
        tk.Button(self.main_window, text='猜词', command=self.guess_word).place(x=215, y=350, width=60, height=25)

        tk.Label(self.main_window, text="房间用户", font=("宋体", 10)).place(x=380, y=20, width=150, height=20)
        self.user_list = scrolledtext.ScrolledText(self.main_window, font=("宋体", 10), state=tk.DISABLED)
        self.user_list.place(x=380, y=40, width=150, height=120)
        self.update_room_users()

        tk.Label(self.main_window, text=f"房主: {self.host}", font=("宋体", 10)).place(x=380, y=170)
        self.lbl_drawer = tk.Label(self.main_window, text=f"绘画人: {self.drawer}", font=("宋体", 10))
        self.lbl_drawer.place(x=380, y=190)

        if self.username == self.host:
            self.var_target_drawer = tk.StringVar()
            tk.Entry(self.main_window, textvariable=self.var_target_drawer).place(x=380, y=220, width=80)
            tk.Button(self.main_window, text='设绘画人', command=self.set_drawer).place(x=465, y=220, width=65)

        if self.username == self.drawer:
            self.var_word = tk.StringVar()
            tk.Entry(self.main_window, textvariable=self.var_word).place(x=380, y=250, width=80)
            tk.Button(self.main_window, text='设词语', command=self.set_word).place(x=465, y=250, width=65)
            tk.Button(self.main_window, text='开始绘图', command=self.open_drawing_board).place(x=380, y=285, width=70)
            tk.Button(self.main_window, text='发送图片', command=self.send_image).place(x=460, y=285, width=70)

        tk.Button(self.main_window, text='退出房间', command=self.exit_room).place(x=380, y=350, width=150)

    # UI Helpers
    def safe_update_text(self, widget, text, tag=None):
        """Safely updates a disabled ScrolledText widget."""
        widget.config(state=tk.NORMAL)
        widget.insert(tk.END, text, tag)
        widget.config(state=tk.DISABLED)
        widget.see(tk.END)

    def update_user_list(self, users):
        self.user_list.config(state=tk.NORMAL)
        self.user_list.delete(1.0, tk.END)
        for u in users:
            suffix = "[我]" if u == self.username else ""
            self.user_list.insert(tk.END, f"{u}{suffix}\n")
        self.user_list.config(state=tk.DISABLED)

    def update_room_users(self):
        self.user_list.config(state=tk.NORMAL)
        self.user_list.delete(1.0, tk.END)
        for u in self.players:
            tag = "[房主]" if u == self.host else ""
            self.user_list.insert(tk.END, f"{u}{tag}\n")
        self.user_list.config(state=tk.DISABLED)

    # Actions
    def send_chat(self):
        msg = self.var_chat.get().strip()
        if msg:
            self.network.send_data({"cmd": "chat", "user": self.username, "msg": msg})
            self.var_chat.set('')
        else:
            messagebox.showinfo('提示', '请输入消息')

    def create_room(self):
        room = self.var_room_name.get().strip()
        if not room:
            messagebox.showerror('错误', '房间名不能为空')
            return
        if any(char.isspace() for char in room):
            messagebox.showerror('错误', '房间名不能包含空白字符')
            return
        self.network.send_data({
            "cmd": "create_room", "user": self.username, "room": room,
            "host": self.username, "drawer": self.username, "players": [self.username]
        })

    def join_room(self):
        room = self.var_room_name.get().strip()
        if room:
            self.network.send_data({"cmd": "join_room", "user": self.username, "room": room})
        else:
            messagebox.showerror('错误', '请输入房间名')

    def exit_room(self):
        self.network.send_data({"cmd": "exit_room", "player": self.username, "room": self.this_room})
        self.this_room = None
        self.setup_main_ui()

    def guess_word(self):
        word = self.var_guess.get().strip()
        if word:
            self.network.send_data({"cmd": "guess", "player": self.username, "word": word})
        else:
            messagebox.showerror('错误', '请输入猜测内容')

    def set_drawer(self):
        target = self.var_target_drawer.get().strip()
        if target in self.players:
            if target != self.drawer:
                self.network.send_data({
                    "cmd": "set_drawer", "player": self.username, 
                    "drawer": target, "room": self.this_room
                })
            else:
                messagebox.showinfo('提示', f'{target} 已经是绘画人')
        else:
            messagebox.showinfo('提示', '玩家不存在')

    def set_word(self):
        word = self.var_word.get().strip()
        if word:
            self.network.send_data({"cmd": "set_word", "player": self.username, "word": word})
        else:
            messagebox.showerror('错误', '请输入答案')

    def open_drawing_board(self):
        DrawingBoard(self.main_window)

    def send_image(self):
        if os.path.exists('sent_pic.jpg'):
            with open('sent_pic.jpg', 'rb') as f:
                img_bytes = f.read()
            self.network.send_data({"cmd": "image", "player": self.username, "image": img_bytes})
        else:
            messagebox.showinfo('提示', '请先绘图并保存')

    def display_image(self):
        path = 'sent_pic.jpg' if self.username == self.drawer else 'received_pic.jpg'
        if os.path.exists(path):
            Image.open(path).show()
        else:
            messagebox.showinfo('提示', '图片不存在')

    def listen_to_server(self):
        """Threaded listener for server messages."""
        while True:
            data = self.network.recv_data()
            if not data:
                print("Server disconnected")
                break
            
            cmd = data.get("cmd")
            if not cmd: continue

            # Dispatch commands to UI thread
            self.main_window.after(0, lambda d=data: self.handle_server_msg(d))

    def handle_server_msg(self, data: Dict[str, Any]):
        """Main message dispatcher for server responses."""
        cmd = data.get("cmd")
        
        if cmd == "offline":
            u = data.get("user")
            if u in self.users_online: self.users_online.remove(u)
            if not self.this_room:
                self.safe_update_text(self.msg_box, f"系统: {u} 下线了\n", "left")
                self.update_user_list(self.users_online)
        
        elif cmd == "online":
            u = data.get("user")
            if u not in self.users_online: self.users_online.append(u)
            if not self.this_room:
                self.safe_update_text(self.msg_box, f"系统: {u} 上线了\n", "left")
                self.update_user_list(self.users_online)
        
        elif cmd == "chat":
            u, m = data.get("user"), data.get("msg")
            tag = "right" if u == self.username else "left"
            display_text = f"{m} :{u}\n" if tag == "right" else f"{u}: {m}\n"
            self.safe_update_text(self.msg_box, display_text, tag)
        
        elif cmd == "create_room":
            if data.get("user") == self.username:
                if data.get("state") == "success":
                    self.this_room = data.get("room")
                    self.host = self.username
                    self.drawer = self.username
                    self.players = [self.username]
                    self.setup_main_ui()
                else:
                    messagebox.showerror('错误', '房间名已存在')
            else:
                if not self.this_room:
                    self.safe_update_text(self.msg_box, f"系统: 用户[{data.get('user')}]创建了房间[{data.get('room')}]\n", "left")
        
        elif cmd == "join_room":
            u = data.get("user")
            if u == self.username:
                if data.get("state") == "success":
                    self.this_room = data.get("room")
                    self.host = data.get("host")
                    self.drawer = data.get("drawer")
                    self.players = data.get("players")
                    self.setup_main_ui()
                else:
                    messagebox.showerror('错误', '加入房间失败')
            else:
                if self.this_room == data.get("room"):
                    if u not in self.players: self.players.append(u)
                    self.safe_update_text(self.msg_box, f"系统: 玩家[{u}]加入了房间\n", "left")
                    self.update_room_users()
        
        elif cmd == "guess":
            p, reply = data.get("player"), data.get("reply")
            if not reply:
                if p == self.username: messagebox.showinfo('提示', '绘画人未设置答案')
            else:
                res_text = "正确！" if reply == "true" else "错误"
                tag = "right" if p == self.username else "left"
                self.safe_update_text(self.msg_box, f"系统: 玩家[{p}]回答{res_text}\n", tag)
        
        elif cmd == "image":
            p = data.get("player")
            if p == self.username:
                self.safe_update_text(self.msg_box, "系统: 图片已发送成功\n", "right")
            else:
                img_bytes = data.get("image")
                if img_bytes:
                    with open('received_pic.jpg', 'wb') as f:
                        f.write(img_bytes)
                    self.safe_update_text(self.msg_box, f"系统: 收到绘画人[{p}]的图片\n", "left")
        
        elif cmd == "set_drawer":
            self.drawer = data.get("drawer")
            if self.this_room:
                self.lbl_drawer.config(text=f"绘画人: {self.drawer}")
                # Refresh UI to show/hide drawer buttons
                self.setup_main_ui()
                if self.drawer == self.username:
                    messagebox.showinfo('提示', '你被指定为绘画人')
        
        elif cmd == "set_word":
            p = data.get("player")
            if p == self.username:
                self.safe_update_text(self.msg_box, f"系统: 答案[{data.get('word')}]设置成功\n", "right")
            else:
                self.safe_update_text(self.msg_box, f"系统: 绘画人[{p}]已设置答案\n", "left")
        
        elif cmd == "exit_room":
            p = data.get("player")
            if p in self.players: self.players.remove(p)
            self.safe_update_text(self.msg_box, f"系统: 玩家[{p}]退出了房间\n", "left")
            self.update_room_users()
        
        elif cmd == "delete_room":
            messagebox.showinfo('提示', f"房主[{data.get('host')}]注销了房间")
            self.this_room = None
            self.setup_main_ui()

    def on_closing(self):
        if messagebox.askokcancel("退出", "确定要退出吗？"):
            self.network.send_data({"cmd": "offline", "user": self.username})
            self.network.disconnect()
            self.root.quit()

if __name__ == "__main__":
    ChatApp()
