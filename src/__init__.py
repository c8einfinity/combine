# Start your project here
import os

from tina4_python.Database import Database
from tina4_python.Migration import migrate
from tina4_python.ORM import orm
from .app.Setup import check_setup

database_path = os.getenv("DATABASE_PATH", "db-mysql-nyc3-mentalmetrix-do-user-4490318-0.c.db.ondigitalocean.com/25060:qfinder")

dba = Database(f"mysql.connector:{database_path}",
               os.getenv("DATABASE_USERNAME", "doadmin"),
               os.getenv("DATABASE_PASSWORD", "doadmin"))
migrate(dba)
orm(dba)

# Check if we have everything setup
check_setup(dba)

# import everything

from .app import *
from .routes import *


