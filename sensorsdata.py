import subprocess
import re

def run_command(cmd, shell = False):
  result = subprocess.run(
    cmd if shell else cmd.split(),
    stdout = subprocess.PIPE,
    universal_newlines = True,
    check = True,
    shell = shell
  )

  print(cmd, ": ", result.stdout.strip())

  return result.stdout.strip()

def get_cpu_model():
  result = run_command("lscpu | awk '/Model name:/ {sub(/^Model name:/, \"\", $0); print $0}'", shell=True)
  return result

CPU_NAME = get_cpu_model()


def get_gpu_model():
  result = run_command("nvidia-smi --query-gpu gpu_name --format=csv,noheader")
  return result

GPU_NAME = get_gpu_model()


def get_gpu_info():
  keys = ["utilization.gpu", "temperature.gpu", "fan.speed", "utilization.memory"]
  result = run_command("nvidia-smi --query-gpu " + ",".join(keys) + " --format=csv,noheader,nounits")

  return [int(i) for i in result.split(", ")]

# get_gpu_info()

def get_sensors_info():
  result = run_command("sensors -u")

  return result.split("\n")

# get_sensors_info()

def get_cpu_usage():
  result = run_command("vmstat 1 2|tail -1|awk '{print 100 - $15}'", shell=True)

  return int(result)

# get_cpu_usage()

def get_ram():
  result = run_command("free | awk '/Mem:/ {print $3/$2*100}'", shell=True)

  return float(result.replace(",", "."))

# get_ram()

# fans can be named in /etc/sensors.d/*.conf
def take_cpu_fan(fans):
  copy = list(fans)

  cpu_fan = copy.pop(1)
  assert cpu_fan[0] == "CPU_FAN"

  return copy, cpu_fan


def parse_fans(sensors_info):
  fans = []
  reg = re.compile(r"^\s*fan\d+_input:\s*")

  for i, item in enumerate(sensors_info):
    if reg.match(item):
      fans.append([
        re.sub(r":\s*$", "", sensors_info[i - 1]),  # name
        float(reg.sub("", item)),                   # speed
      ])

  return take_cpu_fan(fans)


def parse_cpu_temp(sensors_info):
  for i, item in enumerate(sensors_info):
    if item == "Tctl:":
      return float(re.sub(r"^\s*temp1_input:\s*", "", sensors_info[i + 1]))

  return 0


def relabel_fans(fans):
  copy = list(fans)

  for fan in copy:
    # Rear fans connected to CHA_FAN1 header
    if fan[0] == "CHA_FAN1":
      fan[0] = "Rear"
      continue

    # Front fans connected to CHA_FAN2 header
    if fan[0] == "CHA_FAN2":
      fan[0] = "Front"
      continue

  return copy


def format_cpu(cpu_name, cpu_usage, cpu_temp, cpu_fan, ram):
  return {
    "name": cpu_name,
    "utilization": { "value": cpu_usage, "unit": "%" },
    "temperature": { "value": cpu_temp, "unit": "°C" },
    "fanspeed": { "value": cpu_fan[1], "unit": "rpm" },
    "memory": { "value": ram, "unit": "%" },
  }


def format_gpu(gpu_name, gpu_usage, gpu_temp, gpu_fanspeed, vram):
  return {
    "name": gpu_name,
    "utilization": { "value": gpu_usage, "unit": "%" },
    "temperature": { "value": gpu_temp, "unit": "°C" },
    "fanspeed": { "value": gpu_fanspeed, "unit": "%" },
    "memory": { "value": vram, "unit": "%" },
  }


def format_fans(fans):
  return [
    { "name": fan[0], "speed": { "value": fan[1], "unit": "rpm" } }
    for fan in fans
  ]

# sensors -u|grep -B 1 -E 'fan.+_input'|sed 's/.*_input:\s*//'|sed s/://

def get_sensors():
  sensors_info = get_sensors_info()
  rest_of_fans, cpu_fan = parse_fans(sensors_info)

  cpu_usage = get_cpu_usage()
  cpu_temp = parse_cpu_temp(sensors_info)
  ram = get_ram()

  gpu_usage, gpu_temp, gpu_fanspeed, vram = get_gpu_info()

  cpu = format_cpu(CPU_NAME, cpu_usage, cpu_temp, cpu_fan, ram)
  gpu = format_gpu(GPU_NAME, gpu_usage, gpu_temp, gpu_fanspeed, vram)
  fans = format_fans(relabel_fans(rest_of_fans))

  return cpu, gpu, fans
