# This dockerfile specifies containers that can be used for testing of IP-based multiplayer games
# Drawing visualisation power from https://stackoverflow.com/questions/16296753/can-you-run-gui-applications-in-a-docker-container
FROM python:3.8

# Make sure the package repository is up to date
RUN     echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list
RUN     apt-get update

# Install vnc, xvfb in order to create a 'fake' display
## These applications are likely to update less frequently than the game's codebase and python dependencies, so we having them first should improve caching
RUN     apt-get install -y x11vnc xvfb
RUN     mkdir ~/.vnc
# Setup a password
RUN     x11vnc -storepasswd 1234 ~/.vnc/passwd

# Bring in game files from the parent file system
COPY . ../cartolan_sim
WORKDIR ../cartolan_sim

# Install python packages based on the codebase
RUN pip install --upgrade pip && \
    pip install invoke && \ 
    invoke install-dependencies

# Launch the network multiplayer version of Cartolan
