# How to use this project:

1. Clone this project to your PC. 
   
   ```git clone git@ibg3repo.ibg.kfa-juelich.de:t.korf/clisos-pynodered.git```
2. Install Docker (https://www.docker.com/get-started)
3. Login to Gitlab Server:

   ```docker login ibg3repo.ibg.kfa-juelich.de:5000```
4. To start the container execute:

   ```docker run --rm -it --name pynodered -v path/to/project:/data -p 127.0.0.1:1880:1880 ibg3repo.ibg.kfa-juelich.de:5000/t.korf/clisos-pynodered:latest```

5. Open `localhost:1880` in your browser
   


For Debugging use the following command:

   ```docker logs -f pynodered```


When updating the requirements.txt file you need to restart the docker container:

   ```docker restart pynodered```