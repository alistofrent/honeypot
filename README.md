This project includes two variations of a honeypot. The first uses the Python package Paramiko and creates a fake file system for an SSH-connected 'attacker' to browse through. The files, folders, and file content don't actually exist but are faked inside the Python code. The second version creates an Ubuntu docker container whenever an SSH connection is initiated, then connects the 'attacker' to the docker image.

Make sure to install any packages your system doesn't have from the import section(s).

**SSH Fake File System**

You will need to install the paramiko package for this to work.

Run the script using the command:
sudo python3 linux_ssh_backdoor.py

Note that it will run on port 22 by default.

Connect using the command:
ssh user@[IP_ADDRESS] -p 22

The default credentials are username: "user" and password: "Password"

The available commands are:
ls
cd
pwd
mkdir
touch
rm
grep -r
cat
clear
who
uname -a, -s, -n, -r, -v, -m, -p, -i, -o
find
ps
netstat -a, -t, -u, -x, -p, -n, -l, -r
exit/logout
?


**SSH Docker Proxy**

You will need to install the psutil and shutil packages for this to work.

The docker image will be created with the following credentials:
User - uname: 'user', password 'userpassword'
Admin - uname: 'root', password 'changeme'

Start the python script using the command:
sudo python3 ssh_docker_spawn.py

Connect using the command:
ssh -o StrictHostKeyChecking=accept-new -p 2222 user@[IP_ADDRESS]
Note that StrictHostKeyChecking=accept-new is needed for a successful connection, as otherwise there can security check issues.
