import os
import socket
import time
import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib as mpl
# 服務器的地址和端口
server_address = ('localhost', 14551)
# 創建一個UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2.0)  # 設置超時時間，確保如果數據丟失，不會永遠等待

# 用於保存往返時間及其對應序列號的列表
rtt_data = []

try:
    for i in range(200):
        # 發送消息，附加序列號
        message = f'msg{i}'.encode()
        send_time = time.time()
        try:
            sock.sendto(message, server_address)

            # 等待回應
            while True:
                data, server = sock.recvfrom(4096)
                receive_time = time.time()
                # 檢查回應的消息是否匹配
                if data.decode() == f'msg{i}':
                    break
        except socket.timeout:
            print(f'消息 {i} 超時，未收到回應')
            continue

        # 計算往返時間並保存
        rtt = (receive_time - send_time) * 1000  # 轉換為毫秒
        rtt_data.append((i, rtt))
        print(f"接收到匹配的回應: {data.decode()}，RTT: {rtt:.3f} ms")

finally:
    print('關閉socket')
    sock.close()

# 將RTT數據保存到CSV檔案，增加了描述性欄位
with open('rtt_data.csv', 'w', newline='', encoding='utf_8_sig') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['封包序列號', 'RTT (ms)'])
    for seq, rtt in rtt_data:
        writer.writerow([seq, rtt])

# 讀取CSV檔案
data = pd.read_csv('rtt_data.csv')

# 計算平均RTT
average_rtt = data['RTT (ms)'].mean()
print(f'平均RTT: {average_rtt:.3f} ms')

# 繪製RTT圖表
# 獲取專案資料夾路徑
project_folder = os.path.dirname(os.path.abspath(__file__))
# 設置中文支持的字體
font_path = os.path.join(project_folder, 'MicrosoftYaHei.ttf')
custom_font = FontProperties(fname=font_path)
mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 使用微软雅黑
mpl.rcParams['axes.unicode_minus'] = False

plt.figure(figsize=(10, 6))
plt.plot(data['封包序列號'], data['RTT (ms)'], label='RTT (ms)', marker='o')
plt.xlabel('封包序列號')
plt.ylabel('RTT (毫秒)')
plt.title('UDP 往返時間 (RTT)')
plt.legend()
plt.grid(True)
# 在保存前設置中文支持
plt.savefig('rtt_chart.png', dpi=300)  # 保存圖表為PNG檔案
plt.show()