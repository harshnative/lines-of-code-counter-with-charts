import requests
import json
import settingsFile
import time
import sys
import os
import pexpect
import subprocess
from sqlitewrapper import SqliteCipher


# class containing global variables
class GlobalData:
    settingsDict = {}

    tempFolderName = "temp_linesOfCodeCounter/"

    dataBase = "linesOfCodeCounter_db.db"

    dbObj = SqliteCipher(dataBase , password="hello")



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

    statusCodeList = []

    # check pages till the page is empty
    while(True):
 
        # call api from github
        if(accessToken != None):
            data = requests.get("https://api.github.com/user/repos".format(username),{'visibility': 'all' , 'affiliation' : 'owner' , 'per_page' : 100 , 'page' : pageCount} , headers={'username': f"{username}" , 'Authorization' : f"token {accessToken}"})
        else:
            data = requests.get("https://api.github.com/users/{}/repos".format(username) , {'affiliation' : 'owner' , 'per_page' : 100 , 'page' : pageCount})

        statusCode = data.status_code
        statusCodeList.append(statusCode)
        
        tempRepos = []

        # grab the repo names
        for i in json.loads(data.text):

            # repo should not be fork
            if(not(i["fork"])):
                repos.append([str(i["full_name"]) , bool(i["private"]) , str(i["name"]) , str(i["updated_at"])])

        # break if the page was empty
        if(len(tempRepos) == 0):
            break

        # add results to the main data
        repos.extend(tempRepos)
        pageCount = pageCount + 1

    return statusCodeList , repos








