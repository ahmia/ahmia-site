#!/usr/bin/env python
"""Manage program for Django."""
import os
import sys

if __name__ == "__main__":
    # Path to the settings.py file
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ahmia.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
