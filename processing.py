import logging
import pandas as pd
from scipy import stats
import numpy as np
from modules import config

module_logger = logging.getLogger("mainApp.processing")

def cal_modified_zscore(series):
    
    # configure logger
    logger = logging.getLogger("mainApp.processing.add")
    
    """
    Calculate modified z-scores.
    Formula: M_i = 0.6745(x_i-median) / MAD. Where MAD is median absolute deviation.
    """
    df = series.to_frame(name='x')
    median = df.x[(df.x.notnull()) & (df.x != 0)].median()
    df.abs_diff = abs(df.x - median)
    mad = df.abs_diff[(df.x.notnull()) & (df.x != 0)].median()
    m = 0.6745 * df.abs_diff / mad  # Modified z-scores

    logger.debug("Created modified zscores")
    
    return m

def cal_lift(test, control):
    
    # configure logger
    logger = logging.getLogger("mainApp.processing.add")
    
    """
    Calculating lift.
    Args:
        test: input dataframe for test data.
        control: input dataframe for control data.
    Output:
        lift: Interger represent lift value.
    """
	
    if control.mean() == 0:
        lift = config.ERROR_TSHLD
    else:
        lift = test.mean() / control.mean()
    
    logger.debug("Created Lifts")
                
    return lift

def cal_incr_sales (lift, totalSales):

    if lift == config.ERROR_TSHLD: 
        incr_sales = np.NaN
    else:        
        incr_sales = (1-1/lift)*totalSales
    
    return incr_sales
    
def label_store(df):
    
    # configure logger
    logger = logging.getLogger("mainApp.processing.add")
    
    # 0 and Nan
    df['label'] = 'undefined'
    df.loc[df.NormSales_F == 0, 'label'] = '0'
    df.loc[df.NormSales_F.isnull(), 'label'] = 'NULL'
    df.loc[df.NormSales_F == np.inf, 'label'] = 'NULL'
    # High outliers based on Ratio and low outliers based on reciprocal
    df['z_score'] = cal_modified_zscore(df.NormSales_F)
    df.ix[df.label == 'undefined', 'reciprocal'] = 1 / df.NormSales_F
    df['rec_z_score'] = cal_modified_zscore(df.reciprocal)
    df.ix[(df.z_score > 3.49) & (df.label == 'undefined'), 'label'] = 'High'
    df.ix[(df.rec_z_score > 3.49) & (df.label == 'undefined'), 'label'] = 'Low'
    df.ix[df.label == 'undefined', 'label'] = 'Good'

    logger.debug("Created labels")

    return df[['NormSales_F', 'NormSales_H', 'label']]

def get_Store_Subset_Counts (df):

    counts = df['ClusterName'].value_counts().transpose()
    
    try:    
        Test_Stores = counts['T']
    except KeyError as e:
        Test_Stores = 0
    try:        
        Control_Stores = counts['C']
    except KeyError as e:
        Control_Stores = 0        
    
    return Test_Stores, Control_Stores
    
def cal_diff_selection (store, total_test_sales):

    # configure logger
    logger = logging.getLogger("mainApp.processing.add")

    store = store[store.label != 'NULL']
    flag = pd.Series(index=['0', 'High', 'Low'])
    label_map = pd.Series(data=['RemoveAll', 'RemoveHighLow', 'Remove0Low', 'RemoveLow', 'Remove0High', 'RemoveHigh',
                                'Remove0', 'DoNothing'], index=[0, 1, 2, 3, 4, 5, 6, 7])
    all_stat = pd.DataFrame(columns=['DoNothing', 'Remove0', 'RemoveHigh', 'RemoveLow',
                                     'Remove0High', 'Remove0Low', 'RemoveHighLow', 'RemoveAll'],
                            index=['lift_F', 'lift_H', 'p_value', 'IS', 'TestStores','ControlStores','count_diff', 'output_label'])
    for i in [0, 1]:
        for j in [0, 2]:
            for k in [0, 4]:
                flag['0':'Low'] = i, j, k
                
                store_subset = store.loc[~store.label.isin(flag.loc[flag == 0].index)]
                outlier_label = label_map.iloc[i+j+k]
                
                all_stat.loc['lift_F', outlier_label] = cal_lift(store_subset.loc[store_subset.ClusterName == 'T', 'NormSales_F'],
                                                               store_subset.loc[store_subset.ClusterName == 'C', 'NormSales_F'])
                all_stat.loc['lift_H', outlier_label] = cal_lift(store_subset.loc[store_subset.ClusterName == 'T', 'NormSales_H'],
                                                               store_subset.loc[store_subset.ClusterName == 'C', 'NormSales_H'])
                
                # Calculcate P-Value for tactic
                t_stat, p_value = stats.ttest_ind(store_subset.loc[store_subset.ClusterName == 'T', 'NormSales_F'],
                                                  store_subset.loc[store_subset.ClusterName == 'C', 'NormSales_F'])
                all_stat.loc['p_value', outlier_label] = p_value/2

                # Calculate Incremental Sales for tactic                
                lift = all_stat.loc['lift_F', outlier_label]
                incr_sales = cal_incr_sales (lift,total_test_sales)
                all_stat.loc['IS', outlier_label] = incr_sales
                
                # Calculate Test and Control Store counts in tactic                
                test_stores, control_stores = get_Store_Subset_Counts (store_subset)                    
                all_stat.loc['TestStores', outlier_label] = test_stores
                all_stat.loc['ControlStores', outlier_label] = control_stores
                
                all_stat.loc['count_diff', outlier_label] = (len(store) - len(store_subset))/len(store)
                all_stat.loc['output_label', outlier_label] = flag.tolist()

    logger.debug("Created Metrics in cal_diff_selection: lift_F lift_H p-value IS count_diff and output_label")
                
    return all_stat


