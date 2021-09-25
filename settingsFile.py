# from .txtJson import TxtJson
import time
import subprocess
import os
import hjson
import copy

# main class
class SettingsClass:

    # constructor for the class
    def __init__(self):


        # setting up the settings file path based the operation system of the user
        self.path = os.getcwd() + "/settings.txt"
    

        # default settings file data
        self.settingsFile = {
  "userName": "None" , 
  "githubToken": "None" , 
}

    
    # this method reads data from the settings file and returns it in dictionary format
    def getDict(self):

        try:

            with open(self.path , "r") as file:
                data = file.read()

            dictReturned = hjson.loads(data)

            if(len(dictReturned) < len(self.settingsFile)):
                tempSettings = copy.deepcopy(self.settingsFile)

                tempSettings.update(dictReturned)

                self.regenerateSettingsFile(tempSettings)

                return tempSettings

            else:
                return dictReturned

        # if the settings file is not present
        except FileNotFoundError:
            
            # then first we will write the settings file with default data
            self.regenerateSettingsFile()

            # waiting for the os to actaully index the file
            time.sleep(0.5)

            # then we will return dict
            with open(self.path , "r") as file:
                data = file.read()

            dictReturned = hjson.loads(data)
            return dictReturned

    # this method generate the file with default values
    def regenerateSettingsFile(self , settingsFile = None):

        if(settingsFile == None):
            settingsFile = self.settingsFile

        # writing the file
        with open(self.path , "w+") as file:
            file.write(hjson.dumps(settingsFile))



        
    # function to open the settings using default opener
    # None is retruned on succesfull opening 
    # exception in string format is returned else wise
    def openSettings(self):
        try:
            # startfile utility on windows
            if(self.isOnWindows):
                os.startfile(self.path)
            else:
                # using gedit on linux
                os.system("sudo gedit " + self.path)
            return None
        except Exception as e:
            return str(e)
