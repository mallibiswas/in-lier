# -*- coding: utf-8 -*-
"""
Created on Fri Feb  9 11:38:19 2018

@author: mallinath.biswas

Configure global constants

"""
import datetime
import time

#
######################## CONSTANTS: DO not edit ########################################
#
LIFT_TSHLD = 0.2 # Look for results closest to 20% lift
STORECT_TSHLD = 0.4 # Groups where at least this % of stores have scanned the products
ERROR_TSHLD=1e-10 # to handle divide by 0 in incr sales when lift is missing
METHODOLOGY_DICT = {"Base":"2","History":"3","Two Factor":"4"} # map methodology to key
RUNDATETIME=datetime.datetime.fromtimestamp(time.time()).strftime('%m/%d/%Y %H:%M:%S')
FILEDATETIME=datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S')
#
######################## VARIABLES #####################################################
#
METHODOLOGY_SELECTOR="BestLift" # two valid values "BestLift" and "MinP"
OUTPUTALLTACTICS=True # When set to True this will output csv files for analysis in the OUTPUTDIR into ALLCAMPAIGNSFILENAME
OUTPUTCAMPAIGNFILE=False # Set to True when single files at campaign level are needed
OUTPUTDIR="C:\\Users\\mallinath.biswas\\Documents\\Outlier\\output"
ALLCAMPAIGNSFILENAME="OutlierAnalysis_All_Tactics.csv"
