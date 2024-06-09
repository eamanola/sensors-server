import subprocess
import re


def cpu_model():
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

CPU_NAME = cpu_model()


def gpu_model():
  result = subprocess.run(
    ["nvidia-smi", "--query-gpu", "gpu_name", "--format=csv,noheader"],
    stdout = subprocess.PIPE,
    universal_newlines = True,
    check = True,
  )

  return result.stdout.strip()

GPU_NAME = gpu_model()


def gpu_info():
  keys = ["utilization.gpu", "utilization.memory", "temperature.gpu", "fan.speed"]

  result = subprocess.run(
    ["nvidia-smi", "--query-gpu", ",".join(keys), "--format=csv,noheader,nounits"],
    stdout = subprocess.PIPE,
    universal_newlines = True,
    check = True,
  )

  return dict(zip(keys, [int(i) for i in result.stdout.strip().split(", ")]))


def format_gpu(info):
  return {
    "name": GPU_NAME,
    "utilization": [info["utilization.gpu"], "%"],
    "memory": [info["utilization.memory"], "%"],
    "temperature": [info["temperature.gpu"], "°C"],
    "fanspeed": [info["fan.speed"], "%"],
  }


def sensors():
  result = subprocess.run(
    ["sensors", "-u"],
    stdout = subprocess.PIPE,
    universal_newlines = True,
    check = True,
  )

  return result.stdout.strip().split("\n")


def get_fans(sensors_data):
  fans = []
  reg = re.compile(r"^\s*fan\d+_input:\s*")

  for i, item in enumerate(sensors_data):
    if reg.match(item):
      fans.append({
        "name": re.sub(r":\s*$", "", sensors_data[i - 1]),
        "speed": [float(reg.sub("", item)), "rpm"]
      })

  return fans


# system specific
def format_fans(fans):
  # cpu fan#2
  cpu_fan = fans.pop(1)
  assert cpu_fan["name"] == "CPU_FAN"

  for fan in fans:
    # Rear fans connected to CHA_FAN1 header
    if fan["name"] == "CHA_FAN1":
      fan["name"] = "Rear"
      continue

    # Front fans connected to CHA_FAN2 header
    if fan["name"] == "CHA_FAN2":
      fan["name"] = "Front"
      continue

  return fans, cpu_fan


def cpu_usage():
  result = subprocess.run(
    ["vmstat 1 2|tail -1|awk '{print $15}'"],
    stdout = subprocess.PIPE,
    universal_newlines = True,
    check = True,
    shell = True,
  )

  return 100 - int(result.stdout)


def cpu_temp(sensors_data):
  for i, item in enumerate(sensors_data):
    if item == "Tctl:":
      return float(re.sub(r"^\s*temp1_input:\s*", "", sensors_data[i + 1]))

  return 0


def get_cpu(sensors_data, cpu_fan):
  return {
    "name": CPU_NAME,
    "utilization": [cpu_usage(), "%"],
    "temperature": [cpu_temp(sensors_data), "°C"],
    "fanspeed": cpu_fan["speed"],
  }


# too Spaghetti
# requires 2nd subprocess call for cpu temp
#def fanspeeds():
#  result = subprocess.run(
#    ["sensors -u|grep -B 1 -E 'fan.+_input'|sed 's/.*_input:\s*//'|sed s/://"],
#    stdout = subprocess.PIPE,
#    universal_newlines = True,
#    shell = True
#  )
#
#  fanlist = list(map(
#    (lambda fan: { "name": fan[0], "speed": fan[1], "unit": "rpm" }),
#    [line.split('\n') for line in result.stdout.strip().split('\n--\n')]
#  ))
#  cpu_fan = fanlist.pop(1)
#
#  return cpu_fan, fanlist


def get_sensors():
  gpu = format_gpu(gpu_info())

  sensors_data = sensors()

  fans, cpu_fan = format_fans(get_fans(sensors_data))

  cpu = get_cpu(sensors_data, cpu_fan)

  return cpu, gpu, fans
