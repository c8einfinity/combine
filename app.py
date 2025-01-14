import sys
from tina4_python import *


print("Running the service", sys.argv)
default_port = 8118
if len(sys.argv) > 2:
    default_port = int(sys.argv[2])
run_web_server("0.0.0.0", default_port)