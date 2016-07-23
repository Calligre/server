#!/bin/bash
sudo apt-get -y update
sudo apt-get -y install curl mongodb

curl https://raw.githubusercontent.com/creationix/nvm/master/install.sh | sh
source /home/ubuntu/.nvm/nvm.sh
nvm install 0.10.43
nvm use 0.10.43

npm -g install npm@latest

curl https://install.meteor.com/ | sh

cd /home/ubuntu/alpha
npm install --production
meteor build ./build
tar xzf build/alpha.tar.gz

cd bundle/programs/server
npm install

cd /home/ubuntu/alpha/bundle
npm install -g forever
PATH="/home/ubuntu/.nvm/v0.10.43/bin:$PATH" PORT=3000 MONGO_URL=mongodb://localhost:27017/alpha ROOT_URL=http://alpha.calligre.com forever start main.js
