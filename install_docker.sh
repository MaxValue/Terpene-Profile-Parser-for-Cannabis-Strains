#!/usr/bin/env bash

sudo apt-get remove docker docker-engine docker.io containerd runc docker-compose
sudo apt-get update
sudo apt-get --assume-yes install \
	apt-transport-https \
	ca-certificates \
	curl \
	gnupg-agent \
	software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
# sudo apt-key fingerprint 0EBFCD88
# 9DC8 5822 9FC7 DD38 854A E2D8 8D81 803C 0EBF CD88
sudo add-apt-repository \
	"deb [arch=amd64] https://download.docker.com/linux/ubuntu \
	$(lsb_release -cs) \
	stable"
sudo apt-get update
sudo apt-get --assume-yes install docker-ce docker-ce-cli containerd.io
sudo groupadd docker
sudo gpasswd -a $USER docker
newgrp docker
