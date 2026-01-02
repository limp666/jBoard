import subprocess

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return f"CMD: {cmd}\nRC: {result.returncode}\nOUT: {result.stdout}\nERR: {result.stderr}\n"
    except Exception as e:
        return f"ERROR: {e}\n"

log = run_cmd("git status")
log += run_cmd("git log -1")
log += run_cmd("git push origin main")

with open("push_verify.txt", "w") as f:
    f.write(log)
