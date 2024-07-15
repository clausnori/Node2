import asyncio
import json
import zstandard as zstd
import base64
import ast
import math
import hashlib
import rsa

class Node:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None
        self.peers = []

    async def connect(self) -> None:
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        print(f"Connected to server {self.ip}:{self.port}")

    async def send_data(self, action: str, data: dict) -> dict:
        try:
            message = json.dumps({"action": action, "data": data}).encode()
            self.writer.write(message)
            await self.writer.drain()
            response_data = await self.reader.read(2000)
            return json.loads(response_data.decode())
        except Exception as e:
            print(f"Error sending data: {e}")
            return {}

    async def close(self) -> None:
        try:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
                print(f"Connection closed for {self.ip}:{self.port}")
        except Exception as e:
            print(f"Error closing connection: {e}")

    async def share_node_info(self) -> None:
        try:
            message = {"action": "share_info", "data": {"ip": self.ip, "port": self.port}}
            response = await self.send_data("share_info", message)
            new_peers = response.get("peers", [])
            self.peers.extend(new_peers)
            print(f"Updated peers: {self.peers}")
        except Exception as e:
            print(f"Error sharing node info: {e}")

    async def discover_peers(self) -> None:
        for peer in self.peers:
            try:
                peer_node = Node(peer["ip"], peer["port"])
                await peer_node.connect()
                await peer_node.share_node_info()
                await peer_node.close()
            except Exception as e:
                print(f"Error discovering peers: {e}")

def generate_keys() -> None:
    public_key, private_key = rsa.newkeys(2048)
    with open("public_key.rsa", 'w') as pub_file, open("private_key.rsa", 'w') as priv_file:
        pub_file.write(public_key.save_pkcs1().decode())
        priv_file.write(private_key.save_pkcs1().decode())
    print("Keys generated successfully")

def read_file(filepath: str) -> str:
    with open(filepath, 'r') as file:
        return file.read()

def get_private_key() -> rsa.PrivateKey:
    return rsa.PrivateKey.load_pkcs1(read_file("private_key.rsa").encode())

def get_public_key() -> rsa.PublicKey:
    return rsa.PublicKey.load_pkcs1(read_file("public_key.rsa").encode())

def encrypt_data(data: str) -> str:
    key = get_public_key()
    encrypted_message = rsa.encrypt(data.encode(), key)
    return base64.b64encode(encrypted_message).decode()

def decrypt_data(data: str) -> str:
    key = get_private_key()
    encrypted_message = base64.b64decode(data.encode())
    return rsa.decrypt(encrypted_message, key).decode()

def get_hash(text: str) -> str:
    sha256 = hashlib.sha256()
    sha256.update(text.encode('utf-8'))
    return sha256.hexdigest()

def encode_and_split(data: str, num_parts: int) -> list[str]:
    data_bytes = data.encode('utf-8')
    compressed_data = zstd.compress(data_bytes)
    part_size = math.ceil(len(compressed_data) / num_parts)
    parts = [compressed_data[i*part_size:(i+1)*part_size] for i in range(num_parts)]
    return [base64.b64encode(part).decode('utf-8') for part in parts]

async def distribute_data(data: str, users: list[tuple[str, int]], suma: str) -> None:
    parts = encode_and_split(data, len(users))
    
    for i, (ip, port) in enumerate(users):
        node = Node(ip, port)
        await node.connect()
        
        next_node = {"ip": "END", "port": "END"} if i == len(users) - 1 else {"ip": users[i + 1][0], "port": users[i + 1][1]}
        message = ["Node_Data", suma, parts[i], next_node]
        
        await node.send_data("post_pull", message)
        await node.close()

async def send_data(ip: str, port: int, data: str) -> str:
    node = Node(ip, port)
    await node.connect()
    try:
        response = await node.send_data("post_data", {"message": data})
        block = await node.send_data("get_data", {})
        await node.close()

        if block.get('next_node') != "END":
            next_ip = block['next_node']['ip']
            next_port = block['next_node']['port']
            return await send_data(next_ip, next_port, data)
        else:
            return base64.b64decode(block['data_part']).decode()
    except Exception as e:
        print(f"Error in send_data: {e}")
    finally:
        await node.close()

def save_id(data: list, hash_sum: str) -> None:
    with open(hash_sum, 'w') as file:
        file.write(str(data))

def get_id(id_: str) -> list:
    with open(id_, 'r') as file:
        return ast.literal_eval(file.read())

async def main(data: str, method: str) -> None:
    users = [("0.0.0.0", 8767), ("0.0.0.0", 8765)]
    encrypted_data = encrypt_data(data)
    data_hash = get_hash(data)
    public_key = get_public_key().save_pkcs1().decode()
    
    main_data = ["Node_ID", data_hash, public_key, [users[0][0], users[0][1]]]
    save_id(main_data, data_hash)
    
    if method == "post":
        await distribute_data(encrypted_data, users, data_hash)
    elif method == "get":
        result = await send_data(users[0][0], users[0][1], main_data)
        decrypted_result = decrypt_data(result)
        print(decrypted_result)
    else:
        print("Invalid method")

if __name__ == "__main__":
    input_data = "My name Claus ,hi node"
    asyncio.run(main(input_data, "post"))
