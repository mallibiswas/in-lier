import pandas as pd
import logging
import logging.config
from os import path

from modules import processing
from modules import writing
from modules import inputs           
from modules import config           


def setLogger (configFile):
    
    # setup logger Based on http://docs.python.org/howto/logging.html#configuring-logging    
    config_file_path = path.join(path.dirname(path.abspath(__file__)), configFile)
    if path.isfile(config_file_path) is False:
        raise Exception("Config file {} not found".format(config_file_path))
    else:
        logging.config.fileConfig(config_file_path) 
    logger = logging.getLogger("mainApp")

    logger.propagate = True # turn off upper logger including console logging

    return logger


def main (df_dict, campaignID, methodology_selector):
    
    # Read TvC Cluster and Raw Sales
    TVC = df_dict["TVC"]
    FeaturedRawSales = df_dict["FeaturedRawSales"]
    # Normalized Sales for Featured Products
    FeaturedBaseNormalized = df_dict["FeaturedBaseNormalized"]
    FeaturedHistoryNormalized = df_dict["FeaturedHistoryNormalized"]
    FeaturedTwoFactorNormalized = df_dict["FeaturedTwoFactorNormalized"]
    # Normalized Sales for Halo Products
    HaloBaseNormalized = df_dict["HaloBaseNormalized"]
    HaloHistoryNormalized = df_dict["HaloHistoryNormalized"]
    HaloTwoFactorNormalized = df_dict["HaloTwoFactorNormalized"]
    
    # merge featured and halo datasets
    hist_normalized = pd.merge(FeaturedHistoryNormalized, HaloHistoryNormalized, how='left', left_index=True, right_index=True)
    base_normalized = pd.merge(FeaturedBaseNormalized, HaloBaseNormalized, how='left', left_index=True, right_index=True)
    two_factor_normalized = pd.merge(FeaturedTwoFactorNormalized, HaloTwoFactorNormalized, how='left', left_index=True, right_index=True)

    # get total featured sales by cluster type
    total_sales = pd.merge(TVC, FeaturedRawSales, how='left', left_index=True, right_index=True) # $ total sales by storeid and cluster type
    
    total_test_sales = total_sales.loc[total_sales.ClusterName == 'T', 'sale'].sum() # $ total test sales by storeid
        
    hist_stat, hist_label = processing.cal_result(TVC, hist_normalized, total_test_sales)
    base_stat, base_label = processing.cal_result(TVC, base_normalized, total_test_sales)
    two_factor_stat, two_factor_label = processing.cal_result(TVC, two_factor_normalized, total_test_sales)
    
    hist_stat.loc['method', :] = 'History'
    base_stat.loc['method', :] = 'Base'
    two_factor_stat.loc['method', :] = 'Two Factor'

    # Map methods to keys from dictionary
    hist_stat.loc["methodKey", :] = hist_stat.loc["method", :].map(config.METHODOLOGY_DICT)
    base_stat.loc["methodKey", :] = base_stat.loc["method", :].map(config.METHODOLOGY_DICT)
    two_factor_stat.loc["methodKey", :] = two_factor_stat.loc["method", :].map(config.METHODOLOGY_DICT)

    all_methods = pd.concat([base_stat.transpose(), hist_stat.transpose(), two_factor_stat.transpose()])
    all_methods['campaignID']=campaignID # Track campaign id in column
    
    original = processing.find_original (hist_stat.DoNothing, base_stat.DoNothing, two_factor_stat.DoNothing)

    if methodology_selector is "BestLift":
    
        best_lift = processing.find_best_method (hist_stat, base_stat, two_factor_stat)        
        result, store = processing.create_output_store_list (best_lift, original, base_label, hist_label, two_factor_label)
            
    elif methodology_selector is "MinP":    
        
        min_p = processing.find_min_p (hist_stat, base_stat, two_factor_stat)
        result, store = processing.create_output_store_list (min_p, original, base_label, hist_label, two_factor_label)
        
    else:
        logger.error('Invalid Methodology Selector: valid values are BestLift or MinP')
        raise ValueError

    return result, store, all_methods

        
if __name__ == '__main__':

#################################################################################################
#   Main Program
#################################################################################################
    
    logger = setLogger('logging.conf')    
     
    # initialize global variables
    campaignKey, campaignID, inputDir, outputDir, fileDatestamp = inputs.read_global_variables()
    
    logger.info('Processing outlier for Campaign: {}'.format(campaignID))
            
    # read input files and set them as dataframes    
    campaign_df_dict = inputs.read_data (inputDir, campaignID, fileDatestamp)
    
    result, store, all_methods = main (campaign_df_dict, campaignID, methodology_selector=config.METHODOLOGY_SELECTOR)

    logger.info(result)

    writing.write_tvc(outputDir, result, store, campaignID, fileDatestamp)
    
    if config.OUTPUTALLTACTICS:
        writing.write_all_results(campaign_id=campaignID, df=all_methods, fileDatestamp=fileDatestamp)

