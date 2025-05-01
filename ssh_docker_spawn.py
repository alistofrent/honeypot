import socket
import subprocess
import threading
import time
import os
import shutil
import signal
import sys
import psutil

# Directory to store the persistent SSH keys
SSH_KEYS_DIR = os.path.expanduser("~/ssh_docker_keys")
SSH_KEYS_INITIALIZED = False
PID_FILE = "/tmp/ssh_docker_spawn.pid"


def cleanup_containers():
    """Clean up any containers and images created by this script"""
    print("Cleaning up Docker resources...")

    # Find and remove containers with our prefix
    try:
        containers = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=ssh-container", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=True
        ).stdout.strip().split('\n')

        for container in containers:
            if container:
                print(f"Stopping and removing container: {container}")
                subprocess.run(["docker", "stop", container], stderr=subprocess.DEVNULL)
                subprocess.run(["docker", "rm", container], stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Error cleaning up containers: {e}")

    # Find and remove images with our prefix
    try:
        images = subprocess.run(
            ["docker", "images", "--filter", "reference=ssh-image-*", "--format", "{{.Repository}}"],
            capture_output=True, text=True, check=True
        ).stdout.strip().split('\n')

        for image in images:
            if image:
                print(f"Removing image: {image}")
                subprocess.run(["docker", "rmi", image], stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Error cleaning up images: {e}")


def kill_previous_instances():
    """Kill any previously running instances of this script"""
    # Check if PID file exists
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            try:
                old_pid = int(f.read().strip())
                # Check if process is still running
                if psutil.pid_exists(old_pid):
                    # Get the process to verify it's our script
                    process = psutil.Process(old_pid)
                    if "python" in process.name().lower() and "ssh_docker_spawn.py" in ' '.join(process.cmdline()):
                        print(f"Killing previous instance (PID: {old_pid})")
                        try:
                            process.terminate()
                            # Wait for process to terminate
                            gone, alive = psutil.wait_procs([process], timeout=3)
                            if alive:
                                # Force kill if still alive
                                process.kill()
                        except psutil.NoSuchProcess:
                            pass
            except (ValueError, psutil.Error) as e:
                print(f"Error reading or processing PID file: {e}")

    # Also find any other instances by name
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if this is our script
            if proc.pid != os.getpid() and "python" in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] if proc.info['cmdline'] else [])
                if "ssh_docker_spawn.py" in cmdline:
                    print(f"Killing another instance (PID: {proc.pid})")
                    try:
                        proc.terminate()
                        # Wait for process to terminate
                        gone, alive = psutil.wait_procs([proc], timeout=3)
                        if alive:
                            # Force kill if still alive
                            proc.kill()
                    except psutil.NoSuchProcess:
                        pass
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Write current PID to file
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))


def signal_handler(sig, frame):
    """Handle termination signals"""
    print("\nShutting down SSH proxy server...")
    cleanup_containers()
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    sys.exit(0)


