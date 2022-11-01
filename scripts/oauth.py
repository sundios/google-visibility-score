import argparse
import httplib2
import requests
 
from collections import defaultdict
from dateutil import relativedelta
from googleapiclient.discovery import build
from oauth2client import client
from oauth2client import file
from oauth2client import tools
import os

cred = os.path.abspath("api_keys/client_secret.json")


print(cred)


def authorize_creds(creds,authorizedcreds='authorizedcreds.dat'):
    '''
    Authorize credentials using OAuth2.
    '''
    print('Authorizing Creds')
    # Variable parameter that controls the set of resources that the access token permits.
    SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly'] 
 
    # Path to client_secrets.json file
    CLIENT_SECRETS_PATH = creds
 
    # Create a parser to be able to open browser for Authorization
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[tools.argparser])
    flags = parser.parse_args([])
 
    # Creates an authorization flow from a clientsecrets file.
    # Will raise InvalidClientSecretsError for unknown types of Flows.
    flow = client.flow_from_clientsecrets(
        CLIENT_SECRETS_PATH, scope = SCOPES,
        message = tools.message_if_missing(CLIENT_SECRETS_PATH))
 
    # Prepare credentials and authorize HTTP
    # If they exist, get them from the storage object
    # credentials will get written back to the 'authorizedcreds.dat' file.
    storage = file.Storage(authorizedcreds)
    credentials = storage.get()
 
    # If authenticated credentials don't exist, open Browser to authenticate
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)      # Add the valid creds to a variable
 
    # Take the credentials and authorize them using httplib2   
    http = httplib2.Http()                                      # Creates an HTTP client object to make the http request
    http = credentials.authorize(http=http)                     # Sign each request from the HTTP client with the OAuth 2.0 access token
    webmasters_service = build('searchconsole', 'v1', http=http)   # Construct a Resource to interact with the API using the Authorized HTTP Client.
 
    print('Auth Successful')
    return webmasters_service


webmasters_service = authorize_creds(cred) 


site_list = webmasters_service.sites().list().execute()
 
verified_sites_urls = [s['siteUrl'] for s in site_list['siteEntry']
                       if s['permissionLevel'] != 'siteUnverifiedUser'
                          and s['siteUrl'][:4] == 'http']
 
for site_url in verified_sites_urls:
  print( site_url)