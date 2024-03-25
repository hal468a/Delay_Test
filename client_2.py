import os
import csv
import sys
import time
import json
import socket
import struct
import argparse
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

from tqdm import tqdm
from matplotlib.font_manager import FontProperties

class Client:
    def __init__(self, server_ip:str, server_port:int, timeout):
        self.serverAdd = (server_ip, server_port)
        self.timeout = timeout

        # 創建一個UDP socket
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.settimeout(timeout)  # 設置超時時間，確保如果數據丟失，不會永遠等待
        
        # 用於保存往返時間及其對應序列號的列表
        self.rtt_data = []

        # 定義資料結構
        self.data_format = "63s 63s i i d d d"
        self.size = struct.calcsize(self.data_format)
        self.source = "uav_0".encode("utf-8")
        self.unix_time = 9999
        self.nanoseconds = -9999
        self.latitude = 14.22222
        self.longitude = 14.22222
        self.altitude = 9999

        # json Data
        self.data = {
            "Drone_name": "uav01",  # fack
            "Roll_Axis": "uav01",
            "Pitch_Axis": "uav01",
            "Yaw_Axis": "uav01",
            "Uav_state": "uav01",
            "battery_serial_number": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "battery_voltage": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "battery_level": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "GPS_signal": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Longitude": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Latitude": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Height": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vertical_Speed": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Horizontal Speed": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Ground_Speed": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Flight_duration": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # fack
            "Signal_5G": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # fack
            "Avoidance": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # 待確認 Avoidance
            "Mission_name": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # 先用mission_mode替代
            "Mission_status": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Pilot": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # fack
            "Power": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Mission_end_position": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Power1": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Power2": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Power3": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Power4": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Power5": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Power6": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Power7": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Power8": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Power9": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Power10": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        }


    def send_data(self, nums:int):
        '''
        nums: 要傳送幾筆資料
        '''
        self.nums = nums
        
        try:
            fail = 0
            for i in tqdm(range(self.nums), desc="進行測試"):
                # 發送消息，附加序列號
                message = f'msg{i}'.encode("utf-8")
                json_bytes = json.dumps(self.data).encode("utf-8")

                packed_data = struct.pack(self.data_format, 
                                           self.source,
                                           message,
                                           self.unix_time,
                                           self.nanoseconds,
                                           self.latitude,
                                           self.longitude,
                                           self.altitude)
                send_data = packed_data + json_bytes
                # print(f"send_data_size: {sys.getsizeof(send_data)} bit")
                send_time = time.time()
                try:
                    self.udp.sendto(send_data, self.serverAdd)

                    # 等待回應
                    while True:
                        data, server = self.udp.recvfrom(4096)
                        receive_time = time.time()

                        # 解包
                        unpacked_data = struct.unpack(self.data_format, data[:self.size])
                        # 解析並打印解包後的資料
                        source, message, unix_time, nanoseconds, latitude, longitude, altitude = unpacked_data
                        source = source.rstrip(b'\0').decode('utf-8')  # 刪除字串結尾的空字節
                        message = message.rstrip(b'\0').decode('utf-8')  # 刪除字串結尾的空字節

                        # 檢查回應的消息是否匹配
                        if message == f'msg{i}':
                            fail += 1
                            print(f"匹配失敗: {fail}")
                            break
                        time.sleep(0.5)

                except socket.timeout:
                    fail += 1
                    print(f"超時失敗: {fail}")
                    print(f'消息 {i} 超時，未收到回應')
                    continue

                # 計算往返時間並保存
                rtt = (receive_time - send_time) * 1000  # 轉換為毫秒
                self.rtt_data.append((i, rtt))
                # print(f"接收到匹配的回應: {data.decode()}，RTT: {rtt:.3f} ms")

        finally:
            print('關閉socket')
            self.udp.close()
    
    def write_data(self):

        # 若 path result/ 不存在
        if not os.path.exists("result"):
            os.mkdir("result")

        self.file_name = f'result/rtt_data_{self.nums}.csv'
        print(f"正在寫入 {self.file_name} ...")

        # 將RTT數據保存到CSV檔案，增加了描述性欄位
        with open(self.file_name, 'w', newline='', encoding='utf_8_sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Test Number', 'RTT (ms)'])
            for seq, rtt in self.rtt_data:
                writer.writerow([seq + 1, rtt])

    def plot_data(self):

        # 讀取CSV檔案
        data = pd.read_csv(self.file_name)

        # 計算平均RTT
        average_rtt = data['RTT (ms)'].mean()
        # print(f'平均RTT: {average_rtt:.3f} ms')

        # 初始化變量
        total_time_ms = 0
        packets_in_one_second = 0

        # 遍歷每次測試的往返時間
        for rtt in self.rtt_data:
            # 累計往返時間
            total_time_ms += rtt[1]
            # 檢查累計時間是否已經超過一秒（1000毫秒）
            if total_time_ms > 1000:
                break
            packets_in_one_second += 1
        print(f"一秒鐘內可以往返的封包數量: {packets_in_one_second}")

        # 繪製RTT圖表
        # 獲取專案資料夾路徑
        project_folder = os.path.dirname(os.path.abspath(__file__))

        # 設置中文字體
        font_path = os.path.join(project_folder, 'MicrosoftYaHei.ttf')
        custom_font = FontProperties(fname=font_path)
        mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 使用微软雅黑
        mpl.rcParams['axes.unicode_minus'] = False

        # 繪製圖表並標註一秒內可以往返的封包數量
        plt.figure(figsize=(10, 6))
        plt.plot(data['Test Number'], data['RTT (ms)'], label='RTT (ms)', marker='o')
        # plt.axhline(average_rtt, color='r', linestyle='--', label=f'平均RTT: {average_rtt:.2f} ms')

        plt.title(f'一秒鐘內可以往返的封包數量: {packets_in_one_second}')
        plt.xlabel('測試編號')
        plt.ylabel('往返時間 (ms)')
        plt.legend()
        plt.grid(True)

        # plt.text(10, average_rtt, f'平均延遲: {average_rtt:.3f}', fontsize=10)
        plt.savefig(f'result/rtt_analysis_{self.nums}.png')  # 保存圖表為圖片
        plt.show()

        # print(f"平均往返時間: {average_rtt:.2f} ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # 添加參數
    parser.add_argument('--ip', type=str, help='Default server ip: 127.0.0.1', default="127.0.0.1")
    parser.add_argument('--port', type=int, help='Default server port: 14551', default=14551)
    parser.add_argument('--tout', type=float, help='Default watting TimeOut: 2.0', default=2.0)
    parser.add_argument('--nums', type=int, help='Default number of test: 200', default=200)

    args = parser.parse_args()

    client = Client(server_ip=args.ip, 
                    server_port=args.port, 
                    timeout=args.tout)

    # 傳送資料
    client.send_data(nums=args.nums)

    # 寫入csv file
    client.write_data()

    # 畫圖
    client.plot_data()