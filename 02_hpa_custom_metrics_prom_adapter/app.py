import http
import prometheus_client
import os

REQUESTS = prometheus_client.Counter(
    name="hello_world_total", documentation="Count Total of Hello worlds requested"
)

DUMMY_GAUGE = prometheus_client.Gauge(
    name="dummy_gauge", documentation="A dummy gauge to see How HPA will work"
)

DUMMY_GAUGE_VALUE = int(os.getenv("GAUGE_VALUE", "40"))
DUMMY_GAUGE.set(DUMMY_GAUGE_VALUE)


class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        REQUESTS.inc()
        DUMMY_GAUGE.set(DUMMY_GAUGE_VALUE)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hello world")


if __name__ == "__main__":
    prometheus_client.start_http_server(9000)
    server = http.server.HTTPServer(("0.0.0.0", 8000), MyHandler)
    server.serve_forever()
