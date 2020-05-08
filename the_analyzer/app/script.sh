#!/bin/sh

sudo rm ./myhostfile

docker-compose down

docker-compose up -d --scale mpi_node=4 --build

docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps -aq) | grep -E -o '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)' > myhostfile

while IFS="" read -r ip || [ -n "$p" ]
do
  scp -o StrictHostKeyChecking=no -i ./ssh/id_rsa.mpi .kaggle/rest.py  kaggleuser@$ip:/home/kaggleuser/.local/lib/python3.6/site-packages/kaggle/rest.py
done < myhostfile

master=$(head -n 1 myhostfile)

echo "$(tail -n +2 myhostfile)" > myhostfile

scp -o StrictHostKeyChecking=no -i ./ssh/id_rsa.mpi myhostfile kaggleuser@$master:/home/kaggleuser/myhostfile

docker-compose exec --user kaggleuser --privileged analyzer_run mpirun -np 4 --hostfile /home/kaggleuser/myhostfile python3 /home/kaggleuser/workdir/data_retrieve.py

