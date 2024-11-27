import paho.mqtt.client as mqtt
import threading
import sys
import termios
import tty
import signal

# MQTT Server Configuration
MQTT_SERVER = "mqtt.imcloud.tw"  # 替換成你的 MQTT 伺服器位址
MQTT_PORT = 31801                  # 替換成你的 MQTT 伺服器埠號
MQTT_USERNAME = "justteset"   # 替換成你的 MQTT 使用者名稱
MQTT_PASSWORD = "eTESET!@#2024"   # 替換成你的 MQTT 密碼
TOPIC_PREFIX = "cs"          # 替換成你的 topic prefix

class MQTTSimpleTerminal:
    def __init__(self, mac_addr):
        self.mac_addr = mac_addr
        self.tx_topic = f"{TOPIC_PREFIX}/{mac_addr}/tx"
        self.rx_topic = f"{TOPIC_PREFIX}/{mac_addr}/rx"
        self.running = True

        # 初始化 MQTT Client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_message = self.on_message

    def on_message(self, client, userdata, msg):
        """處理從 tx 主題收到的訊息"""
        sys.stdout.buffer.write(msg.payload)  # 直接寫入標準輸出，無需解碼
        sys.stdout.flush()

    def connect(self):
        """連線到 MQTT Broker"""
        print("Connecting to MQTT broker...")
        self.client.connect(MQTT_SERVER, MQTT_PORT, 60)
        self.client.subscribe(self.tx_topic)

        # 啟動 MQTT 客戶端執行緒
        self.client_thread = threading.Thread(target=self.client.loop_forever)
        self.client_thread.daemon = True
        self.client_thread.start()

        print(f"Connected! Listening on {self.tx_topic} and sending to {self.rx_topic}")
        print("Press Ctrl+] to quit.")

    def run(self):
        """啟動終端"""
        # 設定終端為非緩衝模式
        orig_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)

        try:
            while self.running:
                char = sys.stdin.read(1)  # 逐字讀取
                if char == "\x1d":  # Ctrl+] (ASCII 0x1d) 用於退出
                    print("\nExiting...")
                    self.running = False
                else:
                    self.client.publish(self.rx_topic, char.encode("utf-8"))
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)
            self.client.disconnect()

    def handle_sigint(self, signum, frame):
        """捕獲 Ctrl+C 信號並轉發到 MQTT"""
        self.client.publish(self.rx_topic, b'\x03')  # ASCII 0x03 是 Ctrl+C

def main():
    if len(sys.argv) != 2:
        print("Usage: python mqtt_serial.py <MAC addr>")
        sys.exit(1)
    
    mac_address = sys.argv[1]
    terminal = MQTTSimpleTerminal(mac_address)
    
    # 捕捉 Ctrl+C 信號
    signal.signal(signal.SIGINT, terminal.handle_sigint)
    
    terminal.connect()
    terminal.run()

if __name__ == "__main__":
    main()
