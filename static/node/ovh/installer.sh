#!/bin/sh
#Install and configure a Tor Exit Node

echo "Add Tor repository"
cat >> /etc/apt/sources.list << 'EOF'
# Tor repository
deb http://deb.torproject.org/torproject.org wheezy main
deb-src http://deb.torproject.org/torproject.org wheezy main
EOF
echo "Add the Tor public key"
gpg --keyserver keys.gnupg.net --recv 886DDD89
gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | sudo apt-key add -
echo "update, upgrade and install"
apt-get update
apt-get -y upgrade
apt-get -y install deb.torproject.org-keyring
echo "install iftop"
apt-get -y install iftop
echo "install htop"
apt-get -y install htop
echo "install Tor"
apt-get -y install tor

echo "Configure the Tor Router"
wget https://www.ahmia.fi/IP/ -O IP.txt
wget https://www.ahmia.fi/static/node/our_exit_policy -O /etc/tor/torrc
wget https://www.ahmia.fi/static/node/tor-exit-notice.html -O /etc/tor/tor-exit-notice.html
sed -i "s,ahmiaTorNode1,ahmiaTOR$(hostname),g" /etc/tor/torrc
sed -i "s,SET_IP_ADDRESS_HERE,$( cat IP.txt ),g" /etc/tor/torrc

echo "security measures"
invoke-rc.d nfs-common stop
invoke-rc.d rpcbind stop
update-rc.d -f nfs-common remove
update-rc.d -f rpcbind remove
echo "Starting the Exit Relay"
/etc/init.d/tor start
sleep 300 && invoke-rc.d tor restart > /dev/null 2>&1 &
echo "Running now"
