#! /bin/bash

if [[ $WINDIR ]]; then
	mysqld_running=`ps | grep mysqld`

	if [[ ! $mysqld_running ]]; then
		echo "Starting mysqld..."
		mysqld_safe 1>/dev/null&
		sleep 10
		echo "Shutdown with: mysqladmin -u root -p shutdown"
		echo "Your SQL password is: password"
		export SQL_PASSWORD=password
	fi
fi
echo "Setting up MiniCloud database..."
if [[ $SQL_PASSWORD ]]; then
	mysql -u root --password=$SQL_PASSWORD < SETUP.SQL
else
        echo "Enter the mysql password below:"
        mysql -u root -p < SETUP.SQL
fi
echo "Finished."
