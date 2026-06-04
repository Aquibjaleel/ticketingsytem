# run.py

import sys, os

# Set project root
abspath = os.path.dirname(__file__)
sys.path.append(abspath)
os.chdir(abspath)

# Import your Flask app
from application import app  # Make sure your Flask app object is called 'app'
if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True, port=5000)