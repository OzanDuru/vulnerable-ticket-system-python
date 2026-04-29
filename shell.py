#!/usr/bin/env python3
import subprocess
import sys

if len(sys.argv) > 1:
    cmd = sys.argv[1]
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except Exception as e:
        print(f'Error: {e}')
else:
    print('Usage: python shell.py <command>')
