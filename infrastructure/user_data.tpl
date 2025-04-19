#!/bin/bash -xe
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# Install EFS utils
sudo apt update -y
sudo apt-get update
sudo apt-get -y install git binutils rustc cargo pkg-config libssl-dev gettext
git clone https://github.com/aws/efs-utils
cd efs-utils
./build-deb.sh
sudo apt-get -y install ./build/amazon-efs-utils*deb

# Mount EFS on instance
sudo mkdir -p /mnt/efs
sudo mount -t efs ${efs_id}:/ /mnt/efs
echo "${efs_id}:/ /mnt/efs efs defaults,_netdev 0 0" >> /etc/fstab

# Install blender
sudo snap install blender --classic
sudo apt install -y libgl1-mesa-glx libxi6 libxrender1 libegl1

# Install ffmpeg
sudo apt install -y ffmpeg

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Install blender-on-aws
cd /mnt/efs
if [ ! -d "blender-on-aws" ]; then
  git clone ${github_repo}
else
  echo "Repository already exists, skipping clone"
fi

# Start blender-on-aws as daemon
cd blender-on-aws
export UV_PATH=$(which uv)
export BLENDER_SERVER_ROOT=$(pwd)
sudo envsubst < manifests/blender-server.service > /etc/systemd/system/blender-server.service
sudo systemctl daemon-reload
sudo systemctl enable blender-server
sudo systemctl start blender-server
