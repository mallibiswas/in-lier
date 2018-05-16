# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 14:16:13 2018

@author: mallinath.biswas
"""

import logging
import sys
import os
import pandas as pd
import json
import numpy as np
 
module_logger = logging.getLogger("mainApp.inputs")

def read_file (filePath, valueVar):
    
    # reads contents of the input json files which are always {"storeid":"value"} format    
    with open(filePath) as datafile:
        data = json.load(datafile)
        
    df = pd.DataFrame({valueVar: data})    

    df.index.names = ['StoreID']
    
    df = df.replace([np.inf, -np.inf], np.nan) # replace infinity with nan
    
    return df



def handle_missing_Halo_files (dfDict, refDict):
    
    # configure logger
    logger = logging.getLogger("mainApp.inputs.add")

    haloDict = {k: v for k, v in refDict.items() if k.startswith('Halo')}
            
    for key, value in haloDict.items():
            df = pd.DataFrame (columns=['StoreID',value]) # Create null df to replace missing halo df
            logger.info("Handling Missing Data/File: {}".format(key))
            dfDict[key] = df
            
    return dfDict


def read_data (inputDir, campaign_id, fileDatestamp):
    
    # configure logger
    logger = logging.getLogger("mainApp.inputs.add")

    logger.info("Reading From %s" %(inputDir))
    
    # files Needed: TVC, FeaturedRawSales, 
    # FeaturedBaseNormalized, FeaturedHistoryNormalized, FeaturedTwoFactorNormalized
    # HaloBaseNormalized, HaloHistoryNormalized, HaloTwoFactorNormalized
        
    # these are also the data frame names
    fileDict = {'TVC':'ClusterName', 
                'FeaturedRawSales':'sale', 
                'FeaturedBaseNormalized':'NormSales_F', 
                'FeaturedHistoryNormalized':'NormSales_F', 
                 'FeaturedTwoFactorNormalized':'NormSales_F', 
                 'HaloBaseNormalized':'NormSales_H', 
                 'HaloHistoryNormalized':'NormSales_H', 
                 'HaloTwoFactorNormalized':'NormSales_H'}

    refFileList_ = list(fileDict.keys()) # list of file subject areas, also the data frame names
    refFileList = [] # this is the list with actual filenames to search for
    refSubjectArea = []  # this is the list with subject area to track in df, e.g. FeaturedTwoFactorNormalized
    
    for x in refFileList_:
        refFileList.append(campaign_id+"_"+x+"_"+fileDatestamp+".json")
        refSubjectArea.append(x)
    
    filesInDir = []
    for file in os.listdir(inputDir):
        if file.endswith(".json") and file.startswith(campaign_id):
            filesInDir.append(file) #list of files in the input directory
    
    logger.debug("Files in Dir: {}".format(filesInDir))
    
    campaignFiles = []
    campaignDfs = {}
    
    for each_file in filesInDir:
        logger.debug("Searching for match to file found in Dir: {}".format(each_file))     
        
        for fileName in refFileList:    
            logger.debug("Looking for File in Dir: {}".format(fileName))
            
            if fileName == each_file: 
                filePath = os.path.join(inputDir, each_file)
                
                # find corresponding subject area from index of matched file
                f = refSubjectArea[refFileList.index(fileName)]
                logger.debug("Matched Subject Area: {}".format(f))
                
                # read into df                
                df = read_file(filePath,fileDict[f]) # create df from file
                campaignDfs[f] = df # add to dict

                logger.debug("Read File: %s" %(each_file))
                
                # write to tracking dict
                campaignFiles.append({"dfName":f,
                                      "file":each_file,
                                      "DateStamp":fileDatestamp}) 

    # dictionary operations to find dups
    fileList = []
    
    for d in campaignFiles:
        fileList.append(d["file"]) # List of File Names found

    logger.debug("CampaignFiles: {}".format(campaignFiles))
    logger.debug("fileList: {}".format(fileList))

    # create dict of halo files in reference dict
    haloDict = {k: v for k, v in campaignDfs.items() if k.startswith('Halo')}
    
    # create dict of featured files in reference dict
#    featuredDict = {k: v for k, v in campaignDfs.items() if k.startswith('Featured')}

    if len(campaignFiles) == 0:
        logger.error("No files found for campaignId {} for {} in {}".format(campaign_id, fileDatestamp, inputDir))
        raise ValueError ("Expected input files missing:{}".format(refFileList))
                            
    # Check file name list against actual files avaiable of those names, at least 5 files should be available
    if len(campaignFiles) < 5:
        logger.error("Fewer than 5 input files found: {}".format(fileList))
        raise ValueError ("Required input file(s) mismatch in %s" %(inputDir))

    if (len(haloDict) == 0):
        logger.info("Note: Halo File(s) Missing in {} for {}".format(inputDir,fileDatestamp))
        campaignDfs = handle_missing_Halo_files (campaignDfs, fileDict)       
                
    return campaignDfs


def read_global_variables():

    # configure logger
    logger = logging.getLogger("mainApp.inputs.add")
    
    # sets global variables like campaignid from the command line to be used in the code
    if len(sys.argv) < 3:
        logger.error ("Invalid Arguments, need at lest 3 arguments (campaignKey, Campaign Id, directory path)")
        sys.exit(1)
    
    # load and read the command line arguments
    campaignKey = sys.argv[1]
    campaignID = sys.argv[2]    
    inDir = sys.argv[3]
    outDir = sys.argv[3]
    fileDate = sys.argv[4] # date extension for input files
    
    if not os.path.exists(outDir):
        logger.error ("Invalid directory path" %(outDir))
        raise ValueError

    logger.info("Read inputs for CampaignID: %s" %(campaignID))
    logger.info("CampaignKey: %s" %(campaignKey))
    logger.info("Input Directory: %s" %(inDir))
    logger.info("Output Directory: %s" %(outDir))

    return campaignKey, campaignID, inDir, outDir, fileDate