def cal_result (tvc_cluster, method_ratio, total_test_sales):

    # configure logger
    logger = logging.getLogger("mainApp.processing.add")
    
    method_ratio = label_store(method_ratio) # assign labels corresponding to modified Z scores
    method_ratio = pd.merge(tvc_cluster, method_ratio, how='left', left_index=True, right_index=True) # actual stores scanned by ClusterName

    if len(method_ratio) == 0:
        logger.error('Can not find SPR information')
        raise ValueError
    elif len(method_ratio[method_ratio.label.isin(['0', 'NULL'])]) == len(method_ratio):
        logger.error('For total featured item, all stores have zero SPR or NULL SPR.')
        raise ValueError
    else:
        all_stat = cal_diff_selection(method_ratio, total_test_sales)        
        all_stat.loc['action', :] = all_stat.columns

    logger.debug("Created all_stat and method_ratio in cal_result")
        
    return all_stat, method_ratio


def find_min_p (hist_stat, base_stat, two_factor_stat):

    # configure logger
    logger = logging.getLogger("mainApp.processing.add")
    logger.info("Running min P-Value methodology selection logic")
    
    hist_stat = hist_stat.loc[:, (hist_stat.loc['count_diff'] <= config.STORECT_TSHLD) & (hist_stat.loc['lift_F'] > 1)]
    base_stat = base_stat.loc[:, (base_stat.loc['count_diff'] <= config.STORECT_TSHLD) & (base_stat.loc['lift_F'] > 1)]
    two_factor_stat = two_factor_stat.loc[:, (two_factor_stat.loc['count_diff'] <= config.STORECT_TSHLD) & (two_factor_stat.loc['lift_F'] > 1)]
    all_method = pd.concat([hist_stat, base_stat, two_factor_stat], axis=1)
        
    if all_method.empty:
        logger.info("No valid data to run min-P selector, returning default from find_min_p")
        return all_method
    else:
        all_method.columns = range(len(all_method.columns))
        min_p = all_method.loc[:, all_method.loc['p_value'].idxmin(axis=1)]
        logger.info("Found min_p in find_min_p")

        return min_p


def find_best_method (hist_stat, base_stat, two_factor_stat):

    # configure logger
    logger = logging.getLogger("mainApp.processing.add")
    logger.info("Running best-lift methodology selection logic")
    
    # data prep
    hs=hist_stat.transpose() 
    hs.set_index(['action','method'], inplace=True)
    bs=base_stat.transpose() 
    bs.set_index(['action','method'], inplace=True)
    tf=two_factor_stat.transpose() 
    tf.set_index(['action','method'], inplace=True)
    
    df = pd.concat([hs,bs,tf]) 

    if df.empty:
        return df

    # split by Halo and Featured and then combine with single lift column    
    dfF = df[['lift_F','output_label','p_value','count_diff','methodKey','TestStores','ControlStores']].copy()
    dfF['AggregateType'] = 'Featured'
    dfF.rename(columns={'lift_F':'lift'}, inplace=True)   
    
    dfH = df[['lift_H','output_label','p_value','count_diff','methodKey','TestStores','ControlStores']].copy()
    dfH['AggregateType'] = 'Halo'    
    dfH.rename(columns={'lift_H':'lift'}, inplace=True)   
    
    _df = dfF.append(dfH)

    _df['lift_multipler'] = _df['lift'] # fix the nomenclature
    _df['lift'] = _df['lift_multipler'] - 1
                
    _df['Delta'] = config.LIFT_TSHLD - _df['lift'] # Lift below threshold are negative
    _df['Delta'] = _df['Delta'].abs() # take the absolute delta from threshold

    # Sort dataframe by aggregate type and delta descending
    _df.sort_values(['AggregateType','Delta'], axis=0, ascending=True, inplace=True, kind='quicksort', na_position='last')

    _df.reset_index(inplace=True)

    default = _df.iloc[0] # default result = 1st record
    
    for i, rec in _df.iterrows():
        if rec['count_diff'] <= config.STORECT_TSHLD and rec['lift'] > 0: 
            logger.info("Found non-default best_methodology")
            return rec

    logger.info("Selecting default methodology")
        
    return default



def find_original(hist_donothing, base_donothing, two_factor_donothing):
    
    # configure logger
    logger = logging.getLogger("mainApp.processing.add")
    
    df = pd.concat([hist_donothing, base_donothing, two_factor_donothing], axis=1)
    df.columns = range(len(df.columns))
    df.loc['Delta'] = df.loc['lift_F']-(1+config.LIFT_TSHLD)
    df.loc['Delta'] = abs(df.loc['Delta'])
    original = df.loc[:, (df.loc['count_diff'] <= config.STORECT_TSHLD) & (df.loc['lift_F'] > 1)]

    logger.info("Extracting original (default) list")
    
    if original.empty:
        return df.loc[:, df.loc['Delta'].idxmin(axis=1)]
    else:
        return original.loc[:, original.loc['Delta'].idxmin(axis=1)]
    
    
def create_output_store_list (df, original, base_label, hist_label, two_factor_label):
    
    # configure logger
    logger = logging.getLogger("mainApp.processing.add")

    # create final TvC store list based on results    
    logger.info("Created output store list")
    
    if df.empty or df.action is "DoNothing":
        if original.method == 'History':
            return original, hist_label
        elif original.method == 'Base':
            return original, base_label
        elif original.method == 'Two Factor':
            return original, two_factor_label
    else:
        if df.method == 'History':
            return df, hist_label
        elif df.method == 'Base':
            return df, base_label
        elif df.method == 'Two Factor':
            return df, two_factor_label
    
    