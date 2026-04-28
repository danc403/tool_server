import subprocess
import os
import sys
import time

def run_docker_container():
    # Determine the absolute path of the directory where this script is located
    repo_path = os.path.dirname(os.path.abspath(__file__))
    sandbox_path = os.path.join(repo_path, "sandbox")

    # Ensure the sandbox directory exists before mounting
    if not os.path.exists(sandbox_path):
        os.makedirs(sandbox_path)

    image_name = "idg-tool-server"
    container_name = "idg-tool-server"

    # Command to run the docker container
    # -d is removed so we can monitor the process and handle the shutdown
    docker_run_cmd = [
        "docker", "run", "--rm",
        "--name", container_name,
        "-p", "8080:8080",
        "-v", f"{repo_path}:/app",
        "-v", f"{sandbox_path}:/app/sandbox",
        "--cap-drop=ALL",
        image_name
    ]

    print(f"Starting {container_name}...")
    print(f"Mounting Repo: {repo_path}")
    print(f"Mounting Sandbox: {sandbox_path}")

    try:
        # Start the container
        process = subprocess.Popen(docker_run_cmd)
        
        print("\nServer is running. Press Ctrl+C to stop the server and remove the container.")
        
        # Keep the script alive while the container is running
        while True:
            time.sleep(1)
            if process.poll() is not None:
                break

    except KeyboardInterrupt:
        print("\nStopping idg-tool-server...")
    finally:
        # Stop the container explicitly if it's still running
        subprocess.run(["docker", "stop", container_name], capture_output=True)
        print("Container stopped and removed.")

if __name__ == "__main__":
    run_docker_container()
