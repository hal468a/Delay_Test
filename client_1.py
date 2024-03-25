import json
import os
import socket
import sys
import time
import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib as mpl
import struct
import subprocess


# 服務器的地址和端口
server_address = ('localhost', 14551)
# 創建一個UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2.0)  # 設置超時時間，確保如果數據丟失，不會永遠等待

# 用於保存往返時間及其對應序列號的列表
rtt_data = []

try:
    success, fail = 0, 0
    for i in range(200):
        # 發送消息，附加序列號
        message = f'msg{i}'.encode()
        ##############################
        # 定義資料結構
        data_format = "63s 63s i i d d d"
        size = struct.calcsize(data_format)
        # print(f"Size of the data format: {size} bytes")
        source = "uav_0"
        destination = f'msg{i}'
        unix_time = 9999
        nanoseconds = -9999
        latitude = 14.22222
        longitude = 14.22222
        altitude = 9999
        data = {
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
        json_data = json.dumps(data)
        # print("source", source)
        # print("destination", destination)
        # print("unix_time", unix_time)
        # print("nanoseconds", nanoseconds)
        # print("latitude", latitude)
        # print("longitude", longitude)
        # print("altitude", altitude)
        # print(json.dumps(data, indent=2, ensure_ascii=False))
        # 將 JSON 資料填充至 32 字節
        json_data_padded = json_data.encode("utf-8")
        # 打包資料
        packed_data = struct.pack(data_format, source.encode("utf-8"), destination.encode("utf-8"), unix_time,
                                  nanoseconds, latitude, longitude, altitude)
        send_data = packed_data + json_data_padded
        print(f"send_data_size: {sys.getsizeof(send_data)} bit")
        ##############################
        send_time = time.time()
        try:
            #sock.sendto(message, server_address)
            sock.sendto(send_data, server_address)

            # 等待回應
            while True:
                data, server = sock.recvfrom(4096)
                receive_time = time.time()
                data_format = "63s 63s i i d d d"  # 定義收到的struct有多少bytes
                # 查看data_format_size
                #print(f"data_format_size: {struct.calcsize(data_format)} bytes")
                #print(f"63s_size: ", struct.calcsize("63s"), "bytes")
                #print(f"i: ", struct.calcsize("i"), "bytes")
                #print(f"d: ", struct.calcsize("d"), "bytes")
                # 解包
                size = struct.calcsize(data_format)
                unpacked_data = struct.unpack(data_format, data[:size])
                # 解析並打印解包後的資料
                source, destination, unix_time, nanoseconds, latitude, longitude, altitude = unpacked_data
                source = source.rstrip(b'\0').decode('utf-8')  # 刪除字串結尾的空字節
                destination = destination.rstrip(b'\0').decode('utf-8')  # 刪除字串結尾的空字節
                # 檢查回應的消息是否匹配
                #print(destination)
                if destination == f'msg{i}':
                    # print("符合")
                    success += 1
                    break
                time.sleep(0.5)
        except socket.timeout:
            fail += 1
            print(f'消息 {i} 超時，未收到回應')
            continue

        # 計算往返時間並保存
        print(f"Success: {success}、Fail: {fail}")
        rtt = (receive_time - send_time) * 1000  # 轉換為毫秒
        rtt_data.append((i, rtt))
        # print(f"接收到匹配的回應: {data.decode()}，RTT: {rtt:.3f} ms")
        print(f"接收到匹配的回應: {destination}，RTT: {rtt:.3f} ms")

finally:
    print('關閉socket')
    sock.close()

# # 將RTT數據保存到CSV檔案，增加了描述性欄位
# with open('rtt_data.csv', 'w', newline='', encoding='utf_8_sig') as csvfile:
#     writer = csv.writer(csvfile)
#     writer.writerow(['封包序列號', 'RTT (ms)'])
#     for seq, rtt in rtt_data:
#         writer.writerow([seq, rtt])


# 若 path result/ 不存在
if not os.path.exists("test1_result"):
    os.mkdir("test1_result")

file_name = f'test1_result/rtt_data_{200}.csv'
print(f"正在寫入 {file_name} ...")

# 將RTT數據保存到CSV檔案，增加了描述性欄位
with open(file_name, 'w', newline='', encoding='utf_8_sig') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['封包序列號', 'RTT (ms)'])
    for seq, rtt in rtt_data:
        writer.writerow([seq, rtt])

# 讀取CSV檔案
data = pd.read_csv(file_name)

# 計算平均RTT
average_rtt = data['RTT (ms)'].mean()
print(f'平均RTT: {average_rtt:.3f} ms')

# 初始化變量
total_time_ms = 0
packets_in_one_second = 0

# 遍歷每次測試的往返時間
for rtt in rtt_data:
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
# 設置中文支持的字體
font_path = os.path.join(project_folder, 'MicrosoftYaHei.ttf')
custom_font = FontProperties(fname=font_path)
mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 使用微軟雅黑體
mpl.rcParams['axes.unicode_minus'] = False

plt.figure(figsize=(10, 6))
plt.plot(data['封包序列號'], data['RTT (ms)'], label='RTT (ms)', marker='o')
plt.axhline(average_rtt, color='r', linestyle='--', label=f'平均RTT: {average_rtt:.2f} ms')

plt.xlabel('封包序列號')
plt.ylabel('RTT (毫秒)')
plt.title('控制指令平均延遲分析')
# plt.title(f'一秒鐘內可以往返的封包數量: {packets_in_one_second}')
plt.legend()
plt.grid(True)
plt.text(10, average_rtt, f'平均延遲: {average_rtt:.3f}', fontsize=9)
# 在保存前設置中文支持
plt.savefig(f'test1_result/rtt_chart_{200}.png', dpi=300)  # 保存圖表為PNG檔案
plt.show()
