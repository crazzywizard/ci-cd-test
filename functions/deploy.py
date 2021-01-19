from dotenv import load_dotenv
import os
import os.path
from os import path
import sys
import optparse
import json
from inspect import getmembers, isfunction, signature, getdoc
import main
import argparse

# Change default firestore document path.
DEFAULT = 'musicians/{musicians}'


class deployFunction:
    """
    A class used to deploy python cloud functions.

    ...

    Methods
    -------
    getAccount:
        Returns Google Cloud Account Address

    getProjectId:
        Returns Project Id

    getDeployedFunctions:
        Gets all currently deployed functions

    setUp:
        Sets Gcloud account and project

    getFunctions:
        Parses main module and returns python google cloud functions.

    deployPythonFunction(function,documentPath="musicians/{musicians}")
        Deploys python runtime cloud functions.

    deployNodeFunction(function):
        deploys node runtime cloud functions

    """

    def __init__(self, args):
        self.httpTrigger = "gcloud functions deploy {} --runtime python37 --trigger-http "
        self.storageTrigger = "gcloud functions deploy {} --runtime python37 --trigger-resource {}.appspot.com --trigger-event google.storage.object.finalize"
        self.onCreateTrigger = "gcloud functions deploy {} --runtime python37 --trigger-event providers/cloud.firestore/eventTypes/document.create --trigger-resource '{}'"
        self.onUpdateTrigger = "gcloud functions deploy {} --runtime python37 --trigger-event providers/cloud.firestore/eventTypes/document.update --trigger-resource '{}'"
        self.onDeleteTrigger = "gcloud functions deploy {} --runtime python37 --trigger-event providers/cloud.firestore/eventTypes/document.delete --trigger-resource '{}'"
        self.onWriteTrigger = "gcloud functions deploy {} --runtime python37 --trigger-event providers/cloud.firestore/eventTypes/document.write --trigger-resource '{}'"
        self.args = args

    def getAccount(self):
        """
        Gets Google Cloud Account Address

        Returns
        -------
        gcloudAccount : str
            Google Cloud Account ID for current user.
        """
        gcloudAccount = None
        if(path.exists(".env")):
            if(os.getenv("GCLOUD_ACCOUNT")):
                gcloudAccount = os.getenv("GCLOUD_ACCOUNT")
            else:
                gcloudAccount = input("Enter gcloud account:")
                text = '\nGCLOUD_ACCOUNT={}'.format(gcloudAccount)
                f = open('.env', 'a+')
                f.write(text)
                f.close()
        else:
            gcloudAccount = input("Enter gcloud account:")
            text = 'GCLOUD_ACCOUNT={}'.format(gcloudAccount)
            f = open('.env', 'a+')
            f.write(text)
            f.close()
        return gcloudAccount

    def create_ci_cd_key(self):
        data = json.loads(os.getenv('GCLOUD'))
        with open('ci_cd_key.json', 'w') as outfile:
            json.dump(data, outfile)
        return data['client_email']

    def getProjectId(self):
        """
        Gets Project Id.

        Returns
        -------
        projectId : str
            project id for current google cloud project.
        """
        projectId = None
        if(path.exists("../.firebaserc")):
            f = open("../.firebaserc", "r")
            id_file = json.load(f)
            projectId = id_file["projects"]["default"]
        elif(os.getenv("PROJECT_ID")):
            projectId = os.getenv("PROJECT_ID")
        else:
            projectId = input("Enter project id:")
            text = 'PROJECT_ID={}'.format(projectId)
            f = open('.env', 'a+')
            f.write(text)
            f.close()
        return projectId

    def setUp(self):
        """ Sets Gcloud account and project """
        if(os.getenv("CI_CD")):
            client = self.create_ci_cd_key()
            os.system(
                "gcloud auth activate-service-account {} --key-file=./ci_cd_key.json".format(client))
        else:
            os.system('gcloud config set account {}'.format(self.getAccount()))
        projectId = self.getProjectId()
        if(os.getenv('ACCESS')):
            access = os.getenv('ACCESS')
        else:
            currentProjects = os.popen(
                'gcloud projects list --format=list').read()
            access = 'projectId: {}'.format(projectId) in currentProjects
            text = '\nACCESS={}'.format(access)
            f = open('.env', 'a+')
            f.write(text)
            f.close()
        if(access):
            os.system('gcloud config set project {}'.format(projectId))
        else:
            sys.exit(
                'You do not have access to project {}. Please request access to project from project Owner/Admin.'.format(projectId))

    def getDeployedFunctions(self):
        """
        Gets all currently deployed functions.

        Returns
        -------
        currentNodeFunctions : (list)
            all current deployed node functions.

        currentPythonFunctions : (list)
            all current deployed python functions.
        """
        currentNodeFunctions, currentPythonFunctions = list(), list()
        functions_list = json.loads(
            os.popen('gcloud functions list --format=json').read())
        for function in functions_list:
            if 'node' in function['runtime']:
                currentNodeFunctions.append(function['entryPoint'])
            elif 'python' in function['runtime']:
                currentPythonFunctions.append(function['entryPoint'])
        return currentNodeFunctions, currentPythonFunctions

    def getFunctions(self):
        """
        Parses main module and returns python google cloud functions.

        Returns
        -------

        functions : list
            All google cloud functions.

        httpFunctions : list
            All http cloud functions.

        otherFunctions : list
            All functions minus http cloud functions.

        storageFunctions : list
            All storage trigger cloud functions.

        createFunctions : list
            All on create Firestore trigger functions.

        updateFunctions : list
            All on update Firestore trigger functions.

        deleteFunctions : list
            All on delete Firestroe trigger functions.

        writeFunctions : list
            All on write Firestore trigger functions.

        """
        (functions, httpFunctions, otherFunctions,
         storageFunctions, createFunctions, updateFunctions,
         deleteFunctions, writeFunctions) = list(
        ), list(), list(), list(), list(), list(), list(), list()
        functions = [o for o in getmembers(main) if isfunction(o[1])]
        functions = [o[0] for o in functions]
        for function in functions:
            try:
                result = str(signature(getattr(main, function)))
                if 'request' in result:
                    httpFunctions.append(function)
                elif 'data' and 'context' in result:
                    otherFunctions.append(function)
                    eventType = getdoc(getattr(main, function))
                    if 'Cloud Storage' in eventType:
                        storageFunctions.append(function)
                    elif 'Firestore document on create' in eventType:
                        createFunctions.append(function)
                    elif 'Firestore document on update' in eventType:
                        updateFunctions.append(function)
                    elif 'Firestore document on delete' in eventType:
                        deleteFunctions.append(function)
                    elif 'Firestore document on write' in eventType:
                        writeFunctions.append(function)
            except Exception as e:
                print(e)
        return functions, httpFunctions, otherFunctions, storageFunctions, createFunctions, updateFunctions, deleteFunctions, writeFunctions

    def deployPythonFunction(self, function, documentPath=DEFAULT):
        """
        Deploys python runtime cloud function.

        Parameters
        ----------
        function : str
            name of the function to deploy

        documentPath : str
            required if deploying firestore trigger cloud function.
        """
        triggerResource = 'projects/%s/databases/(default)/documents/%s' % (
            self.getProjectId(), documentPath)
        (functions, httpFunctions, otherFunctions, storageFunctions, createFunctions,
            updateFunctions, deleteFunctions, writeFunctions) = self.getFunctions()
        if function in httpFunctions:
            if self.args.env:
                os.system(self.httpTrigger.format(
                    function) + '--env-vars-file .env.yaml')
            else:
                os.system(self.httpTrigger.format(function))
        elif function in storageFunctions:
            os.system(self.storageTrigger.format(
                function, self.getProjectId()))
        elif function in createFunctions:
            os.system(self.onCreateTrigger.format(function, triggerResource))
        elif function in updateFunctions:
            os.system(self.onUpdateTrigger.format(function, triggerResource))
        elif function in deleteFunctions:
            os.system(self.onDeleteTrigger.format(function, triggerResource))
        elif function in writeFunctions:
            os.system(self.onWriteTrigger.format(function, triggerResource))

    def deployNodeFunction(self, function):
        """ Deploys node runtime cloud functions """
        if (os.getenv("CI_CD")):
            os.system('firebase deploy --token {} --only functions:{}'.format(
                os.getenv("FIREBASE_TOKEN"), function))
        else:
            os.system('firebase deploy --only functions:{}'.format(function))