def ensure_ssh_keys():
    global SSH_KEYS_INITIALIZED
    if SSH_KEYS_INITIALIZED:
        return

    if not os.path.exists(SSH_KEYS_DIR):
        os.makedirs(SSH_KEYS_DIR)

    # Check if we already have the keys
    if (os.path.exists(os.path.join(SSH_KEYS_DIR, "ssh_host_rsa_key")) and
            os.path.exists(os.path.join(SSH_KEYS_DIR, "ssh_host_ecdsa_key")) and
            os.path.exists(os.path.join(SSH_KEYS_DIR, "ssh_host_ed25519_key"))):
        SSH_KEYS_INITIALIZED = True
        return

    # Create a temporary container to extract the keys
    print("Initializing SSH keys from a temporary container...")
    temp_container = f"ssh-temp-container-{int(time.time())}"
    try:
        # Start a temporary container
        subprocess.run(["docker", "run", "-d", "--name", temp_container, "ssh-docker-image"], check=True)
        time.sleep(1)  # Wait for container to start

        # Extract SSH host keys from the container
        for key_type in ["rsa", "ecdsa", "ed25519"]:
            key_file = f"ssh_host_{key_type}_key"
            key_path = os.path.join(SSH_KEYS_DIR, key_file)

            # Copy the key from container to host
            subprocess.run([
                "docker", "cp",
                f"{temp_container}:/etc/ssh/{key_file}",
                key_path
            ], check=True)

            # Also copy the public key
            subprocess.run([
                "docker", "cp",
                f"{temp_container}:/etc/ssh/{key_file}.pub",
                f"{key_path}.pub"
            ], check=True)

            # Set proper permissions
            os.chmod(key_path, 0o600)
            os.chmod(f"{key_path}.pub", 0o644)

        print("SSH keys successfully extracted and saved.")
        SSH_KEYS_INITIALIZED = True
    except Exception as e:
        print(f"Error initializing SSH keys: {e}")
        raise
    finally:
        # Clean up the temporary container
        subprocess.run(["docker", "stop", temp_container], stderr=subprocess.DEVNULL)
        subprocess.run(["docker", "rm", temp_container], stderr=subprocess.DEVNULL)


def start_container(client_address):
    # Ensure we have the SSH keys initialized
    ensure_ssh_keys()

    container_name = f"ssh-container-{client_address[0]}-{int(time.time())}"
    try:
        # Create a custom Dockerfile that uses our preserved keys
        dockerfile_content = f"""FROM ssh-docker-image
COPY ssh_host_rsa_key /etc/ssh/ssh_host_rsa_key
COPY ssh_host_rsa_key.pub /etc/ssh/ssh_host_rsa_key.pub
COPY ssh_host_ecdsa_key /etc/ssh/ssh_host_ecdsa_key
COPY ssh_host_ecdsa_key.pub /etc/ssh/ssh_host_ecdsa_key.pub
COPY ssh_host_ed25519_key /etc/ssh/ssh_host_ed25519_key
COPY ssh_host_ed25519_key.pub /etc/ssh/ssh_host_ed25519_key.pub
RUN chmod 600 /etc/ssh/ssh_host_*_key
RUN chmod 644 /etc/ssh/ssh_host_*.pub
"""
        # Create a temporary build directory
        build_dir = os.path.join(SSH_KEYS_DIR, container_name)
        os.makedirs(build_dir, exist_ok=True)

        # Write the Dockerfile
        with open(os.path.join(build_dir, "Dockerfile"), "w") as f:
            f.write(dockerfile_content)

        # Copy the SSH keys to the build directory
        for key_type in ["rsa", "ecdsa", "ed25519"]:
            shutil.copy(
                os.path.join(SSH_KEYS_DIR, f"ssh_host_{key_type}_key"),
                os.path.join(build_dir, f"ssh_host_{key_type}_key")
            )
            shutil.copy(
                os.path.join(SSH_KEYS_DIR, f"ssh_host_{key_type}_key.pub"),
                os.path.join(build_dir, f"ssh_host_{key_type}_key.pub")
            )

        # Build the custom image
        print(f"Building custom container with consistent SSH keys: {container_name}")
        image_name = f"ssh-image-{container_name}"
        subprocess.run([
            "docker", "build", "-t", image_name, build_dir
        ], check=True)

        # Start the container using the custom image
        subprocess.run([
            "docker", "run", "-d", "--name", container_name,
            "-p", "0:22",  # Dynamically assign a port
            image_name
        ], check=True)

        # Wait for container to initialize fully
        print(f"Waiting for container {container_name} to initialize...")
        time.sleep(2)

        # Get the assigned port
        result = subprocess.run(
            ["docker", "port", container_name, "22"],
            capture_output=True, text=True, check=True
        )
        port_mapping = result.stdout.strip()
        if not port_mapping:
            raise RuntimeError(f"No port mapping returned for container {container_name}")

        container_port = port_mapping.split(':')[-1]
        print(f"Container {container_name} listening on port {container_port}")

        return container_name, int(container_port)
    except Exception as e:
        print(f"Error starting container: {e}")
        # Clean up if something went wrong
        try:
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir)
        except:
            pass
        try:
            subprocess.run(["docker", "stop", container_name], stderr=subprocess.DEVNULL)
            subprocess.run(["docker", "rm", container_name], stderr=subprocess.DEVNULL)
        except:
            pass
        raise


