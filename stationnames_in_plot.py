# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 13:30:51 2020

@author: a001695
"""

def insert_station_name(station="", my_plot_psa_file=""):
    '''Uppdaterar en PSA-fil och skriver in stationsnamnet. Används för plottar.'''
    
    #print u'station=', station
    #print my_plot_psa_file

    #kolla att filen är en psa-fil    
    if my_plot_psa_file[-3:] == u'psa' and \
        u'SeaPlot' in my_plot_psa_file:
            
        f = open(my_plot_psa_file, 'r')
        contents = f.readlines()
        f.close()
        
        f = open(my_plot_psa_file, 'w')
        for lines in contents:
            #print lines
            if lines[0:15] == "  <Title value=":
                lines = lines[:16] + station.encode('utf-8') + lines[-5:]
            f.write(lines)
        f.close()
