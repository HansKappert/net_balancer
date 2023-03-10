sudo systemctl daemon-reload
sudo systemctl $1 energynet-balancer.service
sudo systemctl $1 energynet-balancer-web.service