print('Parsing Arguments')
parser = argparse.ArgumentParser(
    prog='deploy', usage='%(prog)s [options] path', description="Deploy Google Cloud Functions")
parser.add_argument('--only', action='store', type=str, default=None,
                    help='What is the name of the function')
parser.add_argument('--all', action='store_true', help='Deploy all functions')
parser.add_argument('--yes', action='store_true', help='Use defaults')
parser.add_argument('--delete', action='store', type=str,
                    default=None, help="Delete Python Cloud Function")
parser.add_argument('--env', action='store_true', help='Deploy env file')
args = parser.parse_args()
load_dotenv()
if os.getenv('VIRTUAL_ENV'):
    print('Using Virtualenv')
else:
    print('Not using Virtualenv')

deploy = deployFunction(args)
deploy.setUp()
print("Getting cloud functions defined in main.py")
(functions, httpFunctions, otherFunctions, storageFunctions, createFunctions,
 updateFunctions, deleteFunctions, writeFunctions) = deploy.getFunctions()
allPythonFunctions = httpFunctions + otherFunctions
firestoreTriggerFunctions = createFunctions + \
    updateFunctions + deleteFunctions + writeFunctions
name = args.only if args.only else None
yes = {'yes', 'y', 'ye'}
no = {'no', 'n'}
default = {''}

