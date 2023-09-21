# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 10:01:38 2015

@author: a001985
===============================================================================
NEW COMMENTS
updated 2023-09-21, Found a bugg with the naming of LIMS-job. Wrong self.ship, should be self.ship_intern_ID and an error with self.serie. Use self.serie_no instead. /MHan
updated 2023-05-12, Added UMF SBE19 (6929) and its config (with fluoremeter, chla and turb and PAR). Changed to a new path to the server onboard Svea /MHan
updated 2022-10-27, Update of header, latitude, remove position format and fix range problems when read in ODV /MHan
updated 2019-04-01, Added some lines to dialog.py that fix if there is more than 100 series in a cruise. the series continues then on next cruise nr. 04.105-> 0505 /MHan
updated 2017-12-15, Added unit to PAR/Irradiance [µE/cm^2*s] and added Chla and Phycocyanin to the different fluorometers. /MHan
updated 2017-12-14, changed the LIMS-id and added _SYNK to the name accoring to LIMS needs for CTD-import./MHAN
updated 2017-06-17, added auto-plots of seaplot, ts-diff, oxy_diff and fluor_turb_par. /MHAN
updated 2017-05-20, added a fourth column in self.cnv_column_info with value 0 or 1, 1 means no change, 0 means all values from this sensor will be replaced by default bad value -9.990e-29. Also updated true depth calculation to use secondary sigmaT if primary sigmaT has flag 0 /OBac
updated 2016-11-24, updated dialog.py and this script to handle also Dana CTD and also already processed CTDs to be reprocessed. Have removed making of shark import file.
updated 2016-08-24, updated dialog.py to handle a wider arrange of different Seabird CTDs. When calling checkCtdFileName() it now requires an input for CTD number, for example checkCtdFileName(ctd='1044'). Easiest is to supply this number in "__init__" /OBac
updated 2016-03-16, added support for 4 digit series in the ctd file name. /OBac
updated 2016-01-07, Adjusted the script for new CTD 1044 and new parameters. /MHAN
updated 2015-11-10, added a method to read the .bl file (self.check_bl()) to see if any bottles were fired, skips bottlesum if no bottles were fired. /OBac
updated 2015-11-10, added try and except for moving .btl and .ros file, if no bottle is fired these files will be missing. /OBac
updated 2015-11-09, updated BottleSum to work and added automatic move of the .btl and .ros file. /OBac
updated 2015-10-18, added Bottle Summary, i.e. BottleSum /JKro
updated 2015-04-22, Changed number of decimals for PAR. Format now '%11.3e'
updated 2015-04-22, Changed the program so that the format only needs to be changed in one place. /MWen

