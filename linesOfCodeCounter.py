import requests
import json
import settingsFile
import time
import sys



# class containing global variables
class GlobalData:
    settingsDict = {}



# class for settings functionality
class Settings:

    # setting up the object 
    settingObj = settingsFile.SettingsClass()

    # method to return the dict
    @classmethod
    def returnDict(cls):
        try:
            returnedDict = cls.settingObj.getDict()

            # if the retruned dict length is zero then restore the settings file
            if(len(returnedDict) == 0):
                cls.restoreSettings()
                time.sleep(0.5)

            return returnedDict

        except Exception as e:
            return {}

    # method to open the settings file
    # returns True on successfull opening 
    # else returns false and logs error
    @classmethod
    def openSettingsFile(cls):
        result = cls.settingObj.openSettings()

        if(result == None):
            return True
        else:
            return False

    
    # method to restore the settings file with default settings
    @classmethod
    def restoreSettings(cls):
        try:
            cls.settingObj.regenerateSettingsFile()
            return True
        except Exception as e:
            return False

















# function to get repos in your github account
# you need to pass the username for your github account
# without accessToken public repos list will be retrived
def getReposList(username , accessToken = None):

    pageCount = 1

    repos = []

    statusCodeLists = []

    # check pages till the page is empty
    while(True):
 
        # call api from github
        if(accessToken != None):
            data = requests.get("https://api.github.com/user/repos".format(username),{'visibility': 'all' , 'affiliation' : 'owner' , 'per_page' : 100 , 'page' : pageCount} , headers={'username': f"{username}" , 'Authorization' : f"token {accessToken}"})
        else:
            data = requests.get("https://api.github.com/users/{}/repos".format(username) , {'affiliation' : 'owner' , 'per_page' : 100 , 'page' : pageCount})

        statusCode = data.status_code
        
        tempRepos = []

        # grab the repo names
        for i in json.loads(data.text):
            repos.append(str(i["full_name"]))

        # break if the page was empty
        if(len(tempRepos) == 0):
            break

        # add results to the main data
        repos.extend(tempRepos)
        statusCodeLists.append(statusCode)
        pageCount = pageCount + 1

    return statusCodeLists , repos











if __name__ == "__main__":

    # get username and access token from the settings file
    GlobalData.settingsDict = Settings.returnDict()

    username = GlobalData.settingsDict.get("userName" , "none")

    if(username.lower() == "none"):
        print("\nset user name in the settings file first\n")
        sys.exit()

    accessToken = GlobalData.settingsDict.get("githubToken" , "none")

    if(username.lower() == "none"):
        accessToken = None


    # get the repo names list
    statusCodeLists , repos = getReposList(username , accessToken)



    
