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
    with open(fname, 'r', encoding='latin-1', errors='replace') as f:
        # Gobble up all the info into a list
        allInfo = f.readlines()
    # Close the file
    f.closed
    
    # Use a loop to go through the file
    # (This probably isn't the most effective
    # method...)
    for rows in allInfo:
        # Check it's not a blank line
        if rows.strip() != '':
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
    
def readPRS(fname):
    from re import split, search
    import numpy as np
    #
    header = []
    cnvData = []
    colList = []
    
    # Open the cnv file:
    with open(fname, 'r', encoding='utf-8', errors='replace') as f:
        # Gobble up all the info into a list
        allInfo = f.readlines()
    # Close the file
    f.closed
    
    # Use a loop to go through the file, skipping the first line
    for iR in range(1,len(allInfo)):
        numList = []
        rows = allInfo[iR]
        # print '%s' % rows.strip()
        if '*' in rows and '|' not in rows:
            colList = split('\s+',rows.strip())
        elif '|' in rows:
            header.append(rows.strip())
        # elif '        ' not in rows and '-----' not in rows:
        elif rows.count(',') > 5:
            # If we have a data row, then we need to convert
            # them to a list of floats. In the file format, 
            # the data are both comma and space delimited(!)
            # If the current line is a data line, then the
            # conversion to float should fail, and we can go to
            # the 'except' clause
    
            # Need to convert rows to a list
            # of numbers
            # Split of commas, because some files include
            # blank spaces instead of values(!)
            rowList = split(',',rows.strip())
            lastTwoCols = rowList.pop()
            nobs, dpth = split('\s+', lastTwoCols.strip())
            rowList.append(nobs)
            rowList.append(dpth)
            del nobs
            del dpth
            del lastTwoCols

            # Bloody useless and inconsistent format
            # Try converting to numbers
            for entries in rowList:
                if search('\S',entries) is not None:
                    # print '%i, %s,' % (entries.count(' '), entries)
                    numList.append(float(entries))
                else:
                    numList.append(np.NaN)
            cnvData.append(numList)

    # Return these results
    cnvInfo = header, colList, cnvData
    return cnvInfo    