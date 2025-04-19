#!/bin/bash -xe
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# Install EFS utils
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
sudo apt install libgl1-mesa-glx libxi6 libxrender1

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Install blender-on-aws
cd /mnt/efs
git clone ${github_repo}

# Run blender-on-aws
cd blender-on-aws
uv run ./run.sh &