===============================================================================
OLD COMMENTS
updated 2015-03-21, added Turbidity column to test_file. /MWen
updated 2015-03-20, added parameter Turbidity, (changed columns for shark-file) /MWen
updated 2015-02-10, correction of true depth calculation, and adding correct min/max span. /OBac
updated 2014,       added parameter PAR, /OBac. 
updated 2013-10-25, changed the outputfiles, because of changed CTD to 0745. /Mhan
updated 2013-02-12, for new ctd-format and new con-file format.
updated 2013-01-28, for new year 2013. Add new folders with new year C:\ctd\data\year och C:\ctd\raw
updated 2012-03-21, when NMEA was added. /Mhan
updated 2012-10-16, changed the outputfiles, because of changed sensors on CTD. /Mhan
===============================================================================
"""

from readCTD import readCNV
from dialog_SBE19 import checkCtdFileName
import os
import numpy as np
import matplotlib.mlab as ml
from re import split
from time import gmtime, strftime
import shutil
import codecs
from stationnames_in_plot import insert_station_name as insert_station_name

class CtdProcessing(object):
    """
    If you add an instrument to the CTD you have to do two things: 
        
    1 - Add a new line to "self.cnv_column_info" under method "load_options". 
        The new line must have the format: [col_nr, format, parameter_name, 1]
    2 - Update the col_nr (firs element in each row) so that the number matches 
        the column in the cnv-file.
        
    If some sensor gives bad data: change the "one" in the fourth column 
    in self.cnv_column_info to a "zero", this will replace all values from the
    sensor to default bad value.
    
    Surface Soak
    Normally the CTD is soaked to 7-8 m before the CTD is taken to the surface
    to start the cast. CTD from DANA has another procedure, hence there is 
    special loop-edit file for this which is used if files are from Dana. 
    If its a normal CTD-cast the options below: 
    should be: 
    
    self.manuell_surfacesoak = False #normalt False
    
    If you need to reprocess a CTD-file due to a mistake in the CTD-procedure 
    so there is no surface values or other, change below :
     
    self.manuell_surfacesoak = True #normalt False
    
    After that open the file: ctd\setup\LoopEdit_shallow.psa and 
    change the needed settings. Open the file through SBE Data Processing
    and change surface soak settings in:
        SBE Data Processing -> Loop edit -> Data set up
    And rerun the program. 
    
    OBS! Note that you have to change back to False when your done. 
    
    20191209: Trying this also when soaking extra deep: 20m /OBac
    Have to set minimum soak depth to deeper than shallowest CTD depth 
    for this to work, but then it seems to work fine. /OBac
    Use deep_surfacesoak = True for this, calls LoopEdit_deep.psa /OBac
    
    """
    # Surface Soak   
    manuell_surfacesoak = False #normalt False        
    deep_surfacesoak = False #normalt False, vid soak omkring 15m vid hög sjö sätt denna till True
    
    #Välj CTD
    ctdnumber = '6929'       #UMFs SBE19
    #ctdnumber = '6164'      #SMHIs SBE19    
    #ctdnumber = '1044'
    #ctdnumber = '0745'
    #ctdnumber = '0817'    #FMI
    #ctdnumber = '0403'   #Dana 1 
    #ctdnumber = '0827'   #Dana 2
    #ctdnumber = '9675' 
    #Dana 99675, har tagit bort första 9:an för att det skall vara samma 
    #antal siffror som våra CTD:er. /MHan    
            
    ctdconfig = '.XMLCON'
    print ctdnumber
    
    def __init__(self):

#        if self.ctdnumber == '6164':
#            self.file_path = 'C:\\ctdSBE19\\temp\\'            
#            self.fname = 'SBE19plus_01906164_2020_09_22_0006.xml'            
#                                    
#            os.rename(file_path, path + '\\' + new_fname + '.hdr')
#            self.ctdNo = '6164'
#            self.cnty = '77'
#            self.ship = '10'
#            self.serieNo = '0006'
#            self.year = '20'
#            self.number_of_bottles = 0
#            self.new_fname = 'SBE19_' + self.ctdNo + '_' + '20200919_1420' + '_' + self.cnty + '_' + self.ship + '_' + self.serieNo
#            self.serieNo
#            self.stationname = 'TEST1'
#            
#            self.load_options()
#            self.create_batch_file()
#            self.run_seabird()
#            self.modify_cnv_file()
#            
#        else:
#            self.get_file()
#            self.load_options()
#            self.check_bl()
#            self.create_batch_file()
#            self.run_seabird()
#            self.modify_cnv_file()
        
        self.get_file()               
        self.load_options()
        self.check_bl()
        self.create_batch_file()
        self.run_seabird()
        self.modify_cnv_file()
        #self.make_LIMS_export_file()
        # this runs only on data from Svea, if processing Svea data on land you can comment this line /OBac
        self.copy_files_to_server()
        
            
        if self.manuell_surfacesoak == True:
            print 'NOTE! The setup for surface soak is changed to manual if you dont know what you are doing contact the cruise leader.'
        if self.deep_surfacesoak == True:
            print 'NOTE! The setup for surface soak is changed to deep if you dont know what you are doing contact the cruise leader.'
        
        print 'Done!'


    #==========================================================================    
    def get_file(self):
        # Call program to get and check file name and also get serial number
        self.fname, self.serie_no, self.stationname = checkCtdFileName(ctd=self.ctdnumber, confile=self.ctdconfig)
        self.stationname = self.stationname.replace(' ','_')
        self.stationname = self.stationname.replace('/','-')
        
        self.new_fname = self.fname.split('.')[0]
        
        self.year = self.fname[13:15]
        if self.new_fname[27:28] == '_':
            self.ship = self.new_fname[28:30]
        else:
            self.ship = self.new_fname[27:29]
        self.cnty = self.new_fname[25:27]
        #end_position = len(self.new_fname)
        #self.serie = self.new_fname[33:end_position] 
        self.ctdNo = self.new_fname[6:10]
                       
        if self.ship == 'SE':
            self.ship_intern_ID = '10'
        else:
            self.ship_intern_ID = 'ID'

               
    #==========================================================================    
    def load_options(self):
        
        # Directories
        self.working_directory = 'C:\\ctdSBE19\\temp\\'
        self.data_directory = 'C:\\ctdSBE19\\data\\'
        self.raw_files_directory = 'C:\\ctdSBE19\\raw\\'
        self.plot_directory = 'C:\\ctdSBE19\\plots\\'
        #self.shark_file_directory = '\\\\SMHI-AR-SHARK1\\ctd\\seabird\\'
        #self.shark_file_directory_lokal = 'C:\\ctd\\data\\sharkimport\\'
        
        # Files
        self.ctdmodule_file = 'ctdmodule.txt'
        self.batch_file = 'SBE_batch.bat'
        
        if self.ctdNo == '1044' or self.ctdNo == '0745':                
            #OBS! Om något ändrats på CTDn, ex bytt sensorer, kör Seabirds program manuellt och titta på cnv-filen och uppdatera formatet nedan.
            #   [col,   'format',   'parameter name']
            
            # if sensor pair 1 is bad, change flag in fourth column to 0
            # columns as of 2017-05-20: 2,4,5,8,15,17,18,23
            
            self.cnv_column_info = [
            [0,     '%11u',     'scan: Scan Count', 1],
            [1,     '%11.3f',   'prDM: Pressure, Digiquartz [db]', 1],
            [2,     '%11.4f',   't090C: Temperature [ITS-90, deg C]', 1],
            [3,     '%11.4f',   't190C: Temperature, 2 [ITS-90, deg C]', 1],
            [4,     '%11.4f',   'T2-T190C: Temperature Difference, 2 - 1 [ITS-90, deg C]', 1],
            [5,     '%11.5f',   'c0S/m: Conductivity [S/m]', 1],
            [6,     '%11.5f',   'c1S/m: Conductivity, 2 [S/m]', 1],
            [7,     '%11u',     'pumps: Pump Status', 1],
            [8,     '%11.4f',   'sbeox0ML/L: Oxygen, SBE 43 [ml/l]', 1],
            [9,     '%11.4f',   'sbeox1ML/L: Oxygen, SBE 43, 2 [ml/l]', 1],
            [10,    '%11.2f',   'altM: Altimeter [m]', 1],
            [11,    '%11.4f',   'flECO-AFL: Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]', 1],
            [12,    '%11.4f',   'flECO-AFL1: Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]', 1],
            [13,    '%11.3e',   'par: PAR/Irradiance, Biospherical/Licor', 1],
            [14,    '%11.7f',   'turbWETntu0: Turbidity, WET Labs ECO [NTU]', 1],
            [15,    '%11.4f',   'sal00: Salinity, Practical [PSU]', 1],
            [16,    '%11.4f',   'sal11: Salinity, Practical, 2 [PSU]', 1],
            [17,    '%11.4f',   'secS-priS: Salinity, Practical, Difference, 2 - 1 [PSU]', 1],
            [18,    '%11.4f',   'sigma-t00: Density [sigma-t, kg/m^3 ]', 1],
            [19,    '%11.4f',   'sigma-t11: Density, 2 [sigma-t, kg/m^3 ]', 1],
            [20,    '%11.3f',   'depSM: Depth [salt water, m], lat ', 1],
            [21,    '%11.3f',   'depFM: Depth [true depth, m], lat ', 1],
            [22,    '%11.3f',   'dz/dtM: Descent Rate [m/s], WS ', 1],
            [23,    '%11.2f',   'svCM: Sound Velocity [Chen-Millero, m/s]', 1],
            [24,    '%11.2f',   'svCM1: Sound Velocity, 2 [Chen-Millero, m/s]', 1],
            [25,    '%11.3e',   'flag: flag', 1]]
            
# Original:            
#            [0,     '%11u',     'scan: Scan Count'],
#            [1,     '%11.3f',   'prDM: Pressure, Digiquartz [db]'],
#            [2,     '%11.4f',   't090C: Temperature [ITS-90, deg C]'],
#            [3,     '%11.4f',   't190C: Temperature, 2 [ITS-90, deg C]'],
#            [4,     '%11.4f',   'T2-T190C: Temperature Difference, 2 - 1 [ITS-90, deg C]'],
#            [5,     '%11.5f',   'c0S/m: Conductivity [S/m]'],
#            [6,     '%11.5f',   'c1S/m: Conductivity, 2 [S/m]'],
#            [7,     '%11u',     'pumps: Pump Status'],
#            [8,     '%11.4f',   'sbeox0ML/L: Oxygen, SBE 43 [ml/l]'],
#            [9,     '%11.4f',   'sbeox1ML/L: Oxygen, SBE 43, 2 [ml/l]'],
#            [10,    '%11.2f',   'altM: Altimeter [m]'],
#            [11,    '%11.4f',   'flECO-AFL: Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]'],
#            [12,    '%11.4f',   'flECO-AFL1: Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]'],
#            [13,    '%11.3e',   'par: PAR/Irradiance, Biospherical/Licor'],
#            [14,    '%11.7f',   'turbWETntu0: Turbidity, WET Labs ECO [NTU]'],
#            [15,    '%11.4f',   'sal00: Salinity, Practical [PSU]'],
#            [16,    '%11.4f',   'sal11: Salinity, Practical, 2 [PSU]'],
#            [17,    '%11.4f',   'secS-priS: Salinity, Practical, Difference, 2 - 1 [PSU]'],
#            [18,    '%11.4f',   'sigma-t00: Density [sigma-t, Kg/m^3 ]'],
#            [19,    '%11.4f',   'sigma-t11: Density, 2 [sigma-t, Kg/m^3 ]'],
#            [20,    '%11.3f',   'depSM: Depth [salt water, m], lat '],
#            [21,    '%11.3f',   'depFM: Depth [true depth, m], lat '],
#            [22,    '%11.3f',   'dz/dtM: Descent Rate [m/s], WS '],
#            [23,    '%11.2f',   'svCM: Sound Velocity [Chen-Millero, m/s]'],
#            [24,    '%11.2f',   'svCM1: Sound Velocity, 2 [Chen-Millero, m/s]'],
#            [25,    '%11.3e',   'flag: flag']
        #----------------------------------------------------------------------

#----------------------------------------------------------------------
        #Svea CTD      
        if self.ctdNo == '1387':
            #OBS! Om något ändrats på CTDn, ex bytt sensorer, kör Seabirds program manuellt och titta på cnv-filen och uppdatera formatet nedan.
            #   [col,   'format',   'parameter name']            
            
            self.cnv_column_info = [
            [0,     '%11u',     'scan: Scan Count', 1],
            [1,     '%11.3f',   'prDM: Pressure, Digiquartz [db]', 1],
            [2,     '%11.4f',   't090C: Temperature [ITS-90, deg C]', 1],
            [3,     '%11.4f',   't190C: Temperature, 2 [ITS-90, deg C]', 1],           
            [4,     '%11.5f',   'c0S/m: Conductivity [S/m]', 1],
            [5,     '%11.5f',   'c1S/m: Conductivity, 2 [S/m]', 1],
            [6,     '%11u',     'pumps: Pump Status', 1],
            [7,     '%11.4f',   'sbeox0V: Oxygen raw, SBE 43 [V]', 1],
            [8,     '%11.4f',   'sbeox1V: Oxygen raw, SBE 43, 2 [V]', 1],
            [9,     '%11.2f',   'altM: Altimeter [m]', 1],
            [10,    '%11.3f',   'dz/dtM: Descent Rate [m/s]', 1],
            [11,    '%11.4f',   'flECO-AFL: Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]', 1],
            [12,    '%11.4f',   'flECO-AFL1: Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]', 1],
            [13,    '%11.3e',   'par: PAR/Irradiance, Biospherical/Licor', 1],
            [14,    '%11.7f',   'turbWETntu0: Turbidity, WET Labs ECO [NTU]', 1],
            [15,    '%11.4f',   'sal00: Salinity, Practical [PSU]', 1],
            [16,    '%11.4f',   'sal11: Salinity, Practical, 2 [PSU]', 1],
            [17,    '%11.4f',   'secS-priS: Salinity, Practical, Difference, 2 - 1 [PSU]', 1],
            [18,    '%11.4f',   'T2-T190C: Temperature Difference, 2 - 1 [ITS-90, deg C]', 1],
            [19,    '%11.4f',   'sigma-t00: Density [sigma-t, kg/m^3 ]', 1],
            [20,    '%11.4f',   'sigma-t11: Density, 2 [sigma-t, kg/m^3 ]', 1],
            [21,    '%11.3f',   'depSM: Depth [salt water, m], lat ', 1],
            [22,    '%11.3f',   'depFM: Depth [true depth, m], lat ', 1],        
            [23,    '%11.2f',   'svCM: Sound Velocity [Chen-Millero, m/s]', 1],
            [24,    '%11.2f',   'svCM1: Sound Velocity, 2 [Chen-Millero, m/s]', 1],
            [25,    '%11.4f',   'sbeox0ML/L: Oxygen, SBE 43 [ml/l], WS = 2', 1],
            [26,    '%11.4f',   'sbeox1ML/L: Oxygen, SBE 43, 2 [ml/l], WS = 2', 1],
            [27,    '%11.4f',   'sbeox0PS: Oxygen, SBE 43 [% saturation], WS = 2', 1],
            [28,    '%11.4f',   'sbeox1PS: Oxygen, SBE 43, 2 [% saturation], WS = 2', 1],
            [29,    '%11.3e',   'flag: flag', 1]]                                   
                           
        #----------------------------------------------------------------------

        #Seabird 19    SMHIs
        if self.ctdNo == '6164':
            #OBS! Om något ändrats på CTDn, ex bytt sensorer, kör Seabirds program manuellt och titta på cnv-filen och uppdatera formatet nedan.
            #   [col,   'format',   'parameter name']            
            
            self.cnv_column_info = [
            [0,     '%11u',     'scan: Scan Count', 1],
            [1,     '%11.3f',   'prdM: Pressure, Strain Gauge [db]', 1],
            [2,     '%11.4f',   'tv290C: Temperature [ITS-90, deg C]', 1],       
            [3,     '%11.5f',   'c0S/m: Conductivity [S/m]', 1],
            [4,     '%11.4f',   'sbeox0V: Oxygen raw, SBE 43 [V]', 1],
            [5,     '%11.3f',   'dz/dtM: Descent Rate [m/s]', 1],
            [6,     '%11.4f',   'sal00: Salinity, Practical [PSU]', 1],
            [7,     '%11.4f',   'density00: Density [density, kg/m^3]', 1],
            [8,     '%11.4f',   'sigma-é00: Density [sigma-theta, kg/m^3]', 1],
            [9,     '%11.3f',   'depSM: Depth [salt water, m], lat ', 1],
            [10,    '%11.3f',   'depFM: Depth [true depth, m], lat ', 1],        
            [11,    '%11.2f',   'svCM: Sound Velocity [Chen-Millero, m/s]', 1],
            [12,    '%11.4f',   'sbeox0ML/L: Oxygen, SBE 43 [ml/l], WS = 2', 1],
            [13,    '%11.4f',   'sbeox0PS: Oxygen, SBE 43 [% saturation], WS = 2', 1],
            [14,    '%11u',     'nbin: number of scans per bin', 1],
            [15,    '%11.3e',   'flag: flag', 1]]                          
                           
        #----------------------------------------------------------------------        
        #Seabird 19    UMFs
        if self.ctdNo == '6929':
            #OBS! Om något ändrats på CTDn, ex bytt sensorer, kör Seabirds program manuellt och titta på cnv-filen och uppdatera formatet nedan.
            #   [col,   'format',   'parameter name']            
            
            self.cnv_column_info = [
            [0,     '%11u',     'scan: Scan Count', 1],
            [1,     '%11.3f',   'prdM: Pressure, Strain Gauge [db]', 1],
            [2,     '%11.4f',   'tv290C: Temperature [ITS-90, deg C]', 1],       
            [3,     '%11.5f',   'c0S/m: Conductivity [S/m]', 1],
            [4,     '%11.4f',   'sbeox0V: Oxygen raw, SBE 43 [V]', 1],
            [5,     '%11.3f',   'dz/dtM: Descent Rate [m/s]', 1],
            [6,     '%11.3f',   'par: PAR/Irradiance, Biospherical/Licor', 1],
            [7,     '%11.4f',   'flECO-AFL: Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]', 1],
            [8,     '%11.4f',   'turbWETntu0: Turbidity, WET Labs ECO [NTU]', 1],
            [9,     '%11.4f',   'sal00: Salinity, Practical [PSU]', 1],
            [10,    '%11.4f',   'density00: Density [density, kg/m^3]', 1],
            [11,    '%11.4f',   'sigma-é00: Density [sigma-theta, kg/m^3]', 1],
            [12,    '%11.3f',   'depSM: Depth [salt water, m], lat ', 1],
            [13,    '%11.3f',   'depFM: Depth [true depth, m], lat ', 1],        
            [14,    '%11.2f',   'svCM: Sound Velocity [Chen-Millero, m/s]', 1],
            [15,    '%11.4f',   'sbeox0ML/L: Oxygen, SBE 43 [ml/l], WS = 2', 1],
            [16,    '%11.4f',   'sbeox0PS: Oxygen, SBE 43 [% saturation], WS = 2', 1],
            [17,    '%11u',     'nbin: number of scans per bin', 1],
            [18,    '%11.3e',   'flag: flag', 1]]                          
                           
        #----------------------------------------------------------------------
                                                                      
    #==========================================================================
    def check_bl(self):
    
        #Check if a .bl-file exists
        if os.path.isfile(self.working_directory + self.new_fname + '.bl') == True:    
            
            bl_file = open(self.working_directory + self.new_fname + '.bl','r')
            
            self.number_of_bottles = 0
            
            for nr,row in enumerate(bl_file):
                if nr > 1:
                    self.number_of_bottles += 1
            
            bl_file.close()
        else: 
            self.number_of_bottles = 0
    #==========================================================================
    def create_batch_file(self):
        """
        Create a textfile that will be called by the bat-file.
        The file runs the SEB-programs
        """
        
        # Open file
        #module_file = open(''.join([self.working_directory, self.ctdmodule_file]), "w")
        module_file = codecs.open(''.join([self.working_directory, self.ctdmodule_file]), "w", encoding='cp1252')
         
        #Data conversion
        #if its DANA:        
        if self.cnty == '26' and self.ship == '01':         
            self.datacnv = 'datcnv /pC:\ctd\setup\DatCnv_DANA.psa' + ' /i' + self.working_directory + self.new_fname + '.hex /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        #elif its FMI    
        elif self.ctdNo == '0817':         
            self.datacnv = 'datcnv /pC:\ctd\setup\DatCnv_FMI.psa' + ' /i' + self.working_directory + self.new_fname + '.hex /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
            
        elif self.ctdNo in ['1387', '1044', '0745']:         
            self.datacnv = 'datcnv /pC:\ctd\setup\DatCnv_Svea.psa' + ' /i' + self.working_directory + self.new_fname + '.hex /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
            
        elif self.ctdNo == '6164':
            self.datacnv = 'datcnv /pC:\ctdSBE19\setup\DatCnv_SBE19.psa' + ' /i' + self.working_directory + self.new_fname + '.hex /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        
        elif self.ctdNo == '6929':
            self.datacnv = 'datcnv /pC:\ctdSBE19\setup\DatCnv_SBE19_6929.psa' + ' /i' + self.working_directory + self.new_fname + '.hex /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'        
        else:
            #pass
            self.datacnv = 'datcnv /pC:\ctd\setup\DatCnv.psa' + ' /i' + self.working_directory + self.new_fname + '.hex /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        module_file.write(self.datacnv)
        
        
        #Filter
        if self.cnty == '26' and self.ship == '01':
            self.filter = 'filter /pC:\ctd\setup\Filter_DANA.psa /i' + self.working_directory + self.new_fname + '.cnv /o%1 \n'
        #elif its FMI    
        elif self.ctdNo == '0817':         
            self.filter = 'filter /pC:\ctd\setup\Filter_FMI.psa /i' + self.working_directory + self.new_fname + '.cnv /o%1 \n'
                        
        elif self.ctdNo in ['1387', '1044', '0745']:         
            self.filter = 'filter /pC:\ctd\setup\Filter_Svea.psa /i' + self.working_directory + self.new_fname + '.cnv /o%1 \n'
            
        elif self.ctdNo in ['6164','6929']: 
            self.filter = 'filter /pC:\ctdSBE19\setup\Filter_SBE19.psa /i' + self.working_directory + self.new_fname + '.cnv /o%1 \n'
            
        else:
            # pass
            self.filter = 'filter /pC:\ctd\setup\Filter.psa /i' + self.working_directory + self.new_fname + '.cnv /o%1 \n'
        module_file.write(self.filter)
        
        #Align CTD
        if self.cnty == '26' and self.ship == '01':
            self.alignctd = 'alignctd /pC:\ctd\setup\AlignCTD_DANA.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        #elif its FMI    
        elif self.ctdNo == '0817':         
            self.alignctd = 'alignctd /pC:\ctd\setup\AlignCTD_FMI.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        
        elif self.ctdNo in ['1387', '1044', '0745']:         
            self.alignctd = 'alignctd /pC:\ctd\setup\AlignCTD_Svea.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'        
            
        elif self.ctdNo in ['6164','6929']:         
            self.alignctd = 'alignctd /pC:\ctdSBE19\setup\AlignCTD_SBE19.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
            
        else:
            self.alignctd = 'alignctd /pC:\ctd\setup\AlignCTD.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        module_file.write(self.alignctd)
          
        #Cell thermal mass
        if self.ctdNo in ['6164','6929']: 
            self.celltm = 'celltm /pC:\ctdSBE19\setup\CellTM_SBE19.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        else:
            self.celltm = 'celltm /pC:\ctd\setup\CellTM.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        module_file.write(self.celltm)
              
        #Loop edit
        #if its DANA:        
        if self.cnty == '26' and self.ship == '01':          
            self.loopedit = 'loopedit /pC:\ctd\setup\LoopEdit_DANA.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'            
            
        elif self.deep_surfacesoak == True:
            self.loopedit = 'loopedit /pC:\ctdSBE19\setup\LoopEdit_deep.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
            
        elif self.manuell_surfacesoak == True:
            #self.loopedit = 'loopedit /pC:\ctd\setup\LoopEdit_manuell_surfacesoak.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'            
            self.loopedit = 'loopedit /pC:\ctdSBE19\setup\LoopEdit_shallow.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
                
        elif self.ctdNo in ['6164','6929']: 
            self.loopedit = 'loopedit /pC:\ctdSBE19\setup\LoopEdit_SBE19.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        
        else:            
            if 0: # test with 0.3 m/s
                print 'running loopedit with minimum 0.3 m/s'
                self.loopedit = 'loopedit /pC:\ctd\setup\LoopEdit_0.3ms.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
            elif 0: # test with 0.5 m/s
                print 'running loopedit with minimum 0.5 m/s'
                self.loopedit = 'loopedit /pC:\ctd\setup\LoopEdit_0.5ms.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
            else: # else is with 0.15m/s (default)
                print 'running loopedit with minimum 0.15 m/s'
                self.loopedit = 'loopedit /pC:\ctd\setup\LoopEdit.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        
        module_file.write(self.loopedit)
             
        #Derive
        #if SBE19
        if self.ctdNo in ['6164','6929']:
            self.derive = 'derive /pC:\ctdSBE19\setup\Derive_SBE19.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        else:
            self.derive = 'derive /pC:\ctd\setup\Derive.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        module_file.write(self.derive)
        
        #Bin Avergae
        if self.ctdNo in ['6164','6929']: 
            self.binavg = 'binavg /pC:\ctdSBE19\setup\BinAvg_SBE19.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        else:
            self.binavg = 'binavg /pC:\ctd\setup\BinAvg.psa /i' + self.working_directory + self.new_fname + '.cnv /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
        module_file.write(self.binavg)
            
        #BottleSum - 18/10-2015 JKro, updated 2015-11-09 OBac
        #self.bottlesum = 'bottlesum /i' + self.working_directory + self.new_fname + '.ros /pC:/ctd/setup/BottleSum.psa /o%1 \n'
        # kolla om .ros-filen finns, den skapas bara om man stängt någon flaska
        if self.number_of_bottles > 0:
            if self.cnty == '26' and self.ship == '01': 
                self.bottlesum = 'bottlesum /pC:\ctd\setup\BottleSum_DANA.psa /i' + self.working_directory + self.new_fname + '.ros /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
            elif self.ctdNo == '0817':         
                self.bottlesum = 'bottlesum /pC:\ctd\setup\BottleSum_FMI.psa /i' + self.working_directory + self.new_fname + '.ros /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
            elif self.ctdNo in ['1387', '1044', '0745']:         
                self.bottlesum = 'bottlesum /pC:\ctd\setup\BottleSum_Svea.psa /i' + self.working_directory + self.new_fname + '.ros /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
            else:
                self.bottlesum = 'bottlesum /pC:\ctd\setup\BottleSum.psa /i' + self.working_directory + self.new_fname + '.ros /c' + self.working_directory + self.new_fname + self.ctdconfig + ' /o%1 \n'
            module_file.write(self.bottlesum)
        else:
            print 'No bottles fired, will not create .btl or .ros file'
        
        #Strip
        #Tar bort O2 raw som används för beräkning av 02
        #borttaget JK, 02 okt 2019
        #self.strip = 'strip /pC:\ctd\setup\Strip.psa /i' + self.working_directory + self.new_fname + '.cnv /o%1 \n' 
        #module_file.write(self.strip)     
        
        #Split
        if self.cnty == '77' and self.ship == '10' and self.ctdNo in ['1387', '1044', '0745']: 
            self.split = 'split /pC:\ctd\setup\Split_Svea.psa /i' + self.working_directory + self.new_fname + '.cnv /o%1 \n'
        elif self.ctdNo in ['6164','6929']:       
            print 'Run Split_SBE19'            
            self.split = 'split /pC:\ctdSBE19\setup\Split_SBE19.psa /i' + self.working_directory + self.new_fname + '.cnv /o%1 \n'
        else:
            self.split = 'split /pC:\ctd\setup\Split.psa /i' + self.working_directory + self.new_fname + '.cnv /o%1 \n'
        module_file.write(self.split)
        
        #SBE19
        if self.ctdNo == '6164': 
            self.plot1 = 'seaplot /pC:\ctdSBE19\setup\File_1-SeaPlot_SBE19.psa /i' + self.working_directory + 'd' + self.new_fname + '.cnv /a_' + self.stationname + ' /o' + self.plot_directory + '20' + self.year + ' /f' + self.new_fname + '\n'
            module_file.write(self.plot1)
        elif self.ctdNo == '6929':
            self.plot1 = 'seaplot /pC:\ctdSBE19\setup\File_1-SeaPlot_SBE19_6929.psa /i' + self.working_directory + 'd' + self.new_fname + '.cnv /a_' + self.stationname + ' /o' + self.plot_directory + '20' + self.year + ' /f' + self.new_fname + '\n'
            module_file.write(self.plot1)
            self.plot2 = 'seaplot /pC:\ctdSBE19\setup\File_2-SeaPlot_SBE19_6929.psa /i' + self.working_directory + 'd' + self.new_fname + '.cnv /a_TS_diff_' + self.stationname + ' /o' + self.plot_directory + '20' + self.year + ' /f' + self.new_fname + '\n'
            module_file.write(self.plot2)
        else:
            #Plot File_1-SeaPlot.psa
            self.plot1 = 'seaplot /pC:\ctd\setup\File_1-SeaPlot.psa /i' + self.working_directory + 'd' + self.new_fname + '.cnv /a_' + self.stationname + ' /o' + self.plot_directory + '20' + self.year + ' /f' + self.new_fname + '\n'
            module_file.write(self.plot1)
            #Plot File_2-SeaPlot_T_S_difference.psa
            self.plot2 = 'seaplot /pC:\ctd\setup\File_2-SeaPlot_T_S_difference.psa /i' + self.working_directory + 'd' + self.new_fname + '.cnv /a_TS_diff_' + self.stationname + ' /o' + self.plot_directory + '20' + self.year + ' /f' + self.new_fname + '\n'
            module_file.write(self.plot2)
            #Plot File_3-SeaPlot_oxygen1&2.psa
            self.plot3 = 'seaplot /pC:\ctd\setup\File_3-SeaPlot_oxygen1&2.psa /i' + self.working_directory + 'd' + self.new_fname + '.cnv /a_oxygen_diff_' + self.stationname + ' /o' + self.plot_directory + '20' + self.year + ' /f' + self.new_fname + '\n'
            module_file.write(self.plot3)
            #Plot File_4-SeaPlot_TURB_PAR.psa
            if self.cnty == '26' and self.ship == '01':
                self.plot4 = 'seaplot /pC:\ctd\setup\File_4-SeaPlot_TURB_PAR_DANA.psa /i' + self.working_directory + 'd' + self.new_fname + '.cnv /a_fluor_turb_par_' + self.stationname + ' /o' + self.plot_directory + '20' + self.year + ' /f' + self.new_fname + '\n'
            elif self.cnty == '77' and self.ship == '10':
                self.plot4 = 'seaplot /pC:\ctd\setup\File_4-SeaPlot_TURB_PAR_Svea.psa /i' + self.working_directory + 'd' + self.new_fname + '.cnv /a_fluor_turb_par_' + self.stationname + ' /o' + self.plot_directory + '20' + self.year + ' /f' + self.new_fname + '\n'                
            else:                
                self.plot4 = 'seaplot /pC:\ctd\setup\File_4-SeaPlot_TURB_PAR.psa /i' + self.working_directory + 'd' + self.new_fname + '.cnv /a_fluor_turb_par_' + self.stationnam + ' /o' + self.plot_directory + '20' + self.year + ' /f' + self.new_fname + '\n'
            module_file.write(self.plot4)
        
        #Skriv in stationsnamn i varje plot
        if self.ctdNo in ['6164','6929']: 
            insert_station_name(self.stationname, 'C:\\ctdSBE19\\setup\\File_1-SeaPlot_SBE19.psa')   
        else:
            insert_station_name(self.stationname, 'C:\\ctd\\setup\\File_1-SeaPlot.psa')
            insert_station_name(self.stationname, 'C:\\ctd\\setup\\File_2-SeaPlot_T_S_difference.psa')
            insert_station_name(self.stationname, 'C:\\ctd\\setup\\File_3-SeaPlot_oxygen1&2.psa')
            insert_station_name(self.stationname, 'C:\\ctd\\setup\\File_4-SeaPlot_TURB_PAR_Svea.psa')
                    
        module_file.close()       
          
    def run_seabird(self):
        print ' running batch'
        os.system(self.working_directory + self.batch_file)
        print 'ready with batch'
        
    def modify_cnv_file(self):        
        # Read "down"-file
        print 'self.new_fname',self.working_directory + 'd' + self.new_fname +'.cnv'

        self.ctd_data = readCNV(self.working_directory + 'd' + self.new_fname +'.cnv')
        
        # Här borde man kunna definiera sensor_index, dvs första kolumnen i self.cnv_column_info
        # den kommer automatiskt efter så som DatCnv.psa är inställd
        # Börjar med att kolla så det iaf är korrekt
        for sensor_row in self.cnv_column_info:
            sensor_index = sensor_row[0]
            sensor_text = sensor_row[2]
            #print sensor_text
            #print sensor_row
            if sensor_text == 'depFM: Depth [true depth, m], lat ':
                # kolla inte True Depth, det läggs till senare
                pass
            elif sensor_text == 'sigma-é00: Density [sigma-theta, kg/m^3]' :
                # kolla inte sigma-é00, då kodningen ställer till det.                
                pass
            else:
                for ctd_header_row in self.ctd_data[1]:
                    
                    if sensor_text in ctd_header_row:
                        sensor_index_cnv_header = int(ctd_header_row[7:9])
                        break
                    else:
                        #print ctd_header_row                        
                        sensor_index_cnv_header = 'not found'
                
                if sensor_index == sensor_index_cnv_header:
                    pass
                
                else:
                    print ('WARNING!!! sensor column index in self.cnv_column_info (%s) is not the same as in the cnv header (%s), stopping script!!!' % (sensor_index,sensor_index_cnv_header))
                    print 'FIX THIS NOW!!!'
                    smurf
        
        sh = [];
        for rows in self.ctd_data[1]:
            sh.append(split(':\s',str.rstrip(rows)).pop())
            
        # get rid of the last column of sh (flags)
        sh.pop()
                
        # Extract the pressure, sigmaT and FW depth:
        # depFM: Depth [fresh water, m], lat = 0    
        for cols in self.ctd_data[1]:
            if self.ctdNo in ['6164','6929']:
                if 'prdM: Pressure, Strain Gauge [db]' in cols:
                    col_pres = int(cols[7:9])
            else:
                if 'prDM: Pressure, Digiquartz [db]' in cols:
                    col_pres = int(cols[7:9])
                    
            if 'sigma' in cols:
                col_dens = int(cols[7:9])
            if 'sigma-t11: Density, 2 [sigma-t' in cols:
                col_dens2 = int(cols[7:9])
            if 'depFM: Depth [fresh water, m]' in cols:
                col_depth = int(cols[7:9])
            if 'svCM: Sound Velocity [Chen-Millero, m/s]' in cols:    
                col_sv = int(cols[7:9])
                
        prdM  = [row[col_pres] for row in self.ctd_data[2]]
        
        if self.cnv_column_info[col_dens][3] == 1:
            sigT  = [row[col_dens] for row in self.ctd_data[2]]
        elif self.cnv_column_info[col_dens2][3] == 1: # use secondary sigT
            sigT = [row[col_dens2] for row in self.ctd_data[2]]
        else:
            sigT = [-9.990e-29 for i in range(len(self.ctd_data[2]))]

        depFM = [row[col_depth] for row in self.ctd_data[2]]
        svCM  = [row[col_sv] for row in self.ctd_data[2]]
        
        #Beräkning från Arnes CTrueDepth.bas program
        #' Plockar pressure från cnv-filen
        #        dblPres = Mid$(strDataline, ((strPresWhere * 11) + 1), 11)             
        #' decibar till bar
        #        dblRPres = dblPres * 10              
        #' Plockar sigmaT från cnv-filen
        #        dblSig = Mid$(strDataline, ((strSigmaTWhere * 11) + 1), 11)
        #' Beräknar densitet
        #        dblDens = (dblSig + 1000) / 1000#              
        #' Beräknar delta djup
        #        dblDDjup = (dblRPres - dblP0) / (dblDens * dblg)       
        #' Summerar alla djup och använd framräknande trycket i nästa iteration
        #        dblDepth = dblDepth + dblDDjup
        #        dblP0 = dblRPres
        
        #Beräkning av truedepth #Ersätt depFM med true depth i headern
        #Start params
        g = 9.818 #' g vid 60 gr nord (dblg)
        P0 = 0 #' starttrycket (vid ytan) (dblP0)
        Dens0 = (sigT[0] + 1000.) /1000. #' start densitet
        Depth = 0 #' start summadjup (dblDepth)
        #Nya variabler
        RPres = []
        Dens = []
        DDepth = []
        TrueDepth =[]
        
        for q in range(0,len(prdM)):
            
            if sigT[q] != -9.990e-29:
                #decibar till bar (dblRPres)
                RPres = prdM[q] * 10.               
                # Beräknar densitet (dblDens)
                Dens = (sigT[q] + 1000.) / 1000.
                #Beräknar delta djup (dblDDjup)
                DDepth = (RPres - P0) / ((Dens+Dens0)/2. * g)        
                #Summerar alla djup och använd framräknande trycket i nästa loop
                #Om det är första (ej helt relevant kanske) eller sista värdet dela med två enl. trappetsmetoden    
                Dens0 = Dens
                #    if q == 0 or q == (len(prdM)-1):
                #        Depth = Depth + DDepth / 2.        
                #    else:
                #        Depth = Depth + DDepth
                # Ändrad av Örjan 2015-02-10 /2. första och sista djupet borttaget.
                Depth = Depth + DDepth
                #Spara framräknat djup för nästa loop
                P0 = RPres
                #Sparar undan TrueDepth
                TrueDepth.append(Depth)
            else:
                TrueDepth.append(-9.990e-29)
            
        #Header
        #Lägg till tid för true depth beräkning i header & average sound velocity
        #xx = [i for i,x in enumerate(self.ctd_data[0]) if x == '** Primary sensors\n']
        try:
            xx = [i for i,x in enumerate(self.ctd_data[0]) if '** Ship' in x]
            #print xx
            tid=strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
            svMean = sum(svCM)/len(svCM)
            self.ctd_data[0].insert(xx[0]+1,'** Average sound velocity: ' + str('%6.2f' %svMean) + ' m/s\n')
            self.ctd_data[0].insert(xx[0]+2,'** True-depth calculation ' + tid + '\n')
            #self.ctd_data[0].insert(xx[0]+3,'** CTD Python Module SMHI /ver 3-12/ feb 2012 \n')
            #self.ctd_data[0].insert(xx[0]+4,'** LIMS Job: 20' + self.year + self.cnty + self.ship + '-' + self.serie + '_SYNC\n')
                      
            #** LIMS Job: 20237710-0616
            self.ctd_data[0].insert(xx[0]+4,'** LIMS Job: 20' + self.year + self.cnty + self.ship_intern_ID + '-' + self.serie_no + '\n')
        except:
            print u'No metadata to file header - SBE19?'
            pass
        
        #Ersätter depFM: Depth [fresh water, m], lat = 0
        #med depFM: Depth [true depth, m], lat = 0   
        #xx = [i for i,x in enumerate(self.ctd_data[0]) if 'depFM: Depth [fresh water, m]' in x]
        #xx = [i for i,x in enumerate(self.ctd_data[0]) if x == '# name 21 = depFM: Depth [fresh water, m], lat = 0\n']
        #self.ctd_data[0][xx[0]] = self.ctd_data[0][xx[0]].replace('fresh water','true depth')
        
        index_true_depth = '99'
        
        for i,x in enumerate(self.ctd_data[0]):

            #Lägger till enhet till PAR/Irradiance                      
            
            if 'par: PAR/Irradiance' in x:                                  
                self.ctd_data[0][i] = self.ctd_data[0][i][:-2] + ' [µE/(cm^2*s)]\n'
            #Lägger till Chl-a på den fluorometer som har serialnumber som börjar på FLNTURTD    
            if 'Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]' in x:
                Fluo_index = i
            if 'Fluorometer, WET Labs ECO-AFL/FL -->' in x and '<SerialNumber>FLNTURTD' in self.ctd_data[0][i+2]:    
                self.ctd_data[0][i] = self.ctd_data[0][i].replace('Fluorometer', 'Chl-a Fluorometer')                
                self.ctd_data[0][Fluo_index] = self.ctd_data[0][Fluo_index].replace('Fluorescence','Chl-a Fluorescence')                                                     
            #Lägger till Phycocyanin på den fluorometer som har serialnumber som börjar på FLNTURTD    
            if 'Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]' in x:
                Fluo_index_2 = i
            if 'Fluorometer, WET Labs ECO-AFL/FL, 2 -->' in x and '<SerialNumber>FLPCRTD' in self.ctd_data[0][i+2]:    
                self.ctd_data[0][i] = self.ctd_data[0][i].replace('Fluorometer', 'Phycocyanin Fluorometer')                                        
                self.ctd_data[0][Fluo_index_2] = self.ctd_data[0][Fluo_index_2].replace('Fluorescence','Phycocyanin Fluorescence')                                                       
            if 'depFM: Depth [fresh water, m]' in x:
                self.ctd_data[0][i] = self.ctd_data[0][i].replace('fresh water','true depth')
                index_true_depth = x[7:9].strip()
            if '# span '+index_true_depth+' =' in x:
                if int(index_true_depth) < 10:
                    self.ctd_data[0][i] = ('# span %s =%11.3f,%11.3f%7s\n' % (index_true_depth,min(TrueDepth),max(TrueDepth),''))
                else:
                    self.ctd_data[0][i] = ('# span %s =%11.3f,%11.3f%6s\n' % (index_true_depth,min(TrueDepth),max(TrueDepth),''))
                        
            #Fixar en felstavning i vissa äldra filer. 
            if 'Lattitude' in x:
                self.ctd_data[0][i] = self.ctd_data[0][i].replace('Lattitude [GG MM.mm N]','Latitude')
            #Tar bort [GG MM.mm N] från lat och long så att filen går att läsa in i ODV.        
            if '** Latitude [GG MM.mm N]' in x:
                self.ctd_data[0][i] = self.ctd_data[0][i].replace(' [GG MM.mm N]','')
            if '** Longitude [GG MM.mm E]' in x:
                self.ctd_data[0][i] = self.ctd_data[0][i].replace(' [GG MM.mm E]','')
                
            # # span 0 =        900,       1295  hämtar span för scan som skall manipuleras   
            if '# span 0' in x:
                span_0 = self.ctd_data[0][i].split('=')[1].replace(' ','').split(',')[0]
                span_1 = self.ctd_data[0][i].split('=')[1].replace(' ','').split(',')[1].strip('\n')
                #* cast  27 16 Oct 2022 06:35:12 samples 75387 to 77005, avg = 1, stop = mag switch

        for i,x in enumerate(self.ctd_data[0]):
            if '* cast' in x:
                #* cast  27 16 Oct 2022 06:35:12 samples 75387 to 77005, avg = 1, stop = mag switch
                q1=self.ctd_data[0][i].split()  
                q1[8] = span_0      #75387
                q1[10] = span_1 + ','     #77005            
                self.ctd_data[0][i] = ' '.join(q1) +'\n'
                #print self.ctd_data[0][i]                                     
                        
        #Ersätt data i fresh water kolumnen med true depth avrundar true depth till tre decimaler
        for row in range(0,len(prdM)):
            if TrueDepth[row] == -9.990e-29:
                self.ctd_data[2][row][col_depth] = -9.990e-29
            else:
                self.ctd_data[2][row][col_depth] = round(TrueDepth[row],3)
        
        # justera span för de parametrar som har sensor_flag = 0
        for sensor_row in self.cnv_column_info:
            if sensor_row[-1] == 0: # entire sensro marked as bad, set span to -9.990e-29, -9.990e-29
                sensor_text = sensor_row[2]
                index_sensor = '99'
                for i,x in enumerate(self.ctd_data[0]):
                    if sensor_text in x:
                        index_sensor = x[7:9].strip()
                    if '# span '+index_sensor+' =' in x:
                        if int(index_sensor) < 10:
                            self.ctd_data[0][i] = ('# span %s = -9.990e-29, -9.990e-29%7s\n' % (index_sensor,''))
                        else:
                            self.ctd_data[0][i] = ('# span %s = -9.990e-29, -9.990e-29%6s\n' % (index_sensor,''))
        
        #TODO: Lägg till if sats som skapar kataloger vid nytt år. /MHAN
        if not os.path.exists(self.data_directory +'20' + self.year + '\\'): #hoppas denna funkar /OBac
            os.mkdir(self.data_directory +'20' + self.year + '\\')
        
        filelist=os.walk(self.data_directory +'20' + self.year + '\\').next()[2]
        
        # print filelist
        # print self.data_directory +'20' + self.year + '\\'
        
        if not self.new_fname + '.cnv' in filelist:
            #Skriver tillbaka header self.ctd_data[0], 
            test_file = open(self.data_directory +'20' + self.year + '\\' + self.new_fname + '.cnv', 'w')
            test_file.writelines(self.ctd_data[0])
            test_file.close()
            
            #och lägger tillbaka data self.ctd_data[2] till samma fil
            test_file = open(self.data_directory +'20' + self.year + '\\' + self.new_fname + '.cnv', "a")
            for row in self.ctd_data[2]:
                row_to_write, bad_flag = self.get_string_for_data_file(row)
                    
                if bad_flag:
                    print 'Bad flag detected at %s db, in %s' % (row[1],self.new_fname)
                # else: # can activate this to not write this depth to the data file
                test_file.write(row_to_write)
                test_file.write('\n')
            test_file.close()
                    
            #TODO: copy cnv and plots to file server
            # C:\ctd\plots\\' + '20' + self.year + ' /f' + self.new_fname
            # /a_' + self.stationname
            # /a_TS_diff_' + self.stationname
            # /a_oxygen_diff_' + self.stationname
            # /a_fluor_turb_par_' + self.stationname
                        
#            if os.path.exists(self.shark_file_directory):
#                self.write_shark_file(self.shark_file_directory)
#                
#            else: #Om det saknas nätverk läggs filen lokalt. 
#                self.write_shark_file(self.shark_file_directory_lokal)
#                print 'Network is missing...'
#                print 'SHARK import file are available here %s' % self.shark_file_directory_lokal
#            
            #Rensa och flytta filer
            #os.remove('C:\\ctd\\temp\\u' + new_fname + '.cnv')
            os.remove(self.working_directory + 'd' + self.new_fname + '.cnv')
            os.remove(self.working_directory + self.new_fname + '.cnv')
                   
            shutil.move(self.working_directory + 'u' + self.new_fname + '.cnv', self.data_directory + '20' + self.year + '\\up_cast')
            shutil.move(self.working_directory + self.new_fname + self.ctdconfig, self.raw_files_directory + '20' + self.year)
            shutil.move(self.working_directory + self.new_fname + '.hex', self.raw_files_directory + '20' + self.year)
            shutil.move(self.working_directory + self.new_fname + '.xml', self.raw_files_directory + '20' + self.year)
            try:
                shutil.move(self.working_directory + self.new_fname + '.hdr', self.raw_files_directory + '20' + self.year)
            except:
                print('No .hdr file to move')
            
            try:
                shutil.move(self.working_directory + self.new_fname + '.bl', self.raw_files_directory + '20' + self.year)
            except:
                print('No .btl file to move')
                
            try: 
                shutil.move(self.working_directory + self.new_fname + '.btl', self.raw_files_directory + '20' + self.year)
            except:
                print('No .btl file to move')
                
            try:
                shutil.move(self.working_directory + self.new_fname + '.ros', self.raw_files_directory + '20' + self.year)
            except:
                print('No .ros file to move')            
            
            
        else: # filen finns redan
            
            q=raw_input('Files do already exist. Overwrite? Y or N?')
            # q = 'Y'
            if q.upper() == 'Y': # om Y; skriv över filen
                #Skriver tillbaka header self.ctd_data[0], 
                test_file = open(self.data_directory + '20' + self.year + '\\' + self.new_fname + '.cnv', 'w')
                test_file.writelines(self.ctd_data[0])
                test_file.close()
                
                #och lägger tillbaka data self.ctd_data[2] till samma fil
                test_file = open(self.data_directory+ '20' + self.year + '\\' + self.new_fname + '.cnv', "a")
                for row in self.ctd_data[2]:
                    row_to_write, bad_flag = self.get_string_for_data_file(row)
                    
                    if bad_flag:
                        print 'Bad flag detected at %s db, in %s' % (row[1],self.new_fname)
                    # else: # can activate this to not write this depth to the data file
                    test_file.write(row_to_write)
                    test_file.write('\n')
                    
                test_file.close()
                
                #TODO:
                #TODO: copy cnv and plots to file server
                # C:\ctd\plots\\' + '20' + self.year + ' /f' + self.new_fname
                # /a_' + self.stationname
                # /a_TS_diff_' + self.stationname
                # /a_oxygen_diff_' + self.stationname
                # /a_fluor_turb_par_' + self.stationname
                                  
                #Rensa och flytta filer
                #os.remove('C:\\ctd\\temp\\u' + new_fname + '.cnv')
                os.remove(self.working_directory + 'd' + self.new_fname + '.cnv')
                os.remove(self.working_directory + self.new_fname + '.cnv')
                
                
                # ta bort äldre filer och kopiera över det nya
                try:
                    os.remove(self.data_directory + '20' + self.year + '\\up_cast\\u' + self.new_fname + '.cnv')
                except:
                    print('No old up_cast file to delete')
                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' +  self.new_fname + self.ctdconfig)
                except:
                    pass
                    
                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' +  self.new_fname + '.hex')
                except:
                    pass

                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' +  self.new_fname + '.xml')
                except:
                    pass
                
                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' +  self.new_fname + '.hdr')
                except:
                    pass
                    
                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' +  self.new_fname + '.bl')
                except:
                    pass
                    
                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' +  self.new_fname + '.btl')
                except:
                    print('No old .btl file to delete')
                try:
                    os.remove(self.raw_files_directory + '20' + self.year + '\\' +  self.new_fname + '.ros')
                except:
                    print('No old .ros file to delete')
                
                print 'work', self.working_directory + 'u' + self.new_fname + '.cnv'
                print 'data', self.data_directory + '20' + self.year + '\\up_cast'
                
                #TODO
                # copy up-cast
                shutil.move(self.working_directory + 'u' + self.new_fname + '.cnv', self.data_directory + '20' + self.year + '\\up_cast')
                shutil.move(self.working_directory + self.new_fname + self.ctdconfig, self.raw_files_directory + '20' + self.year)
                shutil.move(self.working_directory + self.new_fname + '.hex', self.raw_files_directory + '20' + self.year)
                shutil.move(self.working_directory + self.new_fname + '.xml', self.raw_files_directory + '20' + self.year)
                try:
                    shutil.move(self.working_directory + self.new_fname + '.hdr', self.raw_files_directory + '20' + self.year)
                except:
                    print('No .hdr file to move')
                
                try:
                    shutil.move(self.working_directory + self.new_fname + '.bl', self.raw_files_directory + '20' + self.year)
                except:
                    print('No .bl file to move')
                
                try:
                    shutil.move(self.working_directory + self.new_fname + '.btl', self.raw_files_directory + '20' + self.year)
                except:
                    print('No .btl file to move')
                    
                try:
                    shutil.move(self.working_directory + self.new_fname + '.ros', self.raw_files_directory + '20' + self.year)
                except:
                    print('No .ros file to move')
    
    
    #==========================================================================
    def copy_files_to_server(self):
        #print self.cnty
        print self.ship
        #print self.ship_intern_ID
        if self.cnty == '77' and (self.ship == '10' or self.ship == 'SE'):
            
            # write to McHDVideo until write permisisons have been fixed for Mcseabirdchem
            if 0:
                server_data_dir = '\\\\scifi01\\scifi\\Processed\\mchdvideo\\CTD_SBE19\\data\\'
                server_plot_dir = '\\\\scifi01\\scifi\\Processed\\mchdvideo\\CTD_SBE19\\plots\\'
                server_raw_dir =  '\\\\scifi01\\scifi\\Processed\\mchdvideo\\CTD_SBE19\\raw\\'
            else:
                server_data_dir = '\\\\scifi01.svea.slu.se\\Processed$\\McSeabirdChem\\data\\'
                #server_data_dir = '\\\\scifi01\\scifi\\Processed\\mcseabirdchem\\data\\'            
                server_plot_dir = '\\\\scifi01.svea.slu.se\\Processed$\\McSeabirdChem\\plots\\'
                #server_plot_dir = '\\\\scifi01\\scifi\\Processed\\mcseabirdchem\\plots\\'
                server_raw_dir = '\\\\scifi01.svea.slu.se\\Processed$\\McSeabirdChem\\raw\\'
                #server_raw_dir =  '\\\\scifi01\\scifi\\Processed\\mcseabirdchem\\raw\\'
            
            # Data
            if not os.path.exists(server_data_dir + '\\20' + self.year + '\\'): 
                try:
                    os.mkdir(server_data_dir +'20' + self.year + '\\')
                except:
                     print 'Can not connect to server...!'
            # Raw
            if not os.path.exists(server_raw_dir +'\\20' + self.year + '\\'): 
                try:
                    os.mkdir(server_raw_dir +'20' + self.year + '\\')                
                except:
                     print 'Can not connect to server...!'            
            # Plots
            if not os.path.exists(server_plot_dir +'\\20' + self.year + '\\'): 
                try:
                    os.mkdir(server_plot_dir +'20' + self.year + '\\')
                except:
                     print 'Can not connect to server...!'                
            
            # Data (cnv)
            try:
                shutil.copyfile(self.data_directory + '\\20' + self.year + '\\' + self.new_fname + '.cnv', server_data_dir + '\\20' + self.year + '\\' + self.new_fname + '.cnv')
            except:
                print 'Cant copy cnv file to file server!'
            # up-cast
            try:
                shutil.copyfile(self.data_directory + '\\20' + self.year + '\\' + 'up_cast' + '\\' + 'u' + self.new_fname + '.cnv', server_data_dir + '\\20' + self.year + '\\' + 'up_cast' + '\\' + 'u' + self.new_fname + '.cnv')
                print self.data_directory + '\\20' + self.year + '\\' + 'up_cast' + '\\' + 'u' + self.new_fname + '.cnv', server_data_dir + '\\20' + self.year + '\\' + 'up_cast' + '\\' + 'u' + self.new_fname + '.cnv'
            except:
                print 'Cant copy cnv upcast to file server!'
            
            # renamed Raw files
            # bl btl hdr hex ros XMLCON
            try:
                shutil.copyfile(self.raw_files_directory + '\\20' + self.year + '\\' + self.new_fname + '.bl', server_raw_dir + '\\20' + self.year + '\\' + self.new_fname + '.bl')
            except:
                print 'Cant copy raw.bl file to file server!'
            try:
                shutil.copyfile(self.raw_files_directory + '\\20' + self.year + '\\' + self.new_fname + '.btl', server_raw_dir + '\\20' + self.year + '\\' + self.new_fname + '.btl')
            except:
                print 'Cant copy raw.btl file to file server!'
            try:
                shutil.copyfile(self.raw_files_directory + '\\20' + self.year + '\\' + self.new_fname + '.hdr', server_raw_dir + '\\20' + self.year + '\\' + self.new_fname + '.hdr')
            except:
                print 'Cant copy raw.hdr file to file server!'
            try:
                shutil.copyfile(self.raw_files_directory + '\\20' + self.year + '\\' + self.new_fname + '.hex', server_raw_dir + '\\20' + self.year + '\\' + self.new_fname + '.hex')
            except:
                print 'Cant copy raw.hex file to file server!'
            if self.ctdnumber == '6164':
                try:
                    shutil.copyfile(self.raw_files_directory + '\\20' + self.year + '\\' + self.new_fname + '.xml', server_raw_dir + '\\20' + self.year + '\\' + self.new_fname + '.xml')
                except:
                    print 'Cant copy raw.hex file to file server!'
            try:
                shutil.copyfile(self.raw_files_directory + '\\20' + self.year + '\\' + self.new_fname + '.ros', server_raw_dir + '\\20' + self.year + '\\' + self.new_fname + '.ros')
            except:
                print 'Cant copy raw.ros file to file server!'
            try:
                shutil.copyfile(self.raw_files_directory + '\\20' + self.year + '\\' + self.new_fname + '.XMLCON', server_raw_dir + '\\20' + self.year + '\\' + self.new_fname + '.XMLCON')
            except:
                print 'Cant copy raw.XMLCON file to file server!'
            
            
            # Plots
            try:
                filename =  'd' + self.new_fname + '_' + self.stationname + '.jpg'
                shutil.copyfile(self.plot_directory + '\\20' + self.year + '\\' + filename, server_plot_dir + '\\20' + self.year + '\\' + filename)
            except:
                print 'Cant copy CTD plot to file server!'
            try:
                filename = 'd' + self.new_fname + '_TS_diff_' + self.stationname + '.jpg'
                shutil.copyfile(self.plot_directory + '\\20' + self.year + '\\' + filename, server_plot_dir + '\\20' + self.year + '\\' + filename)
            except:
                print 'Cant copy CTD TS_diff plot to file server!'
            try:
                filename = 'd' + self.new_fname + '_oxygen_diff_' + self.stationname + '.jpg'
                shutil.copyfile(self.plot_directory + '\\20' + self.year + '\\' + filename, server_plot_dir + '\\20' + self.year + '\\' + filename)
            except:
                print 'Cant copy CTD oxygen_diff plot to file server!'
            try:
                filename = 'd' + self.new_fname + '_fluor_turb_par_' + self.stationname + '.jpg'
                shutil.copyfile(self.plot_directory + '\\20' + self.year + '\\' + filename, server_plot_dir + '\\20' + self.year + '\\' + filename)
            except:
                print 'Cant copy CTD fluor_turb_par plot to file server!'
            
        else:
            pass
        
        
    #==========================================================================
    def get_string_for_data_file(self, row):        
        
        text_line = ''
        for index, col in enumerate(self.cnv_column_info):
            sensor_flag = col[3] # or maybe better col[-1] ?
#            print index, col, len(row)
#            print row
            if row[-1] == -9.990e-29: # bad flag, entire row is bad
                bad_flag = True
            else:
                bad_flag = False

            if row[index] == -9.990e-29 or sensor_flag == 0:
                text_line = ''.join([text_line, u' -9.990e-29'])
            else:
                text_line = ''.join([text_line, col[1] % row[index]])
            
        
        return text_line, bad_flag
        
    #========================================================================== 
    def make_LIMS_export_file(self)        :
        print 'Making LIMS-export from cnv-file...'    
        #Header of LIMS-export file
        header = 'Depth [m],',u'Temp. [deg C],','Sal. [ ],',u'Chl-Flu. [µg/l],','Turbidity [ ],','Oxygen [ml/l],','Flag'
        
        #Sökväg till filen där redigerade filer hamnar              
        myFileDir = self.data_directory + '/LIMS'    
        # om katalogen inte finns, skapa den
        if not os.path.isdir(myFileDir):
            os.mkdir(myFileDir)    

        #öppna filen, endast läsning
        file1 = open(self.data_directory + '\\20' + self.year + '\\'+ self.new_fname + '.cnv','r')  
        names = self.new_fname
        value = np.array([])

        DcolNo = None
        CcolNo = None
        ScolNo = None
        TcolNo = None
        OcolNo = None
        FcolNo = None
        UcolNo = None
        
        for rows in file1:
            
            """ Tar reda på vilken kolumn som är vad genom att scanna headern """
            if 'depFM:' in rows:
                DcolNo = int(rows.lstrip('# name').partition('=')[0])
            elif 'flECO-AFL:' in rows:
                CcolNo = int(rows.lstrip('# name').partition('=')[0])
            elif 'sal00:' in rows:
                ScolNo = int(rows.lstrip('# name').partition('=')[0])
            elif 'tv290C:' in rows:
                TcolNo = int(rows.lstrip('# name').partition('=')[0])
            elif 'sbeox0ML/L:' in rows:
                OcolNo = int(rows.lstrip('# name').partition('=')[0])
            elif 'flag:' in rows:
                FcolNo = int(rows.lstrip('# name').partition('=')[0])
            elif 'turbWETntu0:' in rows: #turbiditetsmätare
                UcolNo = int(rows.lstrip('# name').partition('=')[0])     
            elif 'upoly0:' in rows: #turbiditetsmätare
                UcolNo = int(rows.lstrip('# name').partition('=')[0])
                #Vi antar att det bara används en turbiditetsmätare - men de 
                #har använt olika typer vid olika tillfälen
                    
            if '** Station:' in rows:
                station = rows[10:].strip(' \r\n')
            
            if '** Latitude' in rows:
                latitud = rows[26:].strip('\r\n')
            if '** Longitude' in rows:
                longitud = rows[27:].strip('\r\n')
         
            #handle data from CTD-file below
            if (rows[:6] == ('      ') or rows[:5] == ('     ') or rows[:4] == ('    ')):
                my_val = rows.split()
                matrix = np.array([])
                for b in range(len(my_val)):
                    matrix = np.append(matrix,float(my_val[b]))    
                value = np.append(value, matrix)
                
        value = np.reshape(value,(-1,len(matrix)))
        max_depth = np.max(value,axis=0)[DcolNo]
        
        if (np.mod(max_depth,0.5) > 0.25): #modulo, mer än 0.25 m
            max_depth = max_depth + 0.5 - np.mod(max_depth,0.5)
        else:
            max_depth = max_depth - np.mod(max_depth,0.5)
        
        #------------------------------------------
        #om  minsta djup skall justeras manuellt
        #------------------------------------------
        min_depth = np.min(value,axis=0)[DcolNo]
        if min_depth > 0.5:
            min_depth = 1.0
        else:
            min_depth = 0.5
        #------------------------------------------
        
       #Hitta första maxvärde för djup och korta av value...
        a = ml.find((value[:,DcolNo]) == max(value[:,DcolNo]))[0]
        #...och släng resterande värden
        value = value[:a+1,:]
        no_of_columns = value.shape[1]
        
        #alla intervall där värden ska summeras
        djupvektor = np.arange(min_depth, max_depth + 0.1, 0.5)
        mean_val = np.zeros((len(djupvektor),
            len(value[0]) - 0),float) #vektor för medelvärden
        #djup tas nu med i mean_val, därav  len(value[0]) - 0), men används ej för tillfället, 4/6-19 JKro
        #djup ej med i value, därav "len(value[0]) - 1)"
        for b in djupvektor:
            temp_val = np.zeros((2,mean_val.shape[1]),float) #temporär vektor för mätvärden
            for rows in np.arange(0,len(value)):
                #välj värden mellan -0.25 och +0.25 kring värdet
                #använd djup dvs 'DcolNo'
                if ((value[rows, DcolNo] >= b - 0.25) &
                    (value[rows, DcolNo] < b + 0.25)):
                    for a in np.arange(0,len(value[0])):
                        temp_val[0, a] = temp_val[0, a] + value[rows, a] #sammanlag summa mätvärden
                        temp_val[1, a] = temp_val[1, a] + 1 #antal mätvärden
                            
            mean_val[int(ml.find(b == djupvektor))][:] = (temp_val[0, :]/temp_val[1, 0]) #medelvärde inom intervall
                            
        file1.close()              
          
        end_file = codecs.open(myFileDir + '\\'+names[0:-4] + '_red.txt',
                               encoding='Latin-1',mode='w') # 'Latin-1' 
        
        end_file.write(u'Uppgifter från från provtagningsprotokoll\n')
        end_file.write(u'Station: ' + station + '\n')
        end_file.write(u'Latitud: ' + latitud + '\n')
        end_file.write(u'Longitud: ' + longitud + '\n')
        end_file.write(u'Datum: ' + names[11:15]+ '-' + names[15:17] + '-' + names[17:19] + '\n')        
        end_file.write(u'Tid: ' + names[20:22]+ ':' + names[22:24] + '\n')
        
        # Add LIMS Job
        end_file.write(u'LIMS Job: ' + names.split('_')[2][0:4] + names.split('_')[4] + names.split('_')[5] + u'-' + names.split('_')[6].strip('.cnv') + '\n\n')
              
        for a in range(0,len(header)):
            end_file.write(header[a])
        end_file.write('\n')

        header_order = [TcolNo,ScolNo,CcolNo,UcolNo,OcolNo,FcolNo]
        dec = ['%5.2f,','%5.3f,','%5.2f,','%5.2f,','%5.2f,','%3i']
        for aa, b in enumerate(djupvektor):
            end_file.write('%5.1f,' %b) #Depth is written to each row
            for i, c in enumerate(header_order):
                if c is None:
                    end_file.write(',')    
                else:
                    #try-except nytt 3/6-19
                    #för att hantera fel med flaggan FcolNo 
                    #när den skrevs till filen - var NaN men behövde vara integer
                    try:
                        end_file.write(dec[i] %mean_val[aa, c])
                    except:
                        if np.isnan(mean_val[aa, c]) and c == FcolNo:
                            print u'Flag is nan, row: ',aa
                            end_file.write(dec[i] %0)                           
            end_file.write('\n')
                   
        end_file.close()
 
        print 'Done making LIMS-export file!'

    #========================================================================== 
    # NOT USED AND NOT UPDATED ANY MORE              
    def get_string_for_shark_file(self, row=False, header=False):
        shark_index = []
        shark_string = []
        shark_format = []
        cnv_column = []
        
        for index, col in enumerate(self.cnv_column_info):
            if len(col) == 6:

                shark_index.append(col[3])
                shark_string.append(col[4])
                shark_format.append(col[5])
                cnv_column.append(col[0])
            
   
        text_list = range(len(shark_index))
        header_list = range(len(shark_index))

           
        if row:
            for index, shark_i in enumerate(shark_index):
                text_list[shark_i] = shark_format[index] % row[cnv_column[index]]
            text_line = ''.join(text_list)
            return text_line
        elif header:
            for index, shark_i in enumerate(shark_index):
                header_list[shark_i] = shark_string[index]
#                print header_list
            header_text = '\n# ' + ', '.join(header_list) + ' \n*END*\n'
            return header_text


ctd = CtdProcessing()