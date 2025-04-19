#!/bin/bash
yum update -y
yum install -y amazon-efs-utils
mkdir -p /mnt/efs
mount -t efs ${efs_id}:/ /mnt/efs
echo "${efs_id}:/ /mnt/efs efs defaults,_netdev 0 0" >> /etc/fstab

sudo snap install blender --classic
sudo apt install libgl1-mesa-glx libxi6 libxrender1
${additional_user_data}
