import subprocess
try:
    log = subprocess.check_output(["git", "log", "-1"], text=True)
    status = subprocess.check_output(["git", "status"], text=True)
    with open("git_verification.txt", "w") as f:
        f.write("LOG:\n" + log + "\n\nSTATUS:\n" + status)
except Exception as e:
    with open("git_verification.txt", "w") as f:
        f.write(str(e))
