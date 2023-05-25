./services.sh stop
cp net_balancer-main/src/cache.json              .
mv net_balancer-main/src/energy_mediator.db      .
mv net_balancer-main/src/output/measurements.csv .
rm -rf net_balancer-main
curl -L https://github.com/HansKappert/net_balancer/archive/refs/heads/main.zip > latest.zip
# curl -L https://github.com/HansKappert/net_balancer/archive/refs/heads/dev.zip > latest.zip
unzip -o latest.zip -d -q .
# If using dev branch, then uncomment the following
# mv net_balancer-dev net_balancer-main
rm latest.zip
cp cache.json net_balancer-main/src/
mv energy_mediator.db net_balancer-main/src/
mkdir net_balancer-main/src/output
mv measurements.csv net_balancer-main/src/output/
sudo journalctl --rotate
./services.sh start

