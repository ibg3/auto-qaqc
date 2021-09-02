# How to use this project:

1. Clone this project to your PC. 
   
   ```git clone https://github.com/ibg3/auto-qaqc.git```
2. Install Docker (https://www.docker.com/get-started)
3. To start the container execute:

   ```docker run --rm -it --name auto-qaqc -v path/to/project:/data -p 127.0.0.1:1880:1880 ibg3/auto-qaqc:latest```

4. Open `localhost:1880` in your browser
   

For Debugging use the following command:

   ```docker logs -f pynodered```


When updating the requirements.txt file you need to restart the docker container:

   ```docker restart pynodered```
