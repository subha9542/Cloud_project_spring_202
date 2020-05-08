+--------------------------------------+
	Program: The Analyzer
	Cloud Computing Project
	Group-2:
		Alex Garcia, Shawn Saltsman, Subash Sunku
	Description:  
		Take Stock datasets from Kaggle and evaluate the data for trends during a pandemic.
		Two pandemic chosen: H1N1 2009-2010 and CVOID-19 12/20 to Present day.  
		The project initially started with the containerized version but then moved the a VM MPI only solution.
+--------------------------------------+

		****************************
		*	Containerized version: *
		****************************
		Works until python tries to download and store to the filesystem the dataset files.  Receiving permission denied.
		This version is executed via script.sh
		
		Application Location:
		cc server:  cc@129.114.27.12   	pw: clearlab2
		Path: /home/cloud_application/the_analyzer/app
			
			/app/
			    dockerfile
				docker-compose.yml
				kaggle/
				mpi4py_benchmarks/
				myhostfile
				requirements.txt
				script.sh
				ssh/				 
				workdir/
				
		To run the containerized version with auto execute of file (see below for contents):
		
		sudo bash ./script.sh
		
		Description: Script will remove myhostfile, bring down containers, build continers, pull ip address and rebuild the hostfile
		and execute the python code.
		
		********************************
		Local Version - cc networking issues and code needed to be modified
		********************************
                 execute bash vmscript.sh

		********************************
		*	Non-Containerized version: *
		********************************
		Can executed on the cc server without docker but utilizing the hostfile, this is executed in the mpiuser vm
		
		Application Location:
		mpi server: mpiuser@129.114.25.48  pw: mpi
		
		These machines have been updated with docker but later dismissed, but added Kaggle, mpiuser/.kaggle  for the key, python3 numpy, pandas, and matplotlib.
		All machines in the hostfile have also been updated to be identical.
		
		code is placed under code/ directory
		
		Execution:
		mpirun -np # --hostfile ./code/data_retrieve.py
		
		
		***********************
		*	Script Contents	  *
		***********************
		#!/bin/sh

		sudo rm ./myhostfile

		docker-compose down

		docker-compose up -d --scale mpi_node=4 --build

		docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps -aq) | grep -E -o '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)' > myhostfile

		while IFS="" read -r ip || [ -n "$p" ]
		do
		  scp -o StrictHostKeyChecking=no -i ./ssh/id_rsa.mpi kaggle/rest.py  kaggleuser@$ip:/home/kaggleuser/.local/lib/python3.6/site-packages/kaggle/rest.py
		done < myhostfile

		master=$(head -n 1 myhostfile)

		echo "$(tail -n +2 myhostfile)" > myhostfile

		scp -o StrictHostKeyChecking=no -i ./ssh/id_rsa.mpi myhostfile kaggleuser@$master:/home/kaggleuser/myhostfile

		docker-compose exec --user kaggleuser --privileged analyzer_run mpirun -np 4 --hostfile /home/kaggleuser/myhostfile python3 /home/kaggleuser/workdir/data_retrieve.py


		************************
		*  End Script Contents *
		************************
		
		
		************************
		* SSH into Containers  *
		************************
		From the app/ directiory:
		
		ssh -i ./ssh/id_rsa.mpi  kaggleuser@continer_ip_address
		
		container_ip_address can be pulled from the myhostfile after a successful build.
		
		The master ip can be obtained from executing the following:
		
		docker ps -q | xargs -n 1 docker inspect --format '{{ .Name }} {{range .NetworkSettings.Networks}} {{.IPAddress}}{{end}}' | sed 's#^/##' | grep "analyzer"
		
