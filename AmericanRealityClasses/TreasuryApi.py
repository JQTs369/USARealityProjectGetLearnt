# here to get the info we need for our web app
# sources: 
    # https://fiscaldata.treasury.gov/api-documentation/
    # https://fiscaldata.treasury.gov/datasets/historical-debt-outstanding/historical-debt-outstanding
        # Historical Debt Outstanding is a dataset that provides a summary of the U.S. government's total outstanding debt at the end of each fiscal year
        #  from 1789 to the current year. Between 1789 and 1842, the fiscal year began in January. From January 1842 until 1977, the fiscal year began in July.
        #  From July 1977 onwards, the fiscal year has started in October. Between 1789 and 1919, debt outstanding was presented as of the first day of the next fiscal year.
        #  From 1920 onwards, debt outstanding has been presented as of the final day of the fiscal year. This is a high-level summary of historical public debt
        #  and does not contain a breakdown of the debt components.
    # https://taxpolicycenter.org/sites/default/files/statistics/spreadsheet/fed_receipt_funds_3.xlsx
        # treseury site does not have complete history only from 1995 to present -make it make sense


# imports
import requests
# import json
import os
import pandas as pd
# import time


class Treasury:

    def __init__(self):
        # self.base_path = r'https://api.fiscaldata.treasury.gov/services/api/fiscal_service'
        self.ErrorLog = []



    def getHistoricalDebtAPIData(self,BaseUrl):
        '''
        Gets api data and all pages into a list of dicts. can be put into a pandas data frame if needed
        Built of this api. # TODO need to try other base urls to see if it is dynamic
        BaseUrl = r'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_outstanding'
        '''
        data = []
        pageNumber = 1
        while True:
            # try to call data with GET
            response = requests.get(f"{BaseUrl}?page[number]={pageNumber}&page[size]=100")
            if response.status_code == 200:
                # get out data to pharse
                json_data = response.json()

                # append the data from the current page to the list
                data.extend(json_data['data'])

                # get links next key for more pages
                nextPage = json_data['links'].get('next')
                # increase page number if needed
                if nextPage:
                    pageNumber +=1
                else:
                    # no more pages
                    break
            else:
                print(f"Error geting API call: {response.status_code}")
                break
        try:
            debtDF = pd.DataFrame(data)
            debtDF['record_fiscal_year'] = debtDF['record_fiscal_year'].astype(int)
            debtDF['debt_outstanding_amt'] = debtDF['debt_outstanding_amt'].astype(float)
        except Exception as e:
            print(f"Error making Treasery DataFrame: {e}")
        return debtDF
    

    def getTaxPolicyDownload(self,
                TaxPolicySaveLocation:str=r'C:\Users\Jacque Trahan\Documents\USARealityProjectGetLearnt\AmericanRealityClasses\resources\TaxPolicyCentrHistoricRevenues.xlsx'):
        # get directory name sperate from file name
        directory = os.path.dirname(TaxPolicySaveLocation)
        # if directroy does not exits itll be made
        if not os.path.exists(directory):
                os.makedirs(directory)

        # path to link of button on the taxpolicies page
        baseUrl = r'https://taxpolicycenter.org/sites/default/files/statistics/spreadsheet/fed_receipt_funds_3.xlsx'
        # Get our data and save it where user chose.
        response = requests.get(baseUrl)
        if response.status_code == 200:
            with open(TaxPolicySaveLocation, 'wb') as f:
                f.write(response.content)
                print(f"Tax Policy File was successfully saved at {TaxPolicySaveLocation}")
        else:
            print(f"Erorr getting download form url: {response.status_code}")
        # read in data to parase
        try:
            path = TaxPolicySaveLocation
            #start on main headers
            df = pd.read_excel(path,skiprows=6)
            # drop first row is empty
            df = df.drop(0)
            # resname lost columns
            df.rename(columns={"Unnamed: 0":"Fiscal Year","Total":"Receipts Total","Total.1":"Outlays Total","Total.2":"Surplus or Deficit(-) Total"},inplace=True)
            # get rid of dat at the end of table dealing wiith estimating data
            estimateIndex = df[df['Fiscal Year'].str.contains('Estimates',case=False,na=False)].index[0]
            df = df.iloc[:estimateIndex-2]
            df = df[df['Fiscal Year']!='TQ']
            df['Fiscal Year'] = df['Fiscal Year'].astype(int)
            df['Surplus or Deficit(-) Total'] = df['Surplus or Deficit(-) Total'] * 1_000_000

        except Exception as e:
            print(f"Error loading TaxPolicy file: {e}")
        return df
    


        
