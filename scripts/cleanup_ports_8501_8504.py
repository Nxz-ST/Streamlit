import subprocess
import sys

def run(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='cp1252', errors='ignore')
    return p.returncode, p.stdout, p.stderr

ports = [8501,8502,8503,8504]
# collect lines
rc, out, err = run('netstat -ano')
if rc != 0:
    print('netstat failed:', err)
    sys.exit(1)

lines = out.splitlines()
found_pids = set()
for line in lines:
    for port in ports:
        if f':{port} ' in line or f':{port}\r' in line or f':{port}\n' in line:
            parts = line.split()
            if parts:
                pid = parts[-1]
                if pid.isdigit():
                    found_pids.add(pid)

if not found_pids:
    print('No processes found on ports', ports)
    sys.exit(0)

killed = []
for pid in found_pids:
    print('Found PID', pid, '- tasklist:')
    rc2,out2,err2 = run(f'tasklist /FI "PID eq {pid}"')
    print(out2)
    rc3,out3,err3 = run(f'taskkill /PID {pid} /F')
    print(out3 or err3)
    if rc3 == 0:
        killed.append(pid)

print('Killed PIDs:', killed)
