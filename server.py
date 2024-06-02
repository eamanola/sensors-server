from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from sensordata import sensor_data

# hostname = "localhost"
hostname = "0.0.0.0"
port = 8080

def json_sensor_data():
  cpu, gpu, fans = sensor_data();

  return json.dumps({
    "cpu": cpu,
    "gpu": gpu,
    "fans": fans,
  });

class SensorsServer(BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path == "/health":
      self.send_response(200)
      self.send_header("Content-type", "text/plain")
      self.end_headers()
      self.wfile.write(bytes("OK", "UTF-8"))

    elif self.path == "/sensors":
      try:
        data = json_sensor_data();
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(data, "UTF-8"))

      except Exception as err:
        self.send_response(500)
        self.end_headers()
        self.wfile.write(bytes("Internal Server Error", "UTF-8"))

        print(err)

    else:
      self.send_response(403)
      self.end_headers()
      self.wfile.write(bytes("Forbidden", "UTF-8"))

if __name__ == "__main__":
  sensorsServer = HTTPServer((hostname, port), SensorsServer)
  print(f'Server started http://{hostname}:{port}')

  try:
    sensorsServer.serve_forever()
  except KeyboardInterrupt:
    pass

  sensorsServer.server_close()
  print("Server stopped.")
