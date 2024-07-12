import asyncio
import websockets
import websocket
import json

class User():
  def __init__(self):
    self.ip = "0.0.0.0"
    self.port = 8768
    self.pull = {"0.0.0.0":[[1, "1.7.8.9", 8766]]}
  def get_ip(self):
    return self.ip
  def get_port(self):
    return self.port
  def set_pull(self,pull):
    self.pull = pull
  def get_pull(self):
    return self.pull
class Server(User):
  
  def __init__(self,port):
    User.__init__(self)
    
    self.ip = self.get_ip()
    self.port = self.get_port()
  def add_pull(self,data):
    ip = self.get_ip()
    pull = self.get_pull()
    pull[ip].append(data)
    pull = self.set_pull(pull)
    print("addpull",self.get_pull())
  async def handle_connection(self,websocket, path):
      print("New connection established")
      try:
          async for message in websocket:
              try:
                  print(f"System:Received message: {message}")
                  request = json.loads(message)
                  action = request.get("action")
  
                  if action == "get_pull":
                      pull = self.get_pull()
                      await websocket.send(json.dumps(pull))
                  
                  elif action == "get_data":
                      data = [["0.0.0.0", "Simple Data User2", "hdhdhdhhdhhdhhd"]
                      ]
                      await websocket.send(json.dumps(data))
                  
                  elif action == "send_user_data":
                      user_data = request.get("data")
                      print(f"System:Received user data: {user_data}")
                      await websocket.send(json.dumps({"status": "User data received"}))
                  
                  elif action == "send_data":
                      data = request.get("data")
                      print(f"System:Received data: {data}")
                      self.add_pull(data)
                      await websocket.send(json.dumps({"status": "Data received"}))
                  
                  else:
                      await websocket.send(json.dumps({"error": "Unknown action"}))
              
              except json.JSONDecodeError:
                  await websocket.send(json.dumps({"error": "Invalid JSON"}))
      except websockets.ConnectionClosedError as e:
          print(f"Connection closed with error: {e}")
      except Exception as e:
          print(f"An error occurred: {e}")
      finally:
          print("Connection closed")
class Connect(User):
    def __init__(self,ip,port,my_port):
      User.__init__(self)
      print("Run Node²: ")
      self.port = port
      self.con(self.ip,self.port)
      self.pull = self.get_pull()
    def send_ind(self,ip,port):
      new = [0,ip,port]
      return new
    def con(self,ip,port):
      try:
            self.ws = websocket.create_connection(f"ws://{ip}:{port}")
            print(f"Connected to Node² server {ip}:{port}")
      except Exception as e:
            print(f"Failed to connect to Node² server {ip},{port}: {e}")
    def get_pull(self):
        try:
            self.ws.send(json.dumps({"action": "get_pull"}))
            pull = json.loads(self.ws.recv())
            print(f"Received pull data: {pull}")
            return pull
        except Exception as e:
            print(f"Error getting pull: {e}")
            return {}

    def search(self, ip, ip2):
        self.pull = self.get_pull()
        if not self.pull:
            return None
        t = self.pull[ip]
        for i in range(len(t)):
            self.a = t[i][1]
            self.b = t[i][2]
            if self.a == ip2:
              self.data_user = self.search_data(self.a)
            else:
              self.con(self.a,self.b)
              self.search(self.a, ip2)
        try:
          print("@search",self.data_user)
          return self.data_user
          self.close()
        except(AttributeError):
          print("FATAL ERORR")
    # data_pull
    def get_data(self):
        try:
            self.ws.send(json.dumps({"action": "get_data"}))
            data = json.loads(self.ws.recv())
            print(f"System:Received data: {data}")
            return data
        except Exception as e:
            print(f"Error getting data: {e}")
            return []

    def search_data(self, ip):
        data = self.get_data()
        for i in range(len(data)):
            try:
                if data[i][0] == ip:
                    return [data[i][1], data[i][2]]
            except IndexError:
                print(f"Non Found Data for {ip}")

    def close(self):
        try:
            self.ws.close()
            print("WebSocket connection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")

    # Function to send user data to the server
    def send_user_data(self, user_data):
        try:
            message = {
                "action": "send_user_data",
                "data": user_data
            }
            self.ws.send(json.dumps(message))
            response = json.loads(self.ws.recv())
            #print(f"Server response: {response}")
            return response
        except Exception as e:
            print(f"Error sending user data: {e}")
            return None

    # Function to send arbitrary data to the server
    def send_data(self, data):
        try:
            message = {
                "action": "send_data",
                "data": data
            }
            self.ws.send(json.dumps(message))
            response = json.loads(self.ws.recv())
            print(f"Server response: {response}")
            return response
        except Exception as e:
            print(f"Error sending data: {e}")
            return None
def client(ip,port,ip3,my_ip):
  user_data = User()
  com = Connect(ip,port,my_ip)
  try:
      # Send arbitrary data
      arbitrary_data = com.send_ind(user_data.ip,user_data.port)
      response = com.send_data(arbitrary_data)
      print(response)
      test = com.search(ip, ip3)

      return test
  finally:
      com.close()
def server(my_port):
  root = Server(my_port)
  start_server = websockets.serve(root.handle_connection,root.ip,root.port)
  print(f"Node² server is running on ws://localhost:{root.port}")
  asyncio.get_event_loop().run_until_complete(start_server)
  asyncio.get_event_loop().run_forever()
def main():
  user_data = User()
  hi = """
  Welcom in Node²:
  Connect: yes or No
  Run Server Node²:server
  """
  print(hi)
  while True:
    user = input("Node² connect(yes/no): ")
    if user == "yes":
      ip = input("Node² IP: ")
      port = int(input("Node² PORT: "))
      ip3 = input("Node² Find(data) IP: ")
      print(client(ip,port,ip3,user_data.get_ip()))
      user = input("Node² connect(yes/no): ")
    elif user == "server":
      server(user_data.get_port())
    else:
      break
main()
