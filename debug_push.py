import subprocess
import sys

def run_git_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return f"CMD: {cmd}\nRC: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\n"
    except Exception as e:
        return f"CMD: {cmd}\nERROR: {e}\n"

log = ""
log += run_git_cmd("git remote -v")
log += run_git_cmd("git status")
log += run_git_cmd("git push -v")

with open("git_debug_log.txt", "w") as f:
    f.write(log)

print("Debug log written to git_debug_log.txt")
