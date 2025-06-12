#!/bin/bash

# Change to the project directory
cd /Users/ram/Downloads/TAU-project-main

# Activate virtual environment if you're using one
# source /path/to/your/venv/bin/activate

# Run the SLA checker
python manage.py check_sla

# Log the execution
echo "$(date): SLA check completed" >> /Users/ram/Downloads/TAU-project-main/logs/sla_checker.log 