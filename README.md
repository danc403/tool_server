# This repository provides a secure, sandboxed bridge between your Local LLM (Large Language Model) and the local tools it needs to perform web searches, database queries, and file management.

# By using Docker, we ensure that the model stays contained within a "Safe Zone," preventing any accidental changes to your host operating system.

# Repository Structure

# • 

# tool\_server.py: The main API bridge.

# • 

# tools/: A directory containing individual Python scripts for various tasks.

# • 

# sandbox/: The ONLY folder the AI is allowed to write files to.

# • 

# idg-tool-server.tar: The pre-built Linux environment (Debian 13 + Python 3.13).

# • 

# Dockerfile \& requirements.txt: Source files used to build the image environment.

# &#x20;

# Quick Start Guide

# Follow these steps to get the tool server running on your machine.

# 1\. Import the Environment

# Before running the server, you must load the frozen environment into Docker. Open your terminal in this directory and run:

# docker load -i idg-tool-server.tar

# 2\. Launch the Tool Server

# Run the following command to start the server. This maps your local code and the sandbox folder into the container.

# Note: Replace C:\\path\\to\\repo with the actual path to this folder on your computer.

# Bash

# docker run -d \\

# &#x20; --name idg-tool-server \\

# &#x20; -p 8080:8080 \\

# &#x20; -v "C:\\path\\to\\repo":/app \\

# &#x20; -v "C:\\path\\to\\repo\\sandbox":/app/sandbox \\

# &#x20; --cap-drop=ALL \\

# &#x20; idg-tool-server

# 

# 3\. Verify Connection

# To ensure the bridge is active, you can test it via your browser or a terminal command:

# curl http://localhost:8080/status

# If you receive a "Server Online" message, the bridge is ready to receive tool calls from your model.

# &#x20;

# Developer Notes

# Live Debugging

# Because we are mounting the repository as a volume, you can edit tool\_server.py or any script in the tools/ folder using your preferred text editor. The changes will be visible to the container immediately.

# Security

# • 

# Capabilities: The --cap-drop=ALL flag ensures the container has no administrative power over your machine.

# • 

# Isolation: The AI is restricted to the /app/sandbox directory. Do not store sensitive files outside of this folder if you intend for the model to interact with them.

# Shutdown

# To stop the server and free up system resources:

# docker stop idg-tool-server

# To start it again later, simply run docker start idg-tool-server.

# Bloat Control \& Rebuilding

# If you need to change requirements.txt or the Dockerfile, you must "nuke" the old build layers to prevent the image size from ballooning. Use this specific workflow to keep the image lean:

# 1\. 

# Stop and Remove Instance: docker rm -f idg-tool-server

# 2\. 

# Remove the Image: docker rmi idg-tool-server

# 3\. 

# Clear Build Cache: docker builder prune -a (Type 'y' to confirm)

# 4\. 

# Fresh Build: docker build -t idg-tool-server .

# 5\. 

# Export New Tar: docker save -o idg-tool-server.tar idg-tool-server

# 



