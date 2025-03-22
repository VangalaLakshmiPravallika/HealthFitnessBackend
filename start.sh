#!/bin/bash

# Start the Node.js backend
echo "Starting Node.js backend..."
node server.js &

# Start the Python backend using Gunicorn
echo "Starting Python backend..."
gunicorn -w 4 -b 0.0.0.0:10000 app:app &

# Keep the script running
wait