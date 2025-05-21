import subprocess
import os
import time
import platform
import sys
import requests
import argparse

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Run majority vote testing for Auto-SQL')
    
    parser.add_argument('-r', '--runs', 
                        type=int, 
                        default=5,
                        help='Number of runs per question (default: 5)')
    
    parser.add_argument('-t', '--timeout', 
                        type=int, 
                        default=90,
                        help='Request timeout in seconds (default: 90)')
    
    parser.add_argument('-i', '--input', 
                        help='Custom input file path')
    
    parser.add_argument('-o', '--output', 
                        help='Custom output file path')
    
    parser.add_argument('-w', '--wait', 
                        type=int, 
                        default=30,
                        help='Maximum time to wait for server in seconds (default: 30)')
    
    parser.add_argument('--no-server', 
                        action='store_true',
                        help="Don't start the server automatically")
    
    return parser.parse_args()

def open_terminal_and_run(command, cwd=None):
    """Run a command in a new terminal window."""
    system = platform.system()

    if system == "Darwin":  # macOS
        subprocess.Popen(['osascript', '-e',
                          f'tell application "Terminal" to do script "cd {cwd} && {command}"'])
    elif system == "Linux":
        subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'cd {cwd} && {command}; exec bash'])
    elif system == "Windows":
        subprocess.Popen(f'start cmd /K "cd /d {cwd} && {command}"', shell=True)
    else:
        raise OSError("Unsupported operating system.")

def run_command(command, cwd=None):
    """Run a command and wait for it to complete."""
    process = subprocess.Popen(command, shell=True, cwd=cwd)
    process.wait()
    return process.returncode

def wait_for_server(url, max_retries=30, delay=2):
    """Wait for the server to become available."""
    print(f"Waiting for the server at {url} to start...")
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"Server is now available at {url}")
                return True
        except requests.RequestException:
            pass
        
        retries += 1
        dots = "." * (retries % 4)
        sys.stdout.write(f"\rWaiting for server{dots.ljust(3)}  ({retries}/{max_retries})")
        sys.stdout.flush()
        time.sleep(delay)
    
    print("\nServer did not become available in the allocated time.")
    return False

def find_project_root():
    """Find the project root directory."""
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # If we're in the backend folder, move up one directory
    if os.path.basename(current_dir) == 'backend':
        return os.path.dirname(current_dir)
    return current_dir

def build_test_command(args):
    """Build the command to run the majority vote test with arguments."""
    cmd_parts = ["python majority_vote_test.py"]
    
    if args.runs:
        cmd_parts.append(f"-r {args.runs}")
    
    if args.timeout:
        cmd_parts.append(f"-t {args.timeout}")
    
    if args.input:
        cmd_parts.append(f"-i {args.input}")
    
    if args.output:
        cmd_parts.append(f"-o {args.output}")
    
    return " ".join(cmd_parts)

def main():
    # Parse command-line arguments
    args = parse_arguments()
    
    # Find the proper project paths
    project_root = find_project_root()
    backend_path = os.path.join(project_root, "backend")
    
    # Make sure we're working with the correct paths
    print(f"Project root: {project_root}")
    print(f"Backend path: {backend_path}")
    
    if not os.path.exists(backend_path):
        print(f"Error: Backend directory not found at {backend_path}")
        return 1
    
    # Check if backend server is already running
    server_url = "http://localhost:8000/docs"
    server_running = False
    
    if not args.no_server:
        print("Checking if backend server is running...")
        try:
            response = requests.get(server_url, timeout=2)
            print("Backend server is already running.")
            server_running = True
        except requests.RequestException:
            print("Backend server is not running. Starting server...")
            server_running = False
        
        # Start backend server if not running
        if not server_running:
            # Start the backend server
            print(f"Starting server from directory: {backend_path}")
            open_terminal_and_run("python main.py", cwd=backend_path)
            
            # Wait for server to start
            if not wait_for_server(server_url, max_retries=args.wait, delay=2):
                print("Failed to start the backend server. Please check for errors in the terminal window.")
                print("If you want to run the test without starting the server, use the --no-server flag.")
                return 1
    else:
        print("Skipping server check (--no-server flag provided)")
    
    # Build the test command with any provided arguments
    test_cmd = build_test_command(args)
    
    # Run the majority vote test
    print(f"\nRunning majority vote test: {test_cmd}")
    result = run_command(test_cmd, cwd=backend_path)
    
    if result == 0:
        print("\nTesting completed successfully.")
        output_file = args.output if args.output else os.path.join(backend_path, "majority_vote_results.json")
        print(f"Results are saved in {output_file}")
        print("You can view the results by opening this file in a text editor.")
    else:
        print(f"\nTesting completed with errors (exit code {result}).")
    
    return result

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 