from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess

hostname = "localhost"
port = 8080

class SensorsServer(BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path == "/health":
      self.send_response(200)
      self.send_header("Content-type", "text/plain")
      self.end_headers()
      self.wfile.write(bytes("OK", "UTF-8"))

    elif self.path == "/sensors":
      try:
        result = subprocess.run(['sensors', '-j'], stdout = subprocess.PIPE)
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(result.stdout)

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
  print("Server started http://%s:%s" % (hostname, port))

  try:
    sensorsServer.serve_forever()
  except KeyboardInterrupt:
    pass

  sensorsServer.server_close()
  print("Server stopped.")
