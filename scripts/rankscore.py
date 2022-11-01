#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 20:12:47 2022

@author: kburchardt
"""

import pandas as pd
import httplib2
from apiclient.discovery import build
import argparse
from oauth2client import client
from oauth2client import file
from oauth2client import tools
import matplotlib.pyplot as plt
import glob
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import os

cred = os.path.abspath("client_secret.json")


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


# =============================================================================
# Inputs that can be changed.
# =============================================================================

#Site: Here we can select any URL we want from the list of GSC properties.
site = "https://www.uselessthingstobuy.com"

#Daily dates:
#daily dates we want to calculate our visibility score. Limit is 16 months.
start = datetime.date(2022, 1, 1)
end = datetime.date(2022, 3, 30)

#Yearly Dates this will count last 12 months starting today. Limit is 16 months:
yearly_start = date.today() - relativedelta(months=+12)
yearly_end = date.today() 

#Device: Here we can select the device we want to get our data. Desktop, Mobile or Table
device = "mobile"

# =============================================================================
# Functions. 
# =============================================================================


def stupid_prints():  
    print('Ready/')
    print ('ᕦ( ᐛ )ᕤ')
    print ('ᕦ( ᐛ )ᕤ')
    print ('ᕦ( ᐛ )ᕤ')
      

def execute_request(service, property_uri, request):
    """Function to execute your API Request
    Args:
        service: Connection to searchconsole,v1 via http. Line 43
        property_uri: URL we want to use. We define our variable as site. Line44
        request: request with the filters we want. Line 89
    """
    return service.searchanalytics().query(siteUrl=property_uri, body=request).execute()



def get_data(start_date,end_date, device, datarequest):
    """

    Function to get daily and yearly data from GSC api. 
    There is and If else statement that checks if its daily 
    or yearly the data we are requesting.
    
    Parameters
    ----------
    start_date : date type
        represents starting date we want to get data.
    end_date : date type
        represents ending date we want to get data.
    device : str type
        filter results against the specified device type. 
             Supported values: desktop,mobile, tablet.
    datarequest : str type
        What type of data are requesting. Daily or Yearly.

    Returns
    -------
    None.

    """
    if datarequest == "daily":
        print("Getting daily data")
        start_date = start
        end_date = end
        delta = datetime.timedelta(days=1)
    
        
        while start_date <= end_date:
            print( 'Checking date --> ', start_date)
            print( 'For device --->' , device)
            request = {
                'startDate': datetime.datetime.strftime(
                    start_date,"%Y-%m-%d"),
                #end date should be start date so we can get the same date data
                'endDate': datetime.datetime.strftime(
                    start_date,'%Y-%m-%d'),
                'dimensions': ['query'],
                'rowLimit': 25000, #up to 25.000 urls
                'dimensionFilterGroups': [{
                   'filters': [{
                       'dimension': 'device',
                       'expression': device
                   }]
               }],
                
            }
             
            print(request)
            
            #Request to SC API
            response = execute_request(webmasters_service, site, request)
            print("Response OK")
            
            #selecting only rows where data lives
            rows = response['rows']
            
            #calling fucntion that cleans data and creates excell file
            clean_data(rows,start_date,datarequest)
            
            #delta to add one day 
            start_date += delta
            
        stupid_prints()
        
    elif datarequest == "yearly":
        
        print("Getting yearly data")
    
        request = {
                'startDate': datetime.datetime.strftime(start_date,"%Y-%m-%d"),
                #end date should be start date so we can get the same date data
                'endDate': datetime.datetime.strftime(end_date,'%Y-%m-%d'),
                'dimensions': ['query'],
                'rowLimit': 25000, #up to 25.000 urls
                'dimensionFilterGroups': [{
                   'filters': [{
                       'dimension': 'device',
                       'expression': device
                   }]
               }],
                
            }
        print(request)
        
        #Request to SC API
        response = execute_request(webmasters_service, site, request)
        print("Response OK")
        
        #selecting only rows where data lives
        rows = response['rows']
        
        #calling fucntion that cleans data and creates excell file
        clean_data(rows,yearly_start,datarequest)
        
        stupid_prints()
                

def clean_data(rows,start_date,datarequest):
    """ Function that cleans the data and coverts it
    into data frame.
    Depending on the datarequest(daily or yealry) we will
    name the folder differentely and send it to a different 
    folder

    Parameters
    ----------
    rows : list of dictionaries
        contains each keyword as a dictionary
    start_date : date
        Passing this value to name the xlsx file
    datarequest : str type
        What type of data are requesting. Daily or Yearly

    Returns
    -------
    df : Dataframe
        Dataframe with all of our data ready to be exported
        to xlsx
    """    
    print('Cleaning Data...')
    #empty lists to save our data
    #urls = []
    query = []
    clicks = []
    impressions = []
    ctr = []
    rank = []
    
    #for loop that iterates thrhought the list of dictionaries
    #and saves data into empty list
    for row in rows:
        #urls.append(row['keys'][0])
        query.append(row['keys'][0])
        clicks.append(row['clicks'])
        impressions.append(row['impressions'])
        ctr.append(row['ctr'])
        rank.append(row['position'])
    
    if datarequest == "daily":
        
        #creating the Dataframe with our lists
        df = pd.DataFrame()
        #df['URL'] = urls
        df['Query'] = query
        df['Clicks'] = clicks
        df['Impressions'] = impressions
        df['CTR'] = ctr
        df['Position'] = rank
        df['date'] = start_date
        print(df)
        
        #exporting the daily dataframe to the day-data folder 
        df.to_excel(r'../data/day-data/' + str(start_date) + '.xlsx', index = False)
        
    elif datarequest == "yearly":
        
        #creating the Dataframe with our lists
        df = pd.DataFrame()
        #df['URL'] = urls
        df['Query'] = query
        df['Clicks'] = clicks
        df['Impressions'] = impressions
        df['CTR'] = ctr
        df['Position'] = rank
    
        print(df)
        #exporting the daily dataframe to the day-data folder 
        df.to_excel(r'../data/year-data/yearly.xlsx', index = False)
        
        

def ctr_table(df):
    """

    Parameters
    ----------
    df : DATAFRAME
    Yearly dtaframe that we will use rounded up positions to calculate 
    CTR value for each position.

    Returns
    -------
    None.

    """
    # # ##For Testing delete after
    # df = pd.read_excel('/Users/konradburchadtpizarro-local/Desktop/google-visibilty-score/data/year-data/yearly.xlsx')

    
    #Rounding Positions with no decimal
    df['Position'] = df['Position'].round()
    
    
    #groupping by to build CTR table
    ctr = df.groupby('Position', as_index=False)['CTR'].mean()
    
    #selecting only top 20 ( Make sure to check that the 
    #list contains 1- 20 so that we can assing CTR values when doing the calculation)
    ctr = ctr.head(20)
    
    #CTR to be 2 decimals
    ctr['CTR'] = ctr['CTR'].round(3)
    
    #plotting not-normalized Clicks vs Rankings Both
    plt.plot(ctr['Position'],ctr['CTR'], label = "CTR")
    plt.ylabel('CTR')
    plt.title('CTR Table')
    plt.xlabel('Rank')
    plt.legend()
    plt.show()
    
    
    print("CTR Table")
    #normailizing table so that we can get valies from 1 to 0.
    #this is easier to see so that we measure perfecvt score as 1 or 100%
    
    normalized_d = []
    for i in ctr['CTR']:
        print(i)
        n =  i / ctr['CTR'][0]
        normalized_d.append(n)
    
    normalized_d = pd.DataFrame(normalized_d)
    normalized_d.columns = ['Normalized CTR']
    
    
    CTRd = pd.concat([ctr, normalized_d], axis=1)
    
    #CTR to be 2 decimals
    CTRd['Normalized CTR'] = CTRd['Normalized CTR'].round(3)
    
    #Cleaning table in case the numbers are not from 1 - 20 
    CTRd['Position'] = CTRd.index + 1
    
    print(CTRd)
    
    #saving CTR table into excell
    CTRd.to_excel(r'../data/ctr-table/ctr-table.xlsx', index = False)
    
    #plotting Normalized Clicks vs Rankings Both
    plt.plot(CTRd['Position'],CTRd['CTR'], label = "CTR")
    plt.plot(CTRd['Position'],CTRd['Normalized CTR'], label = "Normalized CTR" )
    plt.ylabel('CTR')
    plt.title('CTR Score')
    plt.xlabel('Rank')
    plt.savefig('../data/ctr-table/ctr-table.png', bbox_inches='tight')
    plt.legend()
    plt.show()
    
    visibility_score(CTRd)
    

def visibility_score(CTRd):
    files = sorted(glob.glob('../data/day-data/*'))
    
    keywords = pd.read_excel('../Keywords/Keywords.xlsx')
    
    visibility_score = []
    dates = []
    for f in files:
        #opening file
        print(f)
        d = pd.read_excel(f)
        
        #Rounding Positions with no decimal
        d['Position'] = d['Position'].round()
        
        #slicing Dataframe to use only desired columns
        d = d[['Query','Position','date']]
        
        
        #Vlookup to match CTR scores with Position
        d = pd.merge(d,
                    CTRd,
                    on="Position",
                    how='outer')
        
        #here we create the list of keywords that match from our keyword list and GSC day data.
        new_d = []
        for keyword,sv in keywords.itertuples(index=False):
            print(keyword, sv)
            f = d[d['Query'].eq(keyword)]
            if f.empty:
               print('Kewyord is not in list')
            else:
                f['Search Volume'] = sv
                print(f)
                new_d.append(f)
                
        #concatenating the list of dataframes into a new DF
        new_df = pd.concat(new_d)
        
        #reseting index so we dont get confused
        new_df= new_df.reset_index(drop=True)
        
        #replacing nan values with 0
        new_df = new_df.fillna(0)
        
        #empty df to save visibility by kw
        sv_ctr = []
        
        #removed the divisor of 100
        for i, j in zip(new_df['Normalized CTR'],new_df['Search Volume']):
            s= (i*j)
            sv_ctr.append(s)
            
        #inserting the visibility score    
        new_df.insert(6,'Visibility Score',sv_ctr)
        
        #Day value
        visibility_score.append((new_df['Visibility Score'].sum()/keywords['Search Volume'].sum())*100)
        #getting the date of the visibility score
        date = d['date'].iloc[0].strftime('%Y-%m-%d')
        dates.append(date)
     
    #creating Final Dataframe with dates
    final_df = pd.DataFrame({"Visibility Score":visibility_score,"date":dates})
    
    #saving Visbility score in excel
    final_df.to_excel(r'../data/visibility-score/visibility-score.xlsx', index = False)
    
    #Testing
    # final_df = pd.read_excel('../data/visibility-score/visibility-score.xlsx')
    
    #plotting Normalized Clicks vs Rankings Both
    plt.plot(final_df['date'],final_df['Visibility Score'], label = "Visibility Score")
    plt.ylabel('Visibility Score')
    plt.title('Visibility Score')
    plt.xlabel('dates')
    plt.xticks(rotation = 45)
    plt.legend()
    plt.savefig('../data/visibility-score/visibility-score.png', bbox_inches='tight')
    plt.show()
        


 
#getting Daily data
get_data(start,end,device,"daily")

#getting Yearly data
get_data(yearly_start,yearly_end,device,"yearly")

#load yearly data to create dataframe

df = os.path.abspath("/yearly.xlsx")

df = pd.read_excel('../data/year-data/yearly.xlsx')

#creating and Getting visibily score Visibility score function is inside CTR table
ctr_table(df)







