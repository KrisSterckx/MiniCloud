#! /bin/bash

# check for gcc being installed
gcc_out=`gcc --version | grep "Free Software Foundation"`
if [[ ! $gcc_out ]]; then
    echo Please install gcc first.
    exit 1
fi

# libs
pip install argparse

# python-dev
apt-cyg install python-pip python-devel libffi-devel libxml2-devel

# openstack clients
pip install python-openstackclient
pip install python-neutronclient

# mysql and dataset
apt-cyg update
apt-cyg install python-devel
apt-cyg install mysql-server
apt-cyg install libmysqlclient-devel

pip install pymysql
pip install dataset

# paramiko
# pip install paramiko

# when mysql db is run on this node, may consider giving :
# mysql_install_db
# mysqld_safe &
# mysql_secure_installation
