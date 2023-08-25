sudo cp energynet-balancer-web.service /etc/systemd/system
sudo cp energynet-balancer.service /etc/systemd/system
curl -L https://github.com/HansKappert/net_balancer/archive/refs/heads/main.zip > latest.zip
unzip -o latest.zip -d .
rm latest.zip
sudo apt-get update
sudo apt-get install -y python3-pip
sudo apt-get install -y python3-venv
python3 -m venv venv
source venv/bin/activate
cd ~/net_balancer-main
pip3 install -r requirements.txt
sudo systemctl daemon-reload
