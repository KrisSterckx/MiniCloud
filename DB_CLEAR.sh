#! /bin/bash

echo "Clearing MiniCloud database..."
if [[ $SQL_PASSWORD ]]; then
        mysql -u root --password=$SQL_PASSWORD < CLEAR.SQL
else
        echo "Enter the mysql password below:"
        mysql -u root -p < CLEAR.SQL
fi

echo "Finished."
