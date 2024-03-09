import socket
import argparse

class Server:
    def __init__(self, ip:str, port:int):

        # 建立一個 UDP socket
        self.udp = socket.socket(socket.AF_INET, 
                                 socket.SOCK_DGRAM)
        # 綁定socket到端口
        self.address = (ip, port)
        print('啟動伺服器，位址 %s 連接埠 %s' % self.address)
        self.udp.bind(self.address)
    
    def activate(self):
        try:
            while True:
                print('\n等待接收訊息')
                data, address = self.udp.recvfrom(4096)

                print(f'收到 {len(data)} 位元組自 {address}')
                # print(data)

                if data:
                    sent = self.udp.sendto(data, address)
                    print(f'回傳 {sent} 位元組到 {address}')
                    
        except KeyboardInterrupt as e:
            print(f"Server結束監聽!")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # 添加參數
    parser.add_argument('--ip', type=str, help='Default server ip: 127.0.0.1', default="127.0.0.1")
    parser.add_argument('--port', type=int, help='Default server port: 14551', default=14551)

    args = parser.parse_args()

    server = Server(ip=args.ip, 
                    port=args.port)
    
    # 啟動Server
    server.activate()