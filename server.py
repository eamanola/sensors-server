from http.server import BaseHTTPRequestHandler, HTTPServer
from json import dumps
from subprocess import CalledProcessError, TimeoutExpired
from sensorsdata import get_sensors

# HOSTNAME = "localhost"
HOSTNAME = "0.0.0.0"
PORT = 8080

def get_sensors_json():
  cpu, gpu, fans = get_sensors()

  return dumps({
    "cpu": cpu,
    "gpu": gpu,
    "fans": fans,
  })

class SensorsServer(BaseHTTPRequestHandler):
  # pylint: disable-next=C0103:invalid-name
  def do_GET(self):
    if self.path == "/health":
      self.send_response(200)
      self.send_header("Content-type", "text/plain")
      self.end_headers()
      self.wfile.write(bytes("OK", "UTF-8"))

    elif self.path == "/sensors":
      try:
        data = get_sensors_json()
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(data, "UTF-8"))

      except (
        OSError,
        CalledProcessError,
        TimeoutExpired,
        AssertionError,
      ) as err:
        print("/sensors:", err)
        self.send_response(500)
        self.end_headers()
        self.wfile.write(bytes("Internal Server Error", "UTF-8"))

    else:
      self.send_response(403)
      self.end_headers()
      self.wfile.write(bytes("Forbidden", "UTF-8"))

if __name__ == "__main__":
  sensorsServer = HTTPServer((HOSTNAME, PORT), SensorsServer)
  print(f'Server started http://{HOSTNAME}:{PORT}')

  try:
    sensorsServer.serve_forever()
  except KeyboardInterrupt:
    pass

  sensorsServer.server_close()
  print("Server stopped.")
