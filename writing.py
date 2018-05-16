import pandas as pd
import json
import os
import logging
from modules import config

module_logger = logging.getLogger("mainApp.writing")

def write_all_results (campaign_id, df, fileDatestamp):
    
    # configure logger
    logger = logging.getLogger("mainApp.writing.add")

    if config.OUTPUTCAMPAIGNFILE:
        # Output a single campaign file for each campaign
        f = "{}_OutlierAnalysis_{}.csv".format(campaign_id,config.FILEDATETIME)
        outFile = os.path.join(config.OUTPUTDIR, f)
        df.to_csv(outFile, header=True)

    # output all tactics to single file
    df['AsofDate']=fileDatestamp
    df['UpdatedOn']=config.RUNDATETIME
    
    csvFile = os.path.join(config.OUTPUTDIR, config.ALLCAMPAIGNSFILENAME)    # full file name and path of output file
    
    if os.path.exists(csvFile):
        df.to_csv(csvFile, mode='a', header=False)
    else:
        df.to_csv(csvFile, mode='w', header=True)
        
    logger.info("Written csv files with all outcomes for:{}".format(campaign_id))


def write_tvc(outDir, result, store, campaignID, fileDatestamp):

    # configure logger
    logger = logging.getLogger("mainApp.writing.add")

    fn = '{}_OutlierAnalysis_BestTvC_{}.json'.format(campaignID, fileDatestamp)
    jsonFile = os.path.join(outDir, fn)    # full file name and path of output file
    
    flag = pd.Series(data=result.output_label, index=['0', 'High', 'Low'])
        
    store_subset = store.loc[~store.label.isin(flag.loc[flag == 0].index)]
    
    store_subset_ = store_subset.reset_index()   

    store_subset_["StoreID"] = store_subset_["StoreID"].astype(str)
    
    tvcOutput = store_subset_[['StoreID', 'ClusterName']]
    
    # write to json
    methodDict = {"CalculationMethodKey":str(result["methodKey"])}
    tacticDict = {"Tactic":str(result["action"])}    
    tvcDict = tvcOutput.set_index('StoreID')['ClusterName'].to_dict()    
    
    outDict = {"Method":methodDict,"Tactic":tacticDict,"Stores":tvcDict}      

    logger.info('Best Methodology Key: %s' %(outDict["Method"]["CalculationMethodKey"]))
    logger.info('Best Tactic: %s' %(outDict["Tactic"]["Tactic"]))

    with open(jsonFile, 'w') as f:
        json.dump(outDict, f)
        
    logger.info("Created json file: %s" %(jsonFile))
