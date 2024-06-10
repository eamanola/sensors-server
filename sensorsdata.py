import subprocess
import re


def get_cpu_model():
  result = subprocess.run(
    ["lscpu"],
    stdout = subprocess.PIPE,
    universal_newlines = True,
    check = True,
  )

  reg = re.compile(r"^\s*Model\ name:\s*")

  model_lines = [line for line in result.stdout.strip().split("\n") if reg.match(line)]
  assert len(model_lines) == 1

  return reg.sub("", model_lines[0])

CPU_NAME = get_cpu_model()


def get_gpu_model():
  result = subprocess.run(
    ["nvidia-smi", "--query-gpu", "gpu_name", "--format=csv,noheader"],
    stdout = subprocess.PIPE,
    universal_newlines = True,
    check = True,
  )

  return result.stdout.strip()

GPU_NAME = get_gpu_model()


def get_gpu_info():
  keys = ["utilization.gpu", "temperature.gpu", "fan.speed", "utilization.memory"]

  result = subprocess.run(
    ["nvidia-smi", "--query-gpu", ",".join(keys), "--format=csv,noheader,nounits"],
    stdout = subprocess.PIPE,
    universal_newlines = True,
    check = True,
  )

  return [int(i) for i in result.stdout.strip().split(", ")]

def get_sensors_info():
  result = subprocess.run(
    ["sensors", "-u"],
    stdout = subprocess.PIPE,
    universal_newlines = True,
    check = True,
  )

  return result.stdout.strip().split("\n")


def get_cpu_usage():
  result = subprocess.run(
    ["vmstat 1 2|tail -1|awk '{print $15}'"],
    stdout = subprocess.PIPE,
    universal_newlines = True,
    check = True,
    shell = True,
  )

  return 100 - int(result.stdout)


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


def format_cpu(cpu_usage, cpu_temp, cpu_fan):
  return {
    "name": CPU_NAME,
    "utilization": { "value": cpu_usage, "unit": "%" },
    "temperature": { "value": cpu_temp, "unit": "°C" },
    "fanspeed": { "value": cpu_fan[1], "unit": "rpm" },
  }


def format_gpu(gpu_usage, gpu_temp, gpu_fanspeed, gpu_memory):
  return {
    "name": GPU_NAME,
    "utilization": { "value": gpu_usage, "unit": "%" },
    "temperature": { "value": gpu_temp, "unit": "°C" },
    "fanspeed": { "value": gpu_fanspeed, "unit": "%" },
    "memory": { "value": gpu_memory, "unit": "%" },
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
  cpu = format_cpu(cpu_usage, cpu_temp, cpu_fan)

  gpu_usage, gpu_temp, gpu_fanspeed, gpu_memory = get_gpu_info()
  gpu = format_gpu(gpu_usage, gpu_temp, gpu_fanspeed, gpu_memory)

  relabeled = relabel_fans(rest_of_fans)
  fans = format_fans(relabeled)

  return cpu, gpu, fans
