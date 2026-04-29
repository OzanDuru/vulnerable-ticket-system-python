#!/usr/bin/env python3
"""Run this once to create the database and admin user."""
from app import init_db

if __name__ == '__main__':
    init_db()
