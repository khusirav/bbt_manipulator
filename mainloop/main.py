import time
import requests
import loop_config

while True:
    try:
        response = requests.get("http://nginx_server_container:1010/append_graph_data/USDT-BTC").json()
        time.sleep(loop_config.DELTA_TIME_SEC)
        print(response)
    except Exception as e:
        print(e)
        time.sleep(loop_config.DELTA_TIME_SEC)
