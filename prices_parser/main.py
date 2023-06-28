import prices_parser_config
import requests
import time
import hmac
import base64
import hashlib
import json
import prometheus_client
from prometheus_client import Counter, generate_latest
from flask import Flask, Response
from flask_restful import Resource, Api

full_graph_data = []
part_graph_data = []
prices_parser_http_listener = Flask(__name__)
api = Api(prices_parser_http_listener)

CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)
http_requests_counter = Counter('http_requests_total', 'requests to service', ['method', 'endpoint'])

class get_cur_price(Resource):
    def get(self, pair):
        http_requests_counter.labels('GET', '/get_cur_price/' + str(pair)).inc()
        try:  
            now = int(time.time() * 1000)
            url = "https://api.kucoin.com/api/v1/mark-price/" + str(pair) + "/current"
            str_to_sign = str(now) + 'GET' + '/api/v1/mark-price/' + str(pair) + '/current'
            signature = base64.b64encode(hmac.new(prices_parser_config.API_SECRET.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
            passphrase = base64.b64encode(hmac.new(prices_parser_config.API_SECRET.encode('utf-8'), prices_parser_config.API_PASSPHRASE.encode('utf-8'), hashlib.sha256).digest())

            headers = {
                "KC-API-SIGN": signature,
                "KC-API-TIMESTAMP": str(now),
                "KC-API-KEY": prices_parser_config.API_KEY,
                "KC-API-PASSPHRASE": passphrase,
                "KC-API-KEY-VERSION": "2"
            }

            response = requests.get(url, headers=headers)
            price = response.json().get('data').get('value')
            print(response.status_code, {str(pair) : int(round(1/price))})
            return {str(pair) : int(round(1/price))}
    
        except Exception as e:
            print(e)
            print("Error occured")
            return 418

class append_graph_data(Resource):
    def get(self, pair):
        http_requests_counter.labels('GET', '/append_graph_data/' + str(pair)).inc()
        try:  
            now = int(time.time() * 1000)
            url = "https://api.kucoin.com/api/v1/mark-price/" + str(pair) + "/current"
            str_to_sign = str(now) + 'GET' + '/api/v1/mark-price/' + str(pair) + '/current'
            signature = base64.b64encode(hmac.new(prices_parser_config.API_SECRET.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
            passphrase = base64.b64encode(hmac.new(prices_parser_config.API_SECRET.encode('utf-8'), prices_parser_config.API_PASSPHRASE.encode('utf-8'), hashlib.sha256).digest())

            headers = {
                "KC-API-SIGN": signature,
                "KC-API-TIMESTAMP": str(now),
                "KC-API-KEY": prices_parser_config.API_KEY,
                "KC-API-PASSPHRASE": passphrase,
                "KC-API-KEY-VERSION": "2"
            }

            response = requests.get(url, headers=headers)
            price = response.json().get('data').get('value')
            full_graph_data.append(1/price)
            part_graph_data.append(1/price)
            if len(part_graph_data) > prices_parser_config.PART_GRAPH_DATA_LEN:
                part_graph_data.pop(0)

            print(response.status_code, {str(pair) : int(round(1/price))}, "graph_data was append")
            return {str(pair) : int(round(1/price))}
    
        except Exception as e:
            print(e)
            print("Error occured")
            return 418

class get_part_graph_data(Resource):
    def get(self):
        http_requests_counter.labels('GET', '/get_part_graph_data').inc()
        if len(part_graph_data) != 0:
            return json.dumps(part_graph_data)
        else:
            return {"Error" : "Graph data is empty"}
        
class get_full_graph_data(Resource):
    def get(self):
        http_requests_counter.labels('GET', '/get_full_graph_data').inc()
        if len(full_graph_data) != 0:
            return json.dumps(full_graph_data)
        else:
            return {"Error" : "Graph data is empty"}

api.add_resource(get_cur_price, '/get_cur_price/<pair>')
api.add_resource(append_graph_data, '/append_graph_data/<pair>')
api.add_resource(get_part_graph_data, '/get_part_graph_data')
api.add_resource(get_full_graph_data, '/get_full_graph_data')



class metrics(Resource):
    def get(self):
        http_requests_counter.labels('GET', '/metrics').inc()
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

api.add_resource(metrics, '/metrics')


if __name__ == '__main__':
    prices_parser_http_listener.run(host="0.0.0.0", port='1001', debug=True)

