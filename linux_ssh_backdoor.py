#!/usr/bin/env python3

import os
import datetime
import logging
import argparse
import random

from threading import Thread

# For the SSH server functionality
import paramiko



# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("honeypot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("honeypot")

def create_server_key():
    """Create an RSA key for the SSH server if it doesn't exist."""
    if not os.path.exists('server.key'):
        logger.info("Generating new RSA server key...")
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file('server.key')
        logger.info("Server key generated.")

#Calling server key to make sure it exists before it's called
create_server_key()

# RSA key for the SSH server
HOST_KEY = paramiko.RSAKey(filename='server.key')




class FakeFilesystem:
    """Simulated file system to track interactions with the attacker."""

    def __init__(self):
        # Initialize the fake filesystem
        self.current_dir = "/home/user"
        # self.filesystem = {
        #     "/": {
        #         "type": "dir",
        #         "contents": {
        #             "home": {
        #                 "type": "dir",
        #                 "contents": {
        #                     "user": {
        #                         "type": "dir",
        #                         "contents": {
        #                             "Documents": {
        #                                 "type": "dir",
        #                                 "contents": {}
        #                             },
        #                             "Downloads": {
        #                                 "type": "dir",
        #                                 "contents": {}
        #                             },
        #                             ".bash_history": {
        #                                 "type": "file",
        #                                 "contents": "ls\ncd Documents\npwd\nexit\n"
        #                             }
        #                         }
        #                     }
        #                 }
        #             },
        #             "etc": {
        #                 "type": "dir",
        #                 "contents": {
        #                     "passwd": {
        #                         "type": "file",
        #                         "contents": "root:x:0:0:root:/root:/bin/bash\nuser:x:1000:1000:Regular User:/home/user:/bin/bash\n"
        #                     },
        #                     "shadow": {
        #                         "type": "file",
        #                         "contents": "Not accessible: Permission denied"
        #                     }
        #                 }
        #             },
        #             "var": {
        #                 "type": "dir",
        #                 "contents": {
        #                     "log": {
        #                         "type": "dir",
        #                         "contents": {
        #                             "auth.log": {
        #                                 "type": "file",
        #                                 "contents": "Apr 26 10:12:01 server sshd[1234]: Accepted password for user from 192.168.1.100 port 12345\n"
        #                             }
        #                         }
        #                     },
        #                     "www": {
        #                         "type": "dir",
        #                         "contents": {
        #                             "html": {
        #                                 "type": "dir",
        #                                 "contents": {
        #                                     "index.html": {
        #                                         "type": "file",
        #                                         "contents": "<html><body>Test page</body></html>"
        #                                     },
        #                                     "config.php": {
        #                                         "type": "file",
        #                                         "contents": "<?php\n$db_password = 'AdminPassword123';\n?>"
        #                                     }
        #                                 }
        #                             }
        #                         }
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # }

        self.filesystem = {
            "/": {
                "type": "dir",
                "contents": {
                    "home": {
                        "type": "dir",
                        "contents": {
                            "user": {
                                "type": "dir",
                                "contents": {
                                    "Documents": {
                                        "type": "dir",
                                        "contents": {}
                                    },
                                    "Downloads": {
                                        "type": "dir",
                                        "contents": {}
                                    },
                                    ".bash_history": {
                                        "type": "file",
                                        "contents": "ls\ncd Documents\npwd\nexit\n"
                                    }
                                }
                            }
                        }
                    },
                    "etc": {
                        "type": "dir",
                        "contents": {
                            "passwd": {
                                "type": "file",
                                "contents": "root:x:0:0:root:/root:/bin/bash\nuser:x:1000:1000:Regular User:/home/user:/bin/bash\n"
                            },
                            "shadow": {
                                "type": "file",
                                "contents": "Not accessible: Permission denied"
                            }
                        }
                    },
                    "var": {
                        "type": "dir",
                        "contents": {
                            "log": {
                                "type": "dir",
                                "contents": {
                                    "auth.log": {
                                        "type": "file",
                                        "contents": "Apr 26 10:12:01 server sshd[1234]: Accepted password for user from 192.168.1.100 port 12345\n"
                                    }
                                }
                            },
                            "www": {
                                "type": "dir",
                                "contents": {
                                    "html": {
                                        "type": "dir",
                                        "contents": {
                                            "index.html": {
                                                "type": "file",
                                                "contents": "<html><body>Test page</body></html>"
                                            },
                                            "config.php": {
                                                "type": "file",
                                                "contents": "<?php\n$db_password = 'AdminPassword123';\n?>"
                                            },
                                            "config.db": {
                                                "type": "file",
                                                "password_protected": True,
                                                "password": "AdminPassword123",
                                                "contents": "-- Database Configuration --\r\n" +
                                                            "DATABASE_HOST=localhost\r\n" +
                                                            "DATABASE_PORT=3306\r\n" +
                                                            "DATABASE_NAME=webapp\r\n" +
                                                            "DATABASE_USER=admin\r\n" +
                                                            "DATABASE_PASSWORD=SuperSecretPassword2025!\r\n" +
                                                            "-- API Keys --\r\n" +
                                                            "AWS_ACCESS_KEY=AKIA3IXZF7VXXU5BV2P3\r\n" +
                                                            "AWS_SECRET_KEY=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\r\n" +
                                                            "STRIPE_API_KEY=sk_live_51Nv7ZQJMKVJHbVRSg2GQdbS99iwbkz\r\n" +
                                                            "-- Server Configuration --\r\n" +
                                                            "DEBUG_MODE=false\r\n" +
                                                            "ENABLE_LOGGING=true\r\n" +
                                                            "LOG_LEVEL=warning\r\n"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }


    def get_path_dict(self, path):
        """Get the dictionary at the specified path."""
        if path == "/":
            return self.filesystem["/"]

        parts = path.strip("/").split("/")
        current = self.filesystem["/"]

        for part in parts:
            if part == "":
                continue
            if part not in current["contents"] or current["contents"][part]["type"] != "dir":
                return None
            current = current["contents"][part]

        return current

    def get_item_at_path(self, path):
        """Get the item at the specified path."""
        if path == "/":
            return self.filesystem["/"]

        parent_path = os.path.dirname(path)
        basename = os.path.basename(path)

        parent = self.get_path_dict(parent_path)
        if parent is None or basename not in parent["contents"]:
            return None

        return parent["contents"][basename]

    def resolve_path(self, path):
        """Resolve a path (absolute or relative) to an absolute path."""
        if path.startswith("/"):
            return os.path.normpath(path)
        else:
            return os.path.normpath(os.path.join(self.current_dir, path))

    def change_directory(self, path):
        """Change the current directory."""
        resolved_path = self.resolve_path(path)
        path_dict = self.get_path_dict(resolved_path)

        if path_dict is None:
            return f"cd: {path}: No such file or directory"

        if path_dict.get("type") != "dir":
            return f"cd: {path}: Not a directory"

        self.current_dir = resolved_path
        return ""

    def list_directory(self, path=None):
        """List the contents of a directory."""
        if path is None:
            path = self.current_dir
        else:
            path = self.resolve_path(path)

        path_dict = self.get_path_dict(path)
        if path_dict is None:
            return f"ls: cannot access '{path}': No such file or directory"

        if path_dict.get("type") != "dir":
            return path

        result = []
        for name, item in path_dict["contents"].items():
            if item["type"] == "dir":
                result.append(f"\033[1;34m{name}/\033[0m")  # Blue for directories
            else:
                result.append(name)

        return "  ".join(result)

    def create_directory(self, path):
        """Create a new directory."""
        resolved_path = self.resolve_path(path)
        parent_path = os.path.dirname(resolved_path)
        basename = os.path.basename(resolved_path)

        parent = self.get_path_dict(parent_path)
        if parent is None:
            return f"mkdir: cannot create directory '{path}': No such file or directory"

        if basename in parent["contents"]:
            return f"mkdir: cannot create directory '{path}': File exists"

        parent["contents"][basename] = {
            "type": "dir",
            "contents": {}
        }

        return ""

    def get_current_directory(self):
        """Get the current working directory."""
        return self.current_dir


    def grep_file(self, pattern, path=None, recursive=False):
        """Search for a pattern in a file or directory."""
        if path is None:
            path = self.current_dir
        else:
            path = self.resolve_path(path)

        item = self.get_item_at_path(path)
        if item is None:
            return f"grep: {path}: No such file or directory"

        if item["type"] == "dir":
            results = []

            def search_dir(dir_path, dir_item):
                for name, subitem in dir_item["contents"].items():
                    full_path = os.path.join(dir_path, name)

                    # Skip password-protected files
                    if "password_protected" in subitem and subitem["password_protected"]:
                        continue

                    if subitem["type"] == "file":
                        if pattern in subitem["contents"]:
                            lines = subitem["contents"].split("\n")
                            for line in lines:
                                if pattern in line:
                                    results.append(f"{full_path}:{line}")
                    elif recursive and subitem["type"] == "dir":
                        search_dir(full_path, subitem)

            search_dir(path, item)
            return "\r\n".join(results) if results else f"grep: {pattern}: No matches found"
        else:
            # Skip password-protected files
            if "password_protected" in item and item["password_protected"]:
                return ""

            if pattern in item["contents"]:
                lines = item["contents"].split("\n")
                results = []
                for line in lines:
                    if pattern in line:
                        results.append(line)
                return "\r\n".join(results)
            else:
                return ""

    def create_file(self, path, content=""):
        """Create a new file."""
        resolved_path = self.resolve_path(path)
        parent_path = os.path.dirname(resolved_path)
        basename = os.path.basename(resolved_path)

        parent = self.get_path_dict(parent_path)
        if parent is None:
            return f"touch: cannot touch '{path}': No such file or directory"

        parent["contents"][basename] = {
            "type": "file",
            "contents": content
        }

        return ""

    def remove_item(self, path, recursive=False):
        """Remove a file or directory."""
        resolved_path = self.resolve_path(path)
        parent_path = os.path.dirname(resolved_path)
        basename = os.path.basename(resolved_path)

        parent = self.get_path_dict(parent_path)
        if parent is None or basename not in parent["contents"]:
            return f"rm: cannot remove '{path}': No such file or directory"

        item = parent["contents"][basename]
        if item["type"] == "dir" and not recursive:
            return f"rm: cannot remove '{path}': Is a directory"

        del parent["contents"][basename]
        return ""


class SSHServerInterface(paramiko.ServerInterface):
    """Implementation of the SSH server interface."""

    def __init__(self, client_address):
        self.client_address = client_address

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    # def check_auth_password(self, username, password):
    #     # Log the authentication attempt
    #     logger.info(f"Login attempt: username={username}, password={password}, src={self.client_address}")
    #     return paramiko.AUTH_SUCCESSFUL
    def check_auth_password(self, username, password):
        # Log the authentication attempt
        if password == "Password":
            logger.info(f"Successful login: username={username}, password={password}, src={self.client_address}")
            return paramiko.AUTH_SUCCESSFUL
        else:
            logger.info(f"Failed login attempt: username={username}, password={password}, src={self.client_address}")
            return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password'

    def check_channel_shell_request(self, channel):
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True


class SSHChannel(paramiko.channel.Channel):
    """Custom channel for handling SSH session."""

    def __init__(self, client_address, *args, **kwargs):
        super(SSHChannel, self).__init__(*args, **kwargs)
        self.client_address = client_address
        self.filesystem = FakeFilesystem()
        self.username = "user"
        self.hostname = "server"
        self.exit_status = 0


    def run(self):
        """Run the shell session."""
        self.send(f"Welcome to Ubuntu 20.04.2 LTS (GNU/Linux 5.4.0-77-generic x86_64)\n\n")
        self.send(f" * Documentation:  https://help.ubuntu.com\n")
        self.send(f" * Management:     https://landscape.canonical.com\n")
        self.send(f" * Support:        https://ubuntu.com/advantage\n\n")

        while True:
            # Send prompt
            prompt = f"{self.username}@{self.hostname}:{self.filesystem.get_current_directory()}$ "
            self.send(prompt)

            # Receive command
            command = ""
            while not command.endswith("\n"):
                data = self.recv(1024)
                if not data:
                    return
                self.send(data)  # Echo back
                command += data.decode("utf-8")

            command = command.strip()
            logger.info(f"Command from {self.client_address}: {command}")

            # Process command
            response = self.process_command(command)
            if response is not None:
                self.send(response + "\n")


def handle_connection(client, addr):
    """Handle an incoming SSH connection."""
    try:
        transport = paramiko.Transport(client)
        transport.add_server_key(HOST_KEY)

        server = SSHServerInterface(addr)
        transport.start_server(server=server)

        channel = transport.accept(20)
        if channel is None:
            logger.warning(f"No channel from {addr}")
            return

        logger.info(f"Authenticated connection from {addr}")

        # Set up the fake environment
        fs = FakeFilesystem()
        username = "user"
        hostname = "server"

        # Send welcome message
        welcome_msg = "Welcome to Ubuntu 20.04.2 LTS (GNU/Linux 5.4.0-77-generic x86_64)\r\n\r\n"
        welcome_msg += " * Documentation:  https://help.ubuntu.com\r\n"
        welcome_msg += " * Management:     https://landscape.canonical.com\r\n"
        welcome_msg += " * Support:        https://ubuntu.com/advantage\r\n\r\n"
        channel.sendall(welcome_msg.encode('utf-8'))

        # Main command loop
        while True:
            # Send prompt
            prompt = f"{username}@{hostname}:{fs.get_current_directory()}$ "
            channel.sendall(prompt.encode('utf-8'))

            # Read command line
            command = ""
            buf = b""

            while True:
                data = channel.recv(1024)
                if not data:
                    # Connection closed
                    return

                # Echo data back to client
                channel.sendall(data)

                buf += data
                if b'\n' in buf or b'\r' in buf:
                    # Process when we receive a newline
                    line = buf.decode('utf-8').strip()
                    command = line
                    logger.info(f"Command from {addr}: {command}")
                    break

            # Process the command
            if command == "exit" or command == "logout":
                channel.sendall(b"\r\nlogout\r\nConnection to server closed.\r\n")
                channel.close()
                return

            # Process command and get response
            if command:
                response = process_command(command, fs, username, addr)
                if response:
                    channel.sendall(f"\r\n{response}\r\n".encode('utf-8'))
                else:
                    channel.sendall(b"\r\n")

    except Exception as e:
        logger.error(f"Error handling SSH connection from {addr}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        try:
            transport.close()
        except:
            pass


def process_command(command, fs, username, addr):
    """Process a shell command."""
    if not command:
        return ""

    # Split the command into parts
    parts = command.split()
    cmd = parts[0]
    args = parts[1:]

    if cmd == "exit" or cmd == "logout":
        return "logout\nConnection to server closed."


    elif cmd == "?":
        help_text = (
            "Available commands:\n"
            "  ls        List directory contents\n"
            "  cd        Change directory\n"
            "  pwd       Print working directory\n"
            "  mkdir     Make directory\n"
            "  touch     Create empty file\n"
            "  rm        Remove file or directory\n"
            "  grep      Search for pattern\n"
            "  exit      Exit the shell\n"
            "  logout    Logout of the system\n"
            "  clear     Clear the terminal screen\n"
            "  cat       Display file contents\n"
            "  who       Show who is logged on\n"
            "  uname     Print system information\n"
            "  find      Search for files\n"
            "  ps        Show process status\n"
            "  netstat   Network statistics\n"
        )
        # Replace all newlines with \r\n for proper terminal handling
        return help_text.replace('\n', '\r\n')


    elif cmd == "netstat":
        # Parse netstat command options
        show_all = "-a" in args
        show_tcp = "-t" in args or not any(opt in args for opt in ["-u", "-x"])
        show_udp = "-u" in args
        show_unix = "-x" in args
        show_programs = "-p" in args
        show_numeric = "-n" in args
        show_listening = "-l" in args
        show_route = "-r" in args

        # Current timestamp for dynamic data
        current_time = datetime.datetime.now()

        # Create timestamp for established connections
        def random_timestamp():
            # Generate a random time within the last hour
            minutes_ago = random.randint(0, 59)
            seconds_ago = random.randint(0, 59)
            return (current_time - datetime.timedelta(minutes=minutes_ago, seconds=seconds_ago)).strftime('%H:%M:%S')

        # Generate realistic-looking ports and IPs
        def random_port():
            return str(random.randint(1024, 65535))

        def random_local_ip():
            return f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"

        def random_remote_ip():
            # Different formats for remote IPs to look realistic
            ip_type = random.randint(1, 4)
            if ip_type == 1:  # Local network
                return f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"
            elif ip_type == 2:  # Class B private
                return f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            elif ip_type == 3:  # Class A private
                return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            else:  # Public IP
                return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

        # Routing table for -r option
        if show_route:
            route_output = (
                "Kernel IP routing table\r\n"
                "Destination     Gateway         Genmask         Flags   MSS Window  irtt Iface\r\n"
                "0.0.0.0         192.168.1.1     0.0.0.0         UG        0 0          0 eth0\r\n"
                "127.0.0.0       0.0.0.0         255.0.0.0       U         0 0          0 lo\r\n"
                "192.168.1.0     0.0.0.0         255.255.255.0   U         0 0          0 eth0\r\n"
            )
            return route_output

        # Create connection lists
        tcp_connections = []
        udp_connections = []
        unix_sockets = []

        # Standard services
        services = {
            "22": "sshd",
            "80": "apache2",
            "443": "apache2",
            "3306": "mysqld",
            "8080": "java"
        }

        # TCP connections
        if show_tcp:
            # System services listening
            if show_all or show_listening:
                tcp_connections.append({
                    "protocol": "tcp",
                    "recv_q": "0",
                    "send_q": "0",
                    "local_addr": "0.0.0.0:22",
                    "foreign_addr": "0.0.0.0:*",
                    "state": "LISTEN",
                    "pid_program": "451/sshd"
                })
                tcp_connections.append({
                    "protocol": "tcp",
                    "recv_q": "0",
                    "send_q": "0",
                    "local_addr": "127.0.0.1:3306",
                    "foreign_addr": "0.0.0.0:*",
                    "state": "LISTEN",
                    "pid_program": "474/mysqld"
                })
                tcp_connections.append({
                    "protocol": "tcp",
                    "recv_q": "0",
                    "send_q": "0",
                    "local_addr": "0.0.0.0:80",
                    "foreign_addr": "0.0.0.0:*",
                    "state": "LISTEN",
                    "pid_program": "492/apache2"
                })
                tcp_connections.append({
                    "protocol": "tcp",
                    "recv_q": "0",
                    "send_q": "0",
                    "local_addr": "0.0.0.0:443",
                    "foreign_addr": "0.0.0.0:*",
                    "state": "LISTEN",
                    "pid_program": "492/apache2"
                })

            # Attacker's SSH connection
            tcp_connections.append({
                "protocol": "tcp",
                "recv_q": "0",
                "send_q": "0",
                "local_addr": f"192.168.83.132:22",
                "foreign_addr": f"{addr[0]}:{random_port()}",
                "state": "ESTABLISHED",
                "pid_program": "1234/sshd: " + username
            })

            # Other random established connections
            if show_all:
                # Generate random established connections
                for _ in range(random.randint(3, 8)):
                    local_port = random.choice(list(services.keys()))
                    tcp_connections.append({
                        "protocol": "tcp",
                        "recv_q": str(random.randint(0, 8)),
                        "send_q": str(random.randint(0, 8)),
                        "local_addr": f"{random_local_ip()}:{local_port}",
                        "foreign_addr": f"{random_remote_ip()}:{random_port()}",
                        "state": "ESTABLISHED",
                        "pid_program": f"{random.randint(500, 9999)}/{services[local_port]}"
                    })

        # UDP connections
        if show_udp and (show_all or show_listening):
            udp_connections.append({
                "protocol": "udp",
                "recv_q": "0",
                "send_q": "0",
                "local_addr": "0.0.0.0:123",
                "foreign_addr": "0.0.0.0:*",
                "state": "",
                "pid_program": "389/systemd-timesyn"
            })
            udp_connections.append({
                "protocol": "udp",
                "recv_q": "0",
                "send_q": "0",
                "local_addr": "127.0.0.1:323",
                "foreign_addr": "0.0.0.0:*",
                "state": "",
                "pid_program": "389/chronyd"
            })
            udp_connections.append({
                "protocol": "udp",
                "recv_q": "0",
                "send_q": "0",
                "local_addr": "0.0.0.0:68",
                "foreign_addr": "0.0.0.0:*",
                "state": "",
                "pid_program": "434/NetworkManager"
            })

        # Unix domain sockets
        if show_unix and (show_all or show_listening):
            unix_sockets.append({
                "protocol": "unix",
                "refcnt": "2",
                "flags": "[ ACC ]",
                "type": "STREAM",
                "state": "LISTENING",
                "pid_program": "474/mysqld",
                "path": "/var/run/mysqld/mysqld.sock"
            })
            unix_sockets.append({
                "protocol": "unix",
                "refcnt": "2",
                "flags": "[ ACC ]",
                "type": "STREAM",
                "state": "LISTENING",
                "pid_program": "492/apache2",
                "path": "/var/run/apache2/cgisock.1234"
            })
            unix_sockets.append({
                "protocol": "unix",
                "refcnt": "2",
                "flags": "[ ACC ]",
                "type": "STREAM",
                "state": "LISTENING",
                "pid_program": "421/dbus-daemon",
                "path": "/var/run/dbus/system_bus_socket"
            })

        # Build the output
        output = []

        # Add header based on type
        if tcp_connections or udp_connections:
            output.append("Active Internet connections" +
                          (" (servers and established)" if show_all else
                           (" (only servers)" if show_listening else
                            " (w/o servers)")))
            output.append("Proto Recv-Q Send-Q Local Address           Foreign Address         State" +
                          (" PID/Program name" if show_programs else ""))

        # Add TCP connections
        for conn in tcp_connections:
            line = f"{conn['protocol']} {conn['recv_q']:6} {conn['send_q']:6} {conn['local_addr']:23} {conn['foreign_addr']:23} {conn['state']}"
            if show_programs:
                line += f" {conn['pid_program']}"
            output.append(line)

        # Add UDP connections
        for conn in udp_connections:
            line = f"{conn['protocol']} {conn['recv_q']:6} {conn['send_q']:6} {conn['local_addr']:23} {conn['foreign_addr']:23} {conn['state']}"
            if show_programs:
                line += f" {conn['pid_program']}"
            output.append(line)

        # Add Unix sockets if requested
        if unix_sockets:
            output.append("")  # Empty line
            output.append("Active UNIX domain sockets (servers and established)")
            output.append("Proto RefCnt Flags       Type       State         I-Node" +
                          (" PID/Program name    Path" if show_programs else " Path"))

            for sock in unix_sockets:
                line = f"{sock['protocol']} {sock['refcnt']:6} {sock['flags']} {sock['type']:11} {sock['state']:13}"
                line += f" {random.randint(10000, 99999)}"
                if show_programs:
                    line += f" {sock['pid_program']:<18}"
                line += f" {sock['path']}"
                output.append(line)

        return "\r\n".join(output)

    elif cmd == "uname":
        # Parse uname options
        show_all = "-a" in args
        show_kernel = "-s" in args or not args  # Default behavior is -s
        show_nodename = "-n" in args
        show_release = "-r" in args
        show_version = "-v" in args
        show_machine = "-m" in args
        show_processor = "-p" in args
        show_hardware = "-i" in args
        show_os = "-o" in args

        result = []

        if show_all or show_kernel:
            result.append("Linux")

        if show_all or show_nodename:
            result.append("server")

        if show_all or show_release:
            result.append("5.4.0-77-generic")

        if show_all or show_version:
            result.append("#86-Ubuntu SMP Thu Jun 17 02:35:03 UTC 2021")

        if show_all or show_machine:
            result.append("x86_64")

        if show_all or show_processor:
            result.append("x86_64")

        if show_all or show_hardware:
            result.append("unknown")

        if show_all or show_os:
            result.append("GNU/Linux")

        return " ".join(result)

    elif cmd == "ps":
        # Parse ps command options
        show_all = "-a" in args or "-e" in args or "-ax" in args
        show_full = "-f" in args
        show_forest = "-f" in args

        # Create fake process list
        processes = [
            {"pid": "1", "user": "root", "cpu": "0.0", "mem": "0.1", "vsz": "10576", "rss": "3236", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:03", "command": "/sbin/init"},
            {"pid": "2", "user": "root", "cpu": "0.0", "mem": "0.0", "vsz": "0", "rss": "0", "tty": "?", "stat": "S",
             "start": "Apr01", "time": "0:00", "command": "[kthreadd]"},
            {"pid": "3", "user": "root", "cpu": "0.0", "mem": "0.0", "vsz": "0", "rss": "0", "tty": "?", "stat": "S",
             "start": "Apr01", "time": "0:00", "command": "[rcu_gp]"},
            {"pid": "4", "user": "root", "cpu": "0.0", "mem": "0.0", "vsz": "0", "rss": "0", "tty": "?", "stat": "S",
             "start": "Apr01", "time": "0:00", "command": "[rcu_par_gp]"},
            {"pid": "6", "user": "root", "cpu": "0.0", "mem": "0.0", "vsz": "0", "rss": "0", "tty": "?", "stat": "S",
             "start": "Apr01", "time": "0:00", "command": "[kworker/0:0H-kblockd]"},
            {"pid": "9", "user": "root", "cpu": "0.0", "mem": "0.0", "vsz": "0", "rss": "0", "tty": "?", "stat": "S",
             "start": "Apr01", "time": "0:00", "command": "[mm_percpu_wq]"},
            {"pid": "234", "user": "root", "cpu": "0.0", "mem": "0.1", "vsz": "28988", "rss": "6236", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:01", "command": "/lib/systemd/systemd-journald"},
            {"pid": "267", "user": "root", "cpu": "0.0", "mem": "0.0", "vsz": "22856", "rss": "3968", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:00", "command": "/lib/systemd/systemd-udevd"},
            {"pid": "387", "user": "systemd+", "cpu": "0.0", "mem": "0.1", "vsz": "18664", "rss": "3148", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:00", "command": "/lib/systemd/systemd-resolved"},
            {"pid": "389", "user": "systemd+", "cpu": "0.0", "mem": "0.0", "vsz": "8680", "rss": "2608", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:00", "command": "/lib/systemd/systemd-timesyncd"},
            {"pid": "419", "user": "root", "cpu": "0.0", "mem": "0.0", "vsz": "16124", "rss": "2088", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:00", "command": "/usr/sbin/cron -f"},
            {"pid": "421", "user": "root", "cpu": "0.0", "mem": "0.1", "vsz": "16756", "rss": "2920", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:00",
             "command": "/usr/bin/dbus-daemon --system --address=systemd:"},
            {"pid": "425", "user": "message+", "cpu": "0.0", "mem": "0.0", "vsz": "9460", "rss": "2272", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:00",
             "command": "/usr/bin/dbus-daemon --session --address=systemd:"},
            {"pid": "428", "user": "syslog", "cpu": "0.0", "mem": "0.0", "vsz": "30104", "rss": "2552", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:00", "command": "/usr/sbin/rsyslogd -n -iNONE"},
            {"pid": "430", "user": "root", "cpu": "0.0", "mem": "0.1", "vsz": "31320", "rss": "4628", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:00", "command": "/lib/systemd/systemd-logind"},
            {"pid": "434", "user": "root", "cpu": "0.0", "mem": "0.1", "vsz": "395712", "rss": "8620", "tty": "?",
             "stat": "Ssl", "start": "Apr01", "time": "0:00", "command": "/usr/sbin/NetworkManager --no-daemon"},
            {"pid": "451", "user": "root", "cpu": "0.0", "mem": "0.0", "vsz": "72248", "rss": "3640", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:00", "command": "/usr/sbin/sshd -D"},
            {"pid": "474", "user": "mysql", "cpu": "0.1", "mem": "2.4", "vsz": "1588796", "rss": "98288", "tty": "?",
             "stat": "Ssl", "start": "Apr01", "time": "0:29", "command": "/usr/sbin/mysqld"},
            {"pid": "492", "user": "root", "cpu": "0.0", "mem": "0.1", "vsz": "108024", "rss": "4968", "tty": "?",
             "stat": "Ss", "start": "Apr01", "time": "0:00", "command": "/usr/sbin/apache2 -k start"},
            {"pid": "493", "user": "www-data", "cpu": "0.0", "mem": "0.1", "vsz": "108052", "rss": "2656", "tty": "?",
             "stat": "S", "start": "Apr01", "time": "0:00", "command": "/usr/sbin/apache2 -k start"},
            {"pid": "494", "user": "www-data", "cpu": "0.0", "mem": "0.1", "vsz": "108052", "rss": "2656", "tty": "?",
             "stat": "S", "start": "Apr01", "time": "0:00", "command": "/usr/sbin/apache2 -k start"},
            {"pid": "496", "user": "www-data", "cpu": "0.0", "mem": "0.1", "vsz": "108052", "rss": "2656", "tty": "?",
             "stat": "S", "start": "Apr01", "time": "0:00", "command": "/usr/sbin/apache2 -k start"},
            {"pid": "1021", "user": "root", "cpu": "0.0", "mem": "0.0", "vsz": "16788", "rss": "2356", "tty": "tty1",
             "stat": "Ss+", "start": "Apr01", "time": "0:00",
             "command": "/sbin/agetty -o -p -- \\u --noclear tty1 linux"},
            {"pid": "1033", "user": "user", "cpu": "0.0", "mem": "0.1", "vsz": "13136", "rss": "5412", "tty": "pts/0",
             "stat": "Ss", "start": f"{datetime.datetime.now().strftime('%H:%M')}", "time": "0:00", "command": "-bash"},
            {"pid": "1485", "user": "user", "cpu": "0.0", "mem": "0.0", "vsz": "10652", "rss": "3076", "tty": "pts/0",
             "stat": "R+", "start": f"{datetime.datetime.now().strftime('%H:%M')}", "time": "0:00",
             "command": "ps " + " ".join(args)}
        ]

        # Only show user's own processes unless -a or -e is specified
        if not show_all:
            processes = [p for p in processes if p["tty"] != "?" or p["user"] == username]

        # Format output based on options
        if show_full:
            # Full format
            header = "UID        PID  PPID  C STIME TTY          TIME CMD"
            format_string = "{:<8} {:>5} {:>5}  {:1} {:>5} {:<8} {:>8} {}"

            result = [header]
            for p in processes:
                # Add PPID field for full format
                ppid = "1" if p["pid"] != "1" else "0"
                if int(p["pid"]) > 400 and int(p["pid"]) < 500:
                    ppid = "387"  # Make systemd processes children of systemd

                result.append(format_string.format(
                    p["user"], p["pid"], ppid, "0", p["start"], p["tty"], p["time"], p["command"]
                ))
        else:
            # Standard format
            header = "  PID TTY          TIME CMD"
            format_string = "{:>5} {:<8} {:>8} {}"

            result = [header]
            for p in processes:
                result.append(format_string.format(
                    p["pid"], p["tty"], p["time"], p["command"]
                ))

        return "\r\n".join(result)

    elif cmd == "find":
        # Basic implementation of find command
        if not args:
            return "find: missing path operand"

        path = args[0]

        # Default to current directory if no path specified
        if path == ".":
            path = fs.current_dir

        # Parse options and search criteria
        name_pattern = None
        type_filter = None

        i = 1
        while i < len(args):
            if args[i] == "-name" and i + 1 < len(args):
                # Handle wildcard patterns by converting to simple substring matching
                name_pattern = args[i + 1].replace("*", "").replace('"', '').replace("'", '')
                i += 2
            elif args[i] == "-type" and i + 1 < len(args):
                type_filter = args[i + 1]  # 'f' for files, 'd' for directories
                i += 2
            else:
                i += 1

        # Recursive function to build the result list
        def find_items(current_path, current_item):
            results = []

            # Always add current path to results unless filtering
            should_add = True

            # Apply name filter if specified
            if name_pattern and name_pattern not in os.path.basename(current_path):
                should_add = False

            # Apply type filter if specified
            if type_filter:
                if type_filter == 'f' and current_item["type"] != "file":
                    should_add = False
                elif type_filter == 'd' and current_item["type"] != "dir":
                    should_add = False

            if should_add:
                results.append(current_path)

            # Recursively search directories
            if current_item["type"] == "dir":
                for name, item in current_item["contents"].items():
                    child_path = os.path.join(current_path, name)
                    results.extend(find_items(child_path, item))

            return results

        # Start the search
        resolved_path = fs.resolve_path(path)
        search_item = fs.get_item_at_path(resolved_path)

        if search_item is None:
            return f"find: '{path}': No such file or directory"

        results = find_items(resolved_path, search_item)

        # Sort results for consistent output
        results.sort()

        return "\n".join(results)

    elif cmd == "who":
        # Show both a local user and the current SSH connection
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        # Use fixed-width format specifiers for precise column alignment
        format_string = "{:<12} {:<9} {:<17} {}"

        local_user = format_string.format("user", "tty1", current_time, "(:0)\r\n")
        ssh_connection = format_string.format(username, "pts/0", current_time, f"({addr[0]})\r\n")

        return local_user + "\n" + ssh_connection

    elif cmd == "ls":
        path = args[0] if args else None
        return fs.list_directory(path)

    elif cmd == "cd":
        path = args[0] if args else "/home/user"
        return fs.change_directory(path)

    elif cmd == "pwd":
        return fs.get_current_directory()

    elif cmd == "mkdir":
        if not args:
            return "mkdir: missing operand"
        return fs.create_directory(args[0])

    elif cmd == "touch":
        if not args:
            return "touch: missing file operand"
        return fs.create_file(args[0])

    elif cmd == "rm":
        if not args:
            return "rm: missing operand"

        recursive = "-r" in args or "-rf" in args or "--recursive" in args
        if recursive:
            args = [arg for arg in args if arg not in ["-r", "-rf", "--recursive"]]

        if not args:
            return "rm: missing operand"

        return fs.remove_item(args[0], recursive)


    elif cmd == "grep":
        if len(args) < 1:
            return "grep: missing pattern operand"

        recursive = False
        if "-r" in args or "-R" in args:
            recursive = True
            args = [arg for arg in args if arg not in ["-r", "-R"]]

        if len(args) < 1:
            return "grep: missing pattern operand"

        pattern = args[0]
        path = args[1] if len(args) > 1 else None
        return fs.grep_file(pattern, path, recursive)

    elif cmd == "clear":
        return "\033[H\033[J"  # ANSI escape sequence to clear screen

    # elif cmd == "cat":
    #     if not args:
    #         return "cat: missing file operand"
    #
    #     path = args[0]
    #     resolved_path = fs.resolve_path(path)
    #     item = fs.get_item_at_path(resolved_path)
    #
    #     if item is None:
    #         return f"cat: {path}: No such file or directory"
    #
    #     if item["type"] == "dir":
    #         return f"cat: {path}: Is a directory"
    #
    #     return item["contents"]
    #
    # else:
    #     return f"{cmd}: command not found"

    elif cmd == "cat":
        if not args:
            return "cat: missing file operand"

        path = args[0]
        resolved_path = fs.resolve_path(path)
        item = fs.get_item_at_path(resolved_path)

        if item is None:
            return f"cat: {path}: No such file or directory"

        if item["type"] == "dir":
            return f"cat: {path}: Is a directory"

        # Check if this is a password-protected file
        if "password_protected" in item and item["password_protected"]:
            if len(args) > 1 and args[1] == item["password"]:
                # Correct password provided as argument
                return item["contents"]
            else:
                # No password or incorrect password
                return "This file is encrypted or password protected.\r\nUsage: cat <filename> <password>"

        # Regular non-protected file
        return item["contents"].replace('\n', '\r\n')


def main():
    """Main function to start the honeypot server."""
    parser = argparse.ArgumentParser(description='SSH Honeypot Server')
    parser.add_argument('--port', type=int, default=22, help='Port to listen on')
    parser.add_argument('--bind', default='0.0.0.0', help='Address to bind to')
    args = parser.parse_args()

    # Create server key if it doesn't exist
    create_server_key()

    # Set up the server socket
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((args.bind, args.port))
        sock.listen(100)
        logger.info(f"SSH honeypot server listening on {args.bind}:{args.port}")

        # Accept and handle connections
        while True:
            client, addr = sock.accept()
            logger.info(f"Connection from {addr}")
            Thread(target=handle_connection, args=(client, addr)).start()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        sock.close()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        sock.close()


if __name__ == "__main__":
    main()


# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.







