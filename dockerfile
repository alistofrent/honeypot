FROM ubuntu:22.04

# Install SSH server and necessary packages
RUN apt-get update && apt-get install -y \
    openssh-server \
    python3 \
    vim \
    curl \
    iputils-ping \
    net-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure SSH
RUN mkdir /var/run/sshd
RUN mkdir /root/.ssh

# Set root password - only for initial setup, you'll want to switch to key-based auth
RUN echo 'root:changeme' | chpasswd

# Configure SSH server
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# SSH login fix
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

# Create a non-root user (recommended for security)
RUN useradd -m -s /bin/bash user
RUN echo 'user:userpassword' | chpasswd

# Setup for key-based authentication (recommended)
RUN mkdir -p /home/user/.ssh
RUN chown user:user /home/user/.ssh
RUN chmod 700 /home/user/.ssh

RUN echo 'export PROMPT_COMMAND="history -a; logger -t user-command \"\$(history 1 | sed -e \"s/^[ ]*[0-9]*[ ]*//\")\""' >> /home/user/ssh-log.bashrc


# Add flag file
RUN echo "This is your flag: FLAG{ssh_docker_challenge_completed}" > /home/user/flag.txt
RUN chown user:user /home/user/flag.txt

# Expose SSH port
EXPOSE 22

# Start SSH server
CMD ["/usr/sbin/sshd", "-D"]

