import os
import csv
import time
import socket
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

    def send_data(self, nums:int):
        '''
        nums: 要傳送幾筆資料
        '''
        self.nums = nums
        try:
            for i in tqdm(range(self.nums), desc="進行測試"):
                # 發送消息，附加序列號
                message = f'msg{i}'.encode()
                send_time = time.time()
                try:
                    self.udp.sendto(message, self.serverAdd)

                    # 等待回應
                    while True:
                        data, server = self.udp.recvfrom(4096)
                        receive_time = time.time()

                        # 檢查回應的消息是否匹配
                        if data.decode() == f'msg{i}':
                            break

                except socket.timeout:
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
        print(f'平均RTT: {average_rtt:.3f} ms')

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
        plt.axhline(average_rtt, color='r', linestyle='--', label=f'平均RTT: {average_rtt:.2f} ms')
        plt.title('UDP 往返時間分析')
        plt.xlabel('測試編號')
        plt.ylabel('往返時間 (ms)')
        plt.legend()
        plt.grid(True)
        plt.text(10, average_rtt, f'一秒內可以往返的封包數: {packets_in_one_second}', fontsize=9)
        plt.savefig(f'result/rtt_analysis_{self.nums}.png')  # 保存圖表為圖片
        plt.show()

        print(f"平均往返時間: {average_rtt:.2f} ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # 添加參數
    parser.add_argument('--ip', type=str, help='server ip', default="127.0.0.1")
    parser.add_argument('--port', type=int, help='server port', default=14551)
    parser.add_argument('--tout', type=float, help='等待時間', default=2.0)
    parser.add_argument('--nums', type=int, help='測試筆數', default=200)

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