def handle_client(client_socket, client_address):
    print(f"Connection from {client_address}")
    container_name = None
    container_socket = None

    try:
        # Start a container for this client
        container_name, container_port = start_container(client_address)

        # Connect to the container's SSH service with timeout and retry
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect to container SSH service (attempt {attempt + 1})")
                container_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                container_socket.settimeout(5)
                container_socket.connect(('127.0.0.1', container_port))
                container_socket.settimeout(None)
                print(f"Successfully connected to container SSH service")
                break
            except (socket.timeout, ConnectionRefusedError) as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                if container_socket:
                    container_socket.close()
                if attempt < max_retries - 1:
                    print(f"Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError("Failed to connect to container SSH service after multiple attempts")

        # Set up bidirectional communication
        def forward(source, destination, source_name, dest_name):
            try:
                print(f"Starting forwarding from {source_name} to {dest_name}")
                while True:
                    try:
                        data = source.recv(4096)
                        if not data:
                            print(f"No data received from {source_name}, ending forwarding")
                            break
                        print(f"Forwarding {len(data)} bytes from {source_name} to {dest_name}")
                        destination.sendall(data)
                    except ConnectionResetError as e:
                        print(f"Connection reset while receiving from {source_name}: {e}")
                        break
                    except BrokenPipeError as e:
                        print(f"Broken pipe while sending to {dest_name}: {e}")
                        break
            except Exception as e:
                print(f"Error in forwarding from {source_name} to {dest_name}: {e}")
            finally:
                print(f"Closing {source_name} in forward function")
                try:
                    source.close()
                except:
                    pass

        # Create two threads to handle bidirectional communication
        client_to_container = threading.Thread(
            target=forward,
            args=(client_socket, container_socket, "client", "container")
        )
        container_to_client = threading.Thread(
            target=forward,
            args=(container_socket, client_socket, "container", "client")
        )

        client_to_container.daemon = True
        container_to_client.daemon = True

        client_to_container.start()
        container_to_client.start()

        # Wait for both threads to finish
        client_to_container.join()
        container_to_client.join()

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        # Clean up
        if container_name:
            print(f"Stopping and removing container {container_name}")
            subprocess.run(["docker", "stop", container_name], stderr=subprocess.DEVNULL)
            subprocess.run(["docker", "rm", container_name], stderr=subprocess.DEVNULL)
            # Clean up custom image
            subprocess.run(["docker", "rmi", f"ssh-image-{container_name}"], stderr=subprocess.DEVNULL)
            # Remove build directory
            build_dir = os.path.join(SSH_KEYS_DIR, container_name)
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir)

        if container_socket and not container_socket._closed:
            print("Closing container socket")
            container_socket.close()

        if not client_socket._closed:
            print("Closing client socket")
            client_socket.close()


def main():
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination

    # Kill previous instances and clean up
    kill_previous_instances()
    cleanup_containers()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('0.0.0.0', 2222))
    except OSError as e:
        print(f"Failed to bind to port 2222: {e}")
        print("Port may already be in use. Try finding and killing the process using this port.")
        return

    server.listen(5)
    print("SSH proxy server listening on port 2222")

    try:
        while True:
            client_socket, client_address = server.accept()
            client_handler = threading.Thread(
                target=handle_client, args=(client_socket, client_address)
            )
            client_handler.daemon = True
            client_handler.start()
    except KeyboardInterrupt:
        print("Server shutting down")
    finally:
        server.close()


if __name__ == "__main__":
    main()