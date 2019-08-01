# How to build crosswalk with GB Solutions' camera flash enhancement?

## 1) Install a virtualized Ubuntu 16.04.6 LTS in VirtualBox

Recommended configuration: 100 GB HDD, 8 GB RAM with at least 4 CPU cores
After installation is completed, it is recommended to install Guest Additions features as well.

### 1a) Upgrade the default swap space to 10 GB according to this tutorial: https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-ubuntu-16-04

```bash
sudo swapon --show # Check current swap size
sudo fallocate -l 10G /swapfile # Create new swap file
sudo chmod 600 /swapfile # Set permissions
sudo mkswap /swapfile # Mark swap file as swap space
sudo swapon /swapfile # Enable swap file
sudo swapon --show # Check new swap size
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab # Make swap settings permanent
```
### 1b) Install Git and Depot tools

```bash
sudo apt-get install git # Install Git
mkdir ~/devtools # Create directory for devtools
cd ~/devtools # Open devtools directory
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git # Clone the master brach of depot tools
export PATH="/home/{username}/devtools/depot_tools:$PATH" # Add depot tools to the PATH
cd ~ # Open home directory
```
## 2) Checkout the source and apply GB Solutions' camera flash enhancement

```bash
mkdir crosswalk-checkout # Create directory for checkout
cd crosswalk-checkout/ # Open checkout directory
export XWALK_OS_ANDROID=1 # Set environment variable for android build
gclient config --name src/xwalk https://github.com/gb-solutions/crosswalk.git # Configure gclient
echo "target_os = [ 'android' ]" >> .gclient # Set target os in configuration file
gclient sync # Start downloading dependencies
```

