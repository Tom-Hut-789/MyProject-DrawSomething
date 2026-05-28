import socket
import threading
import pickle
import struct
import os
from typing import Dict, List, Any, Optional, Tuple

# Constants
HOST = '0.0.0.0'
PORT = 5200
BUFFER_SIZE = 4096
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'usr_info.pickle')

class DrawServer:
    """The main server for the DrawSomething game."""

    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        
        # State management
        self.users_online: List[str] = []
        self.user_sockets: Dict[str, socket.socket] = {}
        self.user_addresses: Dict[str, Tuple[str, int]] = {}
        self.rooms: Dict[str, Dict[str, Any]] = {} # {room_name: {host, drawer, word, players}}
        
        self.lock = threading.Lock()
        self.db = self._load_db()

    def _load_db(self) -> Dict[str, str]:
        """Loads user credentials from the pickle database."""
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Database error: {e}")
                return {}
        return {}

    def _save_db(self):
        """Saves user credentials to the pickle database."""
        with open(DB_PATH, 'wb') as f:
            pickle.dump(self.db, f)

    def _get_host_ip(self) -> str:
        """Retrieves the local network IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def send_data(self, conn: socket.socket, data: Dict[str, Any]):
        """Sends serialized data to a client with packet framing."""
        try:
            data_bytes = pickle.dumps(data)
            conn.sendall(struct.pack('i', len(data_bytes)) + data_bytes)
        except Exception as e:
            print(f"Send error: {e}")

    def recv_data(self, conn: socket.socket) -> Optional[Dict[str, Any]]:
        """Receives data from a client with packet framing."""
        try:
            header = conn.recv(4)
            if not header:
                return None
            data_len = struct.unpack('i', header)[0]
            data = b''
            while len(data) < data_len:
                packet = conn.recv(min(data_len - len(data), BUFFER_SIZE))
                if not packet:
                    return None
                data += packet
            return pickle.loads(data)
        except Exception as e:
            print(f"Receive error: {e}")
            return None

    def handle_client(self, conn: socket.socket, addr: Tuple[str, int]):
        """Main client thread handler."""
        print(f"Connected by {addr}")
        username = None
        
        try:
            # Phase 1: Authentication
            authenticated, username = self._authenticate(conn, addr)
            if not authenticated:
                conn.close()
                return

            # Phase 2: Game loop
            current_room = None
            while True:
                data = self.recv_data(conn)
                if not data:
                    break
                
                cmd = data.get("cmd")
                if not cmd: continue
                
                print(f"[{username}] Command: {cmd}")
                
                if cmd == "offline":
                    break
                
                elif cmd == "chat":
                    self._handle_chat(username, data)
                
                elif cmd == "create_room":
                    current_room = self._handle_create_room(username, data, conn)
                
                elif cmd == "join_room":
                    current_room = self._handle_join_room(username, data, conn)
                
                elif cmd == "exit_room":
                    self._handle_exit_room(username, data)
                    current_room = None
                
                elif cmd == "guess":
                    self._handle_guess(username, data, current_room)
                
                elif cmd == "image":
                    self._handle_image(username, data, current_room)
                
                elif cmd == "set_drawer":
                    self._handle_set_drawer(username, data, current_room)
                
                elif cmd == "set_word":
                    self._handle_set_word(username, data, current_room)

        except Exception as e:
            print(f"Client handler error for {username}: {e}")
        finally:
            self._cleanup_client(username, conn)

    def _authenticate(self, conn: socket.socket, addr: Tuple[str, int]) -> Tuple[bool, Optional[str]]:
        """Handles login and registration commands."""
        while True:
            data = self.recv_data(conn)
            if not data: return False, None
            
            cmd = data.get("cmd")
            u, p = data.get("username"), data.get("password")
            
            if cmd == "login":
                with self.lock:
                    if u not in self.db:
                        self.send_data(conn, {"login": "fail_null"})
                    elif self.db[u] != p:
                        self.send_data(conn, {"login": "fail_error"})
                    elif u in self.users_online:
                        self.send_data(conn, {"login": "fail_online"})
                    else:
                        # Success
                        self.send_data(conn, {"login": "success", "users_online": self.users_online})
                        # Notify others
                        for other in self.users_online:
                            self.send_data(self.user_sockets[other], {"cmd": "online", "user": u})
                        
                        self.users_online.append(u)
                        self.user_sockets[u] = conn
                        self.user_addresses[u] = addr
                        return True, u
            
            elif cmd == "register":
                with self.lock:
                    if u in self.db:
                        self.send_data(conn, {"register": "existed"})
                    else:
                        self.db[u] = p
                        self._save_db()
                        self.send_data(conn, {"register": "successful"})
            else:
                return False, None

    def _handle_chat(self, sender: str, data: Dict[str, Any]):
        """Broadcasts chat messages to all online users."""
        msg = data.get("msg")
        with self.lock:
            for user in self.users_online:
                self.send_data(self.user_sockets[user], {"cmd": "chat", "user": sender, "msg": msg})

    def _handle_create_room(self, creator: str, data: Dict[str, Any], conn: socket.socket) -> Optional[str]:
        """Handles room creation."""
        room_name = data.get("room")
        with self.lock:
            if room_name in self.rooms:
                self.send_data(conn, {"cmd": "create_room", "user": creator, "state": "failure_existed", "room": room_name})
                return None
            
            self.rooms[room_name] = {
                "host": creator,
                "drawer": creator,
                "word": "",
                "players": [creator]
            }
            self.send_data(conn, {"cmd": "create_room", "user": creator, "state": "success", "room": room_name})
            # Notify lobby
            for user in self.users_online:
                if user != creator:
                    self.send_data(self.user_sockets[user], {"cmd": "create_room", "user": creator, "room": room_name})
            return room_name

    def _handle_join_room(self, player: str, data: Dict[str, Any], conn: socket.socket) -> Optional[str]:
        """Handles room joining."""
        room_name = data.get("room")
        with self.lock:
            if room_name not in self.rooms:
                self.send_data(conn, {"cmd": "join_room", "user": player, "room": room_name, "state": "failure_absent"})
                return None
            
            room = self.rooms[room_name]
            self.send_data(conn, {
                "cmd": "join_room", "user": player, "room": room_name, "state": "success",
                "host": room["host"], "drawer": room["drawer"], "players": room["players"]
            })
            
            # Notify room players
            for other in room["players"]:
                self.send_data(self.user_sockets[other], {"cmd": "join_room", "user": player, "room": room_name})
            
            room["players"].append(player)
            return room_name

    def _handle_exit_room(self, player: str, data: Dict[str, Any]):
        """Handles room exiting."""
        room_name = data.get("room")
        with self.lock:
            self._cleanup_room(player, room_name)

    def _handle_guess(self, player: str, data: Dict[str, Any], room_name: str):
        """Processes guesses in a room."""
        if not room_name: return
        guess = data.get("word")
        with self.lock:
            room = self.rooms.get(room_name)
            if not room: return
            
            answer = room["word"]
            if not answer:
                self.send_data(self.user_sockets[player], {"cmd": "guess", "player": player, "reply": ""})
                return
            
            reply = "true" if guess == answer else "false"
            for user in room["players"]:
                self.send_data(self.user_sockets[user], {"cmd": "guess", "player": player, "reply": reply})

    def _handle_image(self, player: str, data: Dict[str, Any], room_name: str):
        """Relays drawing images to room players."""
        if not room_name: return
        image_data = data.get("image")
        with self.lock:
            room = self.rooms.get(room_name)
            if not room: return
            for user in room["players"]:
                self.send_data(self.user_sockets[user], {"cmd": "image", "player": player, "image": image_data})

    def _handle_set_drawer(self, requester: str, data: Dict[str, Any], room_name: str):
        """Updates the drawer in a room (host only)."""
        if not room_name: return
        new_drawer = data.get("drawer")
        with self.lock:
            room = self.rooms.get(room_name)
            if not room or room["host"] != requester: return
            
            room["drawer"] = new_drawer
            room["word"] = "" # Reset word for new drawer
            for user in room["players"]:
                self.send_data(self.user_sockets[user], {"cmd": "set_drawer", "player": requester, "drawer": new_drawer, "room": room_name})

    def _handle_set_word(self, drawer: str, data: Dict[str, Any], room_name: str):
        """Sets the word to be guessed (drawer only)."""
        if not room_name: return
        word = data.get("word")
        with self.lock:
            room = self.rooms.get(room_name)
            if not room or room["drawer"] != drawer: return
            
            room["word"] = word
            for user in room["players"]:
                self.send_data(self.user_sockets[user], {"cmd": "set_word", "player": drawer, "word": word})

    def _cleanup_room(self, player: str, room_name: str):
        """Removes a player from a room and deletes the room if necessary."""
        if room_name in self.rooms:
            room = self.rooms[room_name]
            if player in room["players"]:
                room["players"].remove(player)
            
            if player == room["host"]:
                # Notify all room players and delete room
                for other in room["players"]:
                    self.send_data(self.user_sockets[other], {"cmd": "delete_room", "host": player, "room": room_name})
                self.rooms.pop(room_name)
            else:
                # Notify remaining players
                for other in room["players"]:
                    self.send_data(self.user_sockets[other], {"cmd": "exit_room", "player": player, "room": room_name})

    def _cleanup_client(self, username: Optional[str], conn: socket.socket):
        """Cleans up user state on disconnection."""
        with self.lock:
            if username in self.users_online:
                # Remove from any rooms
                rooms_to_cleanup = [rn for rn, r in self.rooms.items() if username in r["players"]]
                for rn in rooms_to_cleanup:
                    self._cleanup_room(username, rn)
                
                self.users_online.remove(username)
                self.user_sockets.pop(username)
                self.user_addresses.pop(username)
                
                # Notify others
                for other in self.users_online:
                    self.send_data(self.user_sockets[other], {"cmd": "offline", "user": username})
            
            conn.close()
            if username:
                print(f"User {username} disconnected.")

    def start(self):
        """Starts the server listener."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        
        print(f"Server started on {self._get_host_ip()}:{self.port}")
        print("Waiting for connections...")
        
        try:
            while True:
                client_sock, client_addr = self.server_socket.accept()
                t = threading.Thread(target=self.handle_client, args=(client_sock, client_addr), daemon=True)
                t.start()
        except KeyboardInterrupt:
            print("Server stopping...")
        finally:
            if self.server_socket:
                self.server_socket.close()

if __name__ == "__main__":
    server = DrawServer()
    server.start()
