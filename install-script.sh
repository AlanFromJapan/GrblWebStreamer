#!/bin/bash
echo "#################################################################"
echo "##                                                             ##"
echo "##  GRBL WebStreamer                                           ##"
echo "##  Installer script, run me once only, should do the whole    ##"
echo "##  job on Raspberry Pi. If not, enjoy troubleshooting.        ##"
echo "##                                                             ##"
echo "##  (You should do an apt update/upgrade before)               ##"
echo "##                                                             ##"
echo "#################################################################"

echo "Proceed with installation?"
read -n1 -s -r -p $'Press any key to continue or Ctrl+C now to stop...\n' key

echo "#################################################################"
echo "Installing dependencies..."
echo "#################################################################"

sudo apt install git python3 python3-pip python3-venv libopenjp2-7 --yes
#get the prebuilt version of flask otherwise there's rust build to do
sudo apt install python3-flask python3-serial --yes

echo "#################################################################"
echo "Creating folders and downloading GrblWebStreamer..."
echo "#################################################################"

mkdir GrblWebStreamer.venv
cd GrblWebStreamer.venv
git clone https://github.com/AlanFromJapan/GrblWebStreamer.git
python3 -m venv --system-site-packages .
source bin/activate
python -m pip install -r ./GrblWebStreamer/requirements.txt

echo "#################################################################"
echo "Creating log folder..."
echo "#################################################################"

sudo mkdir -p /var/local/GrblWebStreamer/logs
sudo mkdir -p /var/local/GrblWebStreamer/uploads
sudo mkdir -p /var/local/GrblWebStreamer/db
sudo chgrp -R pi /var/local/GrblWebStreamer
sudo chmod -R g+rw /var/local/GrblWebStreamer

echo "#################################################################"
echo "Now you work (do nothing mode)..."
echo "#################################################################"

echo "Copy the config.sample.py to config.py and edit it to your needs."
read -n1 -s -r -p $'Press any key to continue ...\n' key

echo "Register the script to run at boot time:"
echo "edit /etc/rc.local and add the following line before the exit 0:"
#runs the venv version of python with the proper packages
echo "/home/pi/GrblWebStreamer.venv/bin/python /home/pi/GrblWebStreamer.venv/GrblWebStreamer/start-service.sh &"
read -n1 -s -r -p $'Press any key to continue ...\n' key


echo "#################################################################"
echo "Should be all good but I will add port mapping (http -> your port assuming it's 12380)"
echo ""
echo ">> if you don't want that, Ctrl+C now, the following is optional"
echo "#################################################################"

read -p "Do you want to proceed with port mapping? (yes/no) " yn

case $yn in 
	yes ) echo ok, we will proceed;;
	no ) echo exiting...;
		exit;;
	* ) echo invalid response;
		exit 1;;
esac


sudo apt install iptables --yes

#All TCP traffic from all interfaces from outside to port 80 redirected to 12380
sudo iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-port 12380

#doing like that so you use the "save on install" feature of iptables-persistent
sudo apt install  iptables-persistent --yes

echo "#################################################################"
echo "That should be finished, reboot and cross your fingers..."

exit 0