def getReposFromGithub(includePrivateRepos):


    def search_excludeLanguages(excludeLanguages , toSearch):
        toSearch = str(toSearch).strip().lower()

        for i in excludeLanguages:
            if(toSearch == str(i).strip().lower()):
                return True
        
        return False


    overAllResult = {}
    excludeLanguages = []
    directClocResults = {}

    # get username and access token from the settings file
    GlobalData.settingsDict = Settings.returnDict()

    username = GlobalData.settingsDict.get("userName" , "none")

    if(username.lower() == "none"):
        print("\nset user name in the settings file first\n")
        sys.exit()

    accessToken = None

    if(includePrivateRepos):
        accessToken = GlobalData.settingsDict.get("githubToken" , "none")

        if(accessToken.lower() == "none"):
            print("\nset access token from github in the settings file first to work with private repos\n")
            sys.exit()

    
    excludeLanguagesSetting = GlobalData.settingsDict.get("excludeLanguages" , "none")
    if(accessToken.lower() != "none"):
        temp_excludeLanguages = excludeLanguagesSetting.split(',')

        for i in temp_excludeLanguages:
            excludeLanguages.append(str(i).strip())


    useCache = GlobalData.settingsDict.get("excludeLanguages" , "false")
    if(useCache.lower() != "true"):
        useCache = True
    else:
        useCache = False

    # get the repo names list
    statusCodeLists , repos = getReposList(username , accessToken)


    # if the status code is not 200 , raise error
    errorGettingRepos = False

    for i in statusCodeLists:
        if(i != 200):
            errorGettingRepos = True

    
    if(errorGettingRepos):
        print("Error while getting repos list of the user = {}".format(username))
        print("Github API status codes = {}".format(statusCodeLists))
        sys.exit()


    # print the names and total number of repos found
    print("\n\nRepos Found = \n")
    for i in repos:
        print("Repo - {} , private = {}".format(i[0] , i[1]))

    print("\nTotal Repos Found = {}".format(len(repos)))


    # Download the repo

    # make temp_linesOfCodeCounter folder 
    try:
        os.mkdir(GlobalData.tempFolderName)
    except FileExistsError:
        pass


    _ , reposFromDb = GlobalData.dbObj.getDataFromTable("repos" , omitID=True)


    # download the repos and get status using cloc
    for i in repos:

        # get date and time from the repos list of the repo
        # date and time of last modified
        splittedDateTime = str(i[3]).split("T")
        dateOfRepo = splittedDateTime[0]
        timeOfRepo = splittedDateTime[1]
        timeOfRepo = timeOfRepo[:-1]


        # check if the db is available in data base
        foundInDb = False

        if(useCache):
            for repoFromDB in reposFromDb:
                if(i[2] == repoFromDB[0]):
                    if((repoFromDB[1] == dateOfRepo) and (repoFromDB[2] == timeOfRepo)):
                        foundInDb = True
                        result = repoFromDB[-1]

        # if the db is not found or is modified or useCache is False then download the new db
        if(not(foundInDb)):

            isRepoPrivate = i[1]

            print("\n\nDownloading {} , please wait ...".format(i[0]))
            print("\n")

            # remove any existing repos in tempFolder
            os.system("rm -rf {}".format(GlobalData.tempFolderName))
            time.sleep(0.5)
            os.mkdir(GlobalData.tempFolderName)
            time.sleep(0.5)

            # download the repos if private
            if(isRepoPrivate):
                child = pexpect.spawn("git clone https://github.com/{}".format(i[0]) , cwd="{}/{}".format(os.getcwd(),GlobalData.tempFolderName) , encoding='utf-8' ,  timeout=3000, maxread=200000)
                
                # pass username and password
                child.expect(".*github.com': ")
                child.sendline(username)
                child.expect(".*github.com': ")
                child.sendline(accessToken)

                # print output of command
                print(child.read())

            else:

                # download a public repo

                # change working dir
                os.chdir("{}/{}".format(os.getcwd(),GlobalData.tempFolderName))
                os.system("git clone https://github.com/{}".format(i[0]))
                time.sleep(0.5)

                # reset working dir
                os.chdir("{}".format(os.getcwd()[:(len(GlobalData.tempFolderName))*-1]))

            time.sleep(0.5)

            # prase the repo using cloc
            result = subprocess.check_output("cloc --json {}/".format(i[2]), shell=True , cwd="{}/{}".format(os.getcwd(),GlobalData.tempFolderName))
            
            try:
                resultDict = dict(json.loads(result))
                GlobalData.dbObj.insertIntoTable("repos" , [i[2] , str(dateOfRepo) , str(timeOfRepo) , json.loads(result)])
            except json.decoder.JSONDecodeError:
                print("\n\nSkipping {}".format(i[0]))
                GlobalData.dbObj.insertIntoTable("repos" , [i[2] , str(dateOfRepo) , str(timeOfRepo) , {}])

            time.sleep(1)

        # else get result from cache
        else:
            print("\nusing cached version of {} , please wait ...".format(i[0]))
            print("\n")

            resultDict = dict(result)

        # parse the result dict
        for a,b in resultDict.items():

            """
            "CSS" :{
            #   "nFiles": 24,
            #   "blank": 2191,
            #   "comment": 227,
            #   "code": 24000},

            CSS = a , rest = b
            """
            b = dict(b)

            # if the a is not in excluded list and not header
            if((a != "header") or (search_excludeLanguages(excludeLanguages , a))):
                
                
                innerDict = overAllResult.get(a , None)

                # if the innerDict is None
                # init as empty dict
                if(innerDict == None):
                    innerDict = {}

                # added value to inner dict
                for k,l in b.items():

                    # if the value is not their , init it to l
                    # else value = value + l
                    valueK = innerDict.get(k , None)

                    if(valueK == None):
                        innerDict[k] = l
                    else:
                        innerDict[k] = innerDict[k] + l

                # add a to overAll dict
                overAllResult[a] = innerDict

        directClocResults[i[2]] = result
        
        print("\n\n")

    for i,j in overAllResult.items():
        print(i)
        print(j)

        print("\n\n")




    





if __name__ == "__main__":
    reposColList = [
            ["repoName" , "TEXT"] , 
            ["date" , "TEXT"] , 
            ["time" , "TEXT"] , 
            ["clocData" , "JSON"] , 
        ]

    try:
        GlobalData.dbObj.createTable("repos" , reposColList)
    except ValueError:
        pass

    print("1. Get Repos from github")
    print("2. Get Repos from local folder")
    choice = int(input("Enter your choice : "))

    if(choice == 1):

        print("\n\n\n")
        includePrivateRepos = input("work with private repo's = [ y/n ] : ")

        if(includePrivateRepos.strip().lower() == "y"):
            includePrivateRepos = True
        else:
            includePrivateRepos = False 

        getReposFromGithub(includePrivateRepos)

    



    
