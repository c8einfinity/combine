# Start your project here

from tina4_python.Database import Database
from tina4_python.Migration import migrate

dba = Database("sqlite3:combine.db")
migrate(dba)

from routes import *