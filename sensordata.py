import subprocess
import json

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

def sensors():
  try:
    result = subprocess.run(
      ['sensors', '-j'],
      stdout = subprocess.PIPE,
      universal_newlines = True,
    )
    data = json.loads(result.stdout);

    return (
      float(data["k10temp-pci-00c3"]["Tctl"]["temp1_input"]),
      float(data["nct6798-isa-0290"]["CHA_FAN1"]["fan1_input"]),
      float(data["nct6798-isa-0290"]["CPU_FAN"]["fan2_input"]),
      float(data["nct6798-isa-0290"]["CHA_FAN2"]["fan3_input"])
    );
  except Exception as err:
    print("sensors:", err);
    return None;

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

    return tuple(int(i) for i in result.stdout.strip().split(', '));
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
  cpu_temperture, rear_fanspeed, cpu_fanspeed, front_fanspeed = sensors();

  gpu_utilization, gpu_memory_utilization, gpu_temperature, gpu_fanspeed = gpu_info();

  cpu = {
    "name": cpu_name,
    "utilization": (cpu_utilization, "%"),
    "temperature": (cpu_temperture, "°C"),
    "fanspeed": (cpu_fanspeed, "rpm"),
  };
  gpu = {
    "name": gpu_name,
    "utilization": (gpu_utilization, "%"),
    "memory": (gpu_memory_utilization, "%"),
    "temperature": (gpu_temperature, "°C"),
    "fanspeed": (gpu_fanspeed, "%"),
  };
  fans = {
    "rear": (rear_fanspeed, "rpm"),
    "front": (front_fanspeed, "rpm"),
  };

  return cpu, gpu, fans;
