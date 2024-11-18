import os
import sys

# Get the full path to the Python executable
python_executable_path = sys.executable

# Convert to a relative path
current_directory = os.getcwd()
relative_path = os.path.relpath(python_executable_path, current_directory)

print(f"Python Executable (Full Path): {python_executable_path}")
print(f"Python Executable (Relative Path): {relative_path}")
