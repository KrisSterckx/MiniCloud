#! /bin/bash

if [ -f minicloud.rc ]; then
    source minicloud.rc
else
    if [ -d /opt/stack ]; then
        version=$(cd /opt/stack/neutron; git rev-parse --abbrev-ref HEAD | grep -oE "[a-z]*$")

        export OS_DEPLOYMENT_NAME=DevStack
        export OS_DEPLOYMENT_TYPE=OpenStack
        export OS_DEPLOYMENT_VERSION=${version^}
        export OS_DEPLOYMENT_LOCATION=localhost
    fi

    source minicloud.rc.sample
fi

python main.py $@
