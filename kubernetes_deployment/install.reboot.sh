##### Install Docker ######
# Mount the SSD storage
mkdir -p /mnt/sda
mount /dev/sda /mnt/sda

# Persist Docker data
mkdir -p /mnt/sda/docker
mkdir -p /var/lib/docker
mount --rbind /mnt/sda/docker /var/lib/docker

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
# Add the repository to Apt sources and install
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Run Docker on RAMDISK mode
mkdir -p /etc/systemd/system/docker.service.d
cat >/etc/systemd/system/docker.service.d/10-ramdisk.conf <<EOF
[Service]
Environment=DOCKER_RAMDISK=true
EOF
systemctl daemon-reload
systemctl restart docker

##### Install K3S and Helm ######
# Persist K3S data
mkdir -p /mnt/sda/data-pipeline/k3s
mkdir -p /var/lib/rancher/k3s
mount --rbind /mnt/sda/data-pipeline/k3s /var/lib/rancher/k3s 

# Install K3S
sudo apt update
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--docker" sh -s - --disable traefik

## Run K3S on RAMDISK mode
sudo mkdir -p /etc/systemd/system/k3s.service.d
sudo tee /etc/systemd/system/k3s.service.d/10-ramdisk.conf > /dev/null <<EOF
[Service]
Environment=DOCKER_RAMDISK=true
EOF
sudo systemctl daemon-reload
sudo systemctl restart k3s

# Add KUBECONFIG to the path
if ! grep -q 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' ~/.bashrc; then
    # Append the export command to .bashrc
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
    echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc
    echo 'KUBECONFIG export added to .bashrc'
    sudo chown $(id -u):$(id -g) /etc/rancher/k3s/k3s.yaml
else
    echo 'KUBECONFIG export already exists in .bashrc'
fi

# Install helm
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
sudo apt-get install apt-transport-https --yes
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm

##### Connect to NFS Storage  #####
# Prepare network VLAN connection for NFS
sudo ip link set dev eno4 up
sudo ip addr add 192.168.242.12/24 dev eno4

# Mount NFS to the machine
apt install nfs-common
echo "192.168.242.1:/pipeline_minio_data  /mnt/pipeline_minio_data nfs4 _netdev,rw,rsize=16384,wsize=16384 0 0" | sudo tee -a /etc/fstab
mkdir -p /mnt/pipeline_minio_data
mount /mnt/pipeline_minio_data

##### Define Public IP #####

ip link set eno6 up
sudo ip addr add <IP_ADDRESS_OF_NODE>/25 dev eno6
sudo ip route add default via <IP_ADDRESS_OF_NODE> dev eno6