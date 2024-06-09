import subprocess
import re


def cpu_model():
  try:
    result = subprocess.run(
      ["lscpu | grep 'Model name:' |sed 's/^Model\ name:\ *//'"],
      stdout = subprocess.PIPE,
      shell = True,
      universal_newlines = True,
    )

    return result.stdout.strip();

  except Exception as err:
    print("cpu_model:", err);
    return None;


def gpu_model():
  try:
    result = subprocess.run(
      ["nvidia-smi", "--query-gpu", "gpu_name", "--format=csv,noheader"],
      stdout = subprocess.PIPE,
      universal_newlines = True,
    );

    return result.stdout.strip();

  except Exception as err:
    print("gpu_model:", err);
    return None;


def cpu_usage():
  try:
    result = subprocess.run(
      ["vmstat 1 2|tail -1|awk '{print $15}'"],
      stdout = subprocess.PIPE,
      universal_newlines = True,
      shell = True
    );

    return 100 - int(result.stdout);

  except Exception as err:
    print("cpu_usage:", err);
    return None;

# too Spaghetti
# requires 2nd subprocess call for cpu temp
#def fanspeeds():
#  try:
#    result = subprocess.run(
#      ["sensors -u|grep -B 1 -E 'fan.+_input'|sed 's/.*_input:\s*//'|sed s/://"],
#      stdout = subprocess.PIPE,
#      universal_newlines = True,
#      shell = True
#    );
#
#    fanlist = list(map(
#      (lambda fan: { "name": fan[0], "speed": fan[1], "unit": "rpm" }),
#      [line.split('\n') for line in result.stdout.strip().split('\n--\n')]
#    ));
#    cpu_fan = fanlist.pop(1);
#
#    return cpu_fan, fanlist;
#  except Exception as err:
#
#    print("sensors:", err);
#    return None;


def sensors():
  try:
    result = subprocess.run(
      ["sensors", "-u"],
      stdout = subprocess.PIPE,
      universal_newlines = True,
    );

    return result.stdout.strip().split('\n');

  except Exception as err:
    print("sensors:", err);
    return None;


def cpu_temp(sensors_output):
  for i, item in enumerate(sensors_output):
    if(item == "Tctl:"):
      return float(re.sub(r'^\s*temp1_input:\s*', '', sensors_output[i + 1]))

  return 0;


def fanspeeds(sensors_output):
  fans = []
  reg = re.compile('^\s*fan\d+_input:\s*')

  for i, item in enumerate(sensors_output):
    if (reg.match(item)):
      fans.append({
        "name": re.sub(r':\s*$', '', sensors_output[i - 1]),
        "speed": (float(reg.sub('', item)), "rpm")
      })

  return fans


def gpu_info():
  try:
    keys = [
      "utilization.gpu",
      "utilization.memory",
      "temperature.gpu",
      "fan.speed",
    ];

    result = subprocess.run(
      [
        "nvidia-smi",
        "--query-gpu",
        ','.join(keys),
        "--format=csv,noheader,nounits",
      ],
      stdout = subprocess.PIPE,
      universal_newlines = True,
    );

    return [int(i) for i in result.stdout.strip().split(', ')];

  except Exception as err:
    print("gpu_info:", err);
    return None;


cpu_name = None;
gpu_name = None;


def sensor_data():
  global cpu_name;
  global gpu_name;

  cpu_name = cpu_model() if cpu_name is None else cpu_name;
  gpu_name = gpu_model() if gpu_name is None else gpu_name;

  cpu_utilization = cpu_usage();
  gpu_utilization, gpu_memory_utilization, gpu_temperature, gpu_fanspeed = gpu_info();

  sensors_output = sensors();
  cpu_temperture = cpu_temp(sensors_output);
  fans = fanspeeds(sensors_output);

  # system specific
  cpu_fan = fans.pop(1)
  for fan in fans:
    if fan['name'] == 'CHA_FAN1':
      fan['name'] = "Rear"
      continue

    if fan['name'] == 'CHA_FAN2':
      fan['name'] = "Front"
      continue
  # system specific

  cpu = {
    "name": cpu_name,
    "utilization": (cpu_utilization, "%"),
    "temperature": (cpu_temperture, "°C"),
    "fanspeed": (cpu_fan["speed"]),
  };
  gpu = {
    "name": gpu_name,
    "utilization": (gpu_utilization, "%"),
    "memory": (gpu_memory_utilization, "%"),
    "temperature": (gpu_temperature, "°C"),
    "fanspeed": (gpu_fanspeed, "%"),
  };

  return cpu, gpu, fans;
