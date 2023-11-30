import subprocess
import time
import signal

process = subprocess.Popen(["python","main.py"])
time.sleep(5)
#process.terminate()
process.send_signal(signal.CTRL_BREAK_EVENT)

print("exit success!!!!")

'''
USE THIS INSTEAD
START STOP
import subprocess
import time
import signal

app = subprocess.Popen(["python","app.py"]) <--------- use without concatenation
print("starting app")
time.sleep(1)
app.send_signal(signal.SIGQUIT)
print("stopping app")
time.sleep(2)

APP
import signal

exit = False

def exit_signal_handler(signal, frame):
    global exit
    print("Terminate signal received")
    exit = True

signal.signal(signal.SIGINT, exit_signal_handler)
signal.signal(signal.SIGTERM, exit_signal_handler)
signal.signal(signal.SIGQUIT, exit_signal_handler)
print("starting")
while not exit:
    pass

'''