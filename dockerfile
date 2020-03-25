# It is our freshly build sonar-scanner-image from previous steps that
# is used here as a base image in docker file that we will be working on
FROM sonar-scanner-image:latest AS sonarqube_scan
# Here we are setting up a working directory to /app. It is like using `cd app` command
WORKDIR /app
# Copying all files from the project directory to our current location (/app) in image
# except patterns mention in .dockerignore
COPY . .
# Execution of example command. Here it is used to show a list of files and directories.
# It will be useful in later exercises in this tutorial. 
RUN ls -list
# To execute sonar-scanner we just need to run "sonar-scanner" in the image. 
# To pass Sonarqube parameter we need to add "-D"prefix to each as in the example below
# sonar.host.url is property used to define URL of Sonarqube server
# sonar.projectKey is used to define project key that will be used to distinguish it in 
# sonarqube server from other projects
# sonar.sources directory for sources of project
RUN sonar-scanner \
    -Dsonar.host.url="http://localhost:9000" \
    -Dsonar.projectKey="2baa74584d6bea97c7f1225c54cd1926b5346190" \
    -Dsonar.sources="lib"