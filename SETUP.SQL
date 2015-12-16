CREATE DATABASE minicloud;
CREATE USER 'minicloud'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON minicloud.* to 'minicloud'@'localhost';
FLUSH PRIVILEGES;