doc_path = dict()
if (path.exists("doc_path.json")):
    print('Getting Document Paths')
    f = open("doc_path.json", "r")
    doc_path = json.load(f)


def firestoreTriggerDeploy(function, doc_path):
    """
    Deploys firestore trigger cloud functions.
    """
    if not (doc_path and doc_path.get(function)):
        choice = input(
            'Use default document path of {} [Y/n]: '.format(DEFAULT)).lower()
        while choice not in yes and choice not in no and choice not in default:
            choice = input('Please response with Y/n: ').lower()
        if choice in yes or choice in default:
            doc_path[function] = DEFAULT
            with open("doc_path.json", "w+") as outfile:
                json.dump(doc_path, outfile, indent=4)
            deploy.deployPythonFunction(function, DEFAULT)
        elif choice in no:
            path = input('Specify Document Path: ')
            doc_path[function] = path
            with open("doc_path.json", "a+") as outfile:
                json.dump(doc_path, outfile)
            deploy.deployPythonFunction(function, path)
    elif doc_path.get(function):
        deploy.deployPythonFunction(function, doc_path[function])


if not name and not args.all and not args.delete:
    name = input("Please enter function name: ")
if args.delete:
    currentNodeFunctions, currentPythonFunctions = deploy.getDeployedFunctions()
    if args.delete in currentPythonFunctions:
        os.system('gcloud functions delete {}'.format(args.delete))
    elif args.delete in allPythonFunctions:
        print('Function already Deleted from Cloud')
        print('Remove function defintion from main.py')

if args.all:
    print("Getting Current Deployed Functions")
    currentNodeFunctions, currentPythonFunctions = deploy.getDeployedFunctions()
    if len(currentPythonFunctions) > len(allPythonFunctions):
        functionsToDelete = [
            x for x in currentPythonFunctions if x not in allPythonFunctions]
        for func in functionsToDelete:
            choice = input(
                'Function {} is not defined in main.py. Delete from cloud? [y/N]: '.format(func)).lower()
            while choice not in yes and choice not in no and choice not in default:
                choice = input('Please response with y/N: ').lower()
            if choice in yes:
                os.system('gcloud functions delete {}'.format(func))
            elif choice in no or choice in default:
                pass
    for function in allPythonFunctions:
        if function in firestoreTriggerFunctions:
            firestoreTriggerDeploy(function, doc_path)
        else:
            deploy.deployPythonFunction(function)
    if(os.getenv("CI_CD")):
        os.system(
            "firebase deploy --only functions --token {}".format(os.getenv("FIREBASE_TOKEN")))
    else:
        os.system("firebase deploy --only functions")
elif name:
    if name in allPythonFunctions:
        if name in firestoreTriggerFunctions:
            firestoreTriggerDeploy(name, doc_path)
        else:
            deploy.deployPythonFunction(name)
    else:
        deploy.deployNodeFunction(name)
