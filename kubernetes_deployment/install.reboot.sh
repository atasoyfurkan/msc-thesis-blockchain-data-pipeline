##### Install Docker ######
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
