For runnint at start as a service
Place .service file in:
/etc/systemd/system/nodes-stack.service

Enable at start
sudo systemctl daemon-reload
sudo systemctl enable nodes-stack
sudo systemctl start nodes-stack


backups

docker exec nodes-db sh -c 'exec mysqldump -u${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME}' > /srv/backups/nodesdb_$(date +%F).sql