# -*- coding: utf-8 -*-
"""
Read in header and data from a CNV file.

Variables: 
    fname - the full name and path of the CNV file
    header - header information (a list)
    cnvData - an array of numbers
    cnvInfo - a tuple containing header & cnvData

Created on Wed Mar 17 09:47:45 2010
@author: a001082
"""

def readCNV(fname):
    from re import match
    from re import split
    header = []
    cnvData = []
    colList = []
    
    # Open the cnv file:
    with open(fname, 'r', encoding='utf-8', errors='replace') as f:
        # Gobble up all the info into a list
        allInfo = f.readlines()
    # Close the file
    f.closed
    
    # Use a loop to go through the file
    # (This probably isn't the most effective
    # method...)
    for rows in allInfo:
        if match('[\#\*]',rows):
            header.append(rows)
            if match('\# name ',rows):
                colList.append(rows)
        else:
            # Need to convert rows to a list
            # of numbers
            numList = []
            listRow = rows.strip().split()
            for mems in listRow:
                numList.append(float(mems))                
            cnvData.append(numList)            
            
    # Return these results
    cnvInfo = header, colList, cnvData
    return cnvInfo
    
    