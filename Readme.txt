Installation:

For a list/versions of installed python packages for the environment where this code was developed refer to "Installed Packages" file

Structure: 	

1. \Outlier\outlier.py: Main program
2. \Outlier\logging.conf: Configuration file the python logger
3. \Outlier\outlier.log: log file output from the python logger
4. \Outlier\modules\ contains modules imported by outlier.py 
5. \Outlier\modules\inputs.py: processes input data
6. \Outlier\modules\processing.py: core logic for assigning modified z-scores and methodology selection
7. \Outlier\modules\writing.py: processes output data and writes to file(s)
8. \Outlier\modules\config.py: stores constant values needed to execute the outlier code 

Example Call:

> python <Main program> <campaign Key> <Campaign ID> <Input Directory> <date of files>
> python D:\Outlier\outlier.py 1398 "001BUKq7AH" "D:\Outlier\input" "20180205"

Note: Exact Campaign Key is not needed to execute the code (any integer will do), which runs off the Campaign Id

<Input Directory>: This directory will contain 8 required input files of this structure: <Campaign Id>_<Subject Area>_yyyymmdd.json

In case of missing Halo files, the module will ignore the files and run the rest of the code

<Subject Area>: TVC, FeaturedRawSales, FeaturedBaseNormalized, FeaturedHistoryNormalized, FeaturedTwoFactorNormalized, HaloBaseNormalized, HaloHistoryNormalized, HaloTwoFactorNormalized

* Input files will be of json format key-value pairs, the keys are always store id in alpha-numeric format
* Multiple files for same campaign Id and subject area are allowed as long as their datestamps are different, the code will pick the set corresponding to the date indicated in the command line  

Outputs:

There are two output files created from this process, (1) a json file with ressults that define the Analytic Store List (2) A csv file with results for all possible tacctics and methodologies

(1) This Output file is written to the same directory as the input files, as read from the command line parameter. 

There is one output file for each campaign id, of the structure 
<Campaign Id>_ OutlierAnalysis_BestTvC_yyyymmdd.json where the date stamp is the same as the input files irrespective of when the outlier code is run, e.g. 001BVKq7AH_OutlierAnalysis_BestTvC_20180205.json

The output file contains three dictionaries: the first dictionary ("Method" dictionary) contains the Calculation Method Key (2,3 or 4) corresponding to the best methodology selected. 

The second dictionary (the "Tactic" Dictionary) is the {"Tactic":<Name>} key-value pair corresponding the selected outlier tactic (the best tactic out of 8)

The third dictionary (the "Stores" Dictionary) is the {<Store Id>:<Cluster Name>} key-value pairs corresponding the selected outlier tactic

(2) There is a second set of outputs that can be turned on from the config.py file, if OUTPUTALLTACTICS=True then all the tactics are written out to a single csv file defined in the ANALTYICSDIR and ANALYTICSFILE parameters in the config file. 
The results are appended to the same file defined by ALLCAMPAIGNSFILENAME. 

In addition, when OUTPUTALLTACTICS=True, all tactics for each campaign can be written to separate file(s) by setting OUTPUTCAMPAIGNFILE=True.
The output file structure will be <Campaign Id>_Outlier_Tactics_<Run Datetime>.csv

