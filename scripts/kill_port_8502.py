import subprocess
import sys

def run(cmd):
    # Use cp1252 to avoid UnicodeDecodeError on Windows netstat output
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='cp1252', errors='ignore')
    return p.returncode, p.stdout, p.stderr

# List netstat
rc, out, err = run('netstat -ano')
if rc != 0:
    print('Failed to run netstat', err)
    sys.exit(1)

lines = [l.strip() for l in out.splitlines() if ':8502' in l]
if not lines:
    print('No process found on port 8502')
    sys.exit(0)

killed = []
for line in lines:
    parts = line.split()
    pid = parts[-1]
    print('Found line:', line)
    print('Attempting to kill PID', pid)
    rc2, out2, err2 = run(f'tasklist /FI "PID eq {pid}"')
    print(out2)
    rc3, out3, err3 = run(f'taskkill /PID {pid} /F')
    print(out3)
    if rc3 == 0:
        killed.append(pid)

if killed:
    print('Killed PIDs:', killed)
else:
    print('No PIDs killed')
