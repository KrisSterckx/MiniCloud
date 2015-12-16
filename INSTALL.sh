#! /bin/bash

# libs
sudo -E pip install argparse

# openstack clients
sudo -E pip install python-openstackclient
sudo -E pip install python-neutronclient

# mysql and dataset
sudo apt-get install mysql-server
sudo -E pip install pymysql
sudo -E pip install dataset

# paramiko
sudo apt-get update && sudo apt-get install libssl-dev
sudo -E pip install paramiko
