#This will be run on a mac machine with github actions
#It will build the app for mac (intel and arm)
#It will then package the app for mac as a .app that runs in the system terminal
#it will also use createDMG.sh to create a .dmg
#it will also create a folder with the jumperless python files, a simple launcher script (that checks for dependencies and installs them if needed), and a readme