#!/bin/bash

# Start the Flask backend using Gunicorn
echo "Starting Flask backend..."
gunicorn -w 4 -b 0.0.0.0:10000 app:app