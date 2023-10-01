This file will contains the micropython OTA updater to handle the server updates

this is a test case for my first steps with chatgpt generated code

procedures to be acomplished when sending a new update

1- create a new directory with the current version number plus 1
2- transfer all the expected update files to the new directory
3- generate a new version file with the current version name + 1 and the received files in the new directory
4- make a copy of the main version file with the following structure version1.0.0 with the number being the current version
5- copy the version file created inside the directory into the upper directory

Important note: this ensures that a proper backup of versions exist if the need for rolback

ToDo: add procedures to handle the write for multiple file
ToDo: add update version and file lists