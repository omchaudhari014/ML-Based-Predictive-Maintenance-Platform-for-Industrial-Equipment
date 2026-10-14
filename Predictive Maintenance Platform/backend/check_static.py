from server import app
import os
print(os.path.abspath(app.static_folder))
