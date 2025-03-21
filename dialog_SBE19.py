# -*- coding: utf-8 -*-
"""
Created on Mon Feb 06 11:19:04 2012
Program to open a dialog box and get a file, check the file name and send it 
along with the serienummer
@author: a001109
"""

def checkCtdFileName(ctd=None, confile='.xmlcon'):
    import Tkinter, tkFileDialog
    import os
    import time
    import sys
    import shutil
    import codecs
    root = Tkinter.Tk()
    root.withdraw() #hiding tkinter window 
    
    if ctd == None:
        sys.exit("No CTD given, when calling checkCtdFileName() add a CTD number like checkCtdFileName(ctd='1044')")
    
    file_path = tkFileDialog.askopenfilename(title="Open file", initialdir="C:\\ctdSBE19\\temp",
    filetypes=[("hex files",".hex"), ("hdr files",".hdr")]) 
#    if '/' in file_path:
#        file_path = file_path.replace('/','\\')
           
    fname = os.path.basename(file_path).upper()
    #print fname    
    path = os.path.dirname(file_path)
    path = "C:\\ctdSBE19\\temp"

    #Ctd from Dana
    if fname[:4] == '26DA':
        #Dana filenames usually look lite this:  26DA.2016.10.1.hdr
        #Merge Cruisenr and activity number 1001. Add zeros.       
        #If serienummer is over 100 add this to next cruise nr 1000        
        if int(fname.split('.')[3].zfill(2)) > 99:                
            serienummer = str(int(fname.split('.')[2])+1).zfill(2) + fname.split('.')[3][1:]            
        else:                        
            serienummer = fname.split('.')[2].zfill(2) + fname.split('.')[3].zfill(2)    
        
    #CTD from Aranda or Meri or Aura
    elif fname[:2] == 'AR' or fname[:2] == 'ME' or fname[:2] == 'AU':
        #serienummer = fname[3:7]
        if len(fname) == 12:
            serienummer = fname[5:8]
            # justerar till 4 siffror
            serienummer = serienummer.zfill(4)
        else: # if series is 4 digits
            serienummer = fname[5:8]
            serienummer = serienummer.zfill(4)
    #Svea            
    elif fname[:2].upper() == 'SV': # Svea
        serienummer = fname[5:9]

    #CTD in processed format: 'SBE09_0745_20161010_1139_34_01_0544.hdr'
    #to be reprocessed

    #nytt namnformat används och då skall man läsa ut cruise number
    #SBE19_6164_20110801_1550_77SE_01_0053
    elif '77SE' in fname:        
        cruise = fname.split('_')[-2]
        cruise = cruise.zfill(2)        
        print 'Cruise: ', cruise     
        print fname        
        serienummer = fname.split('_')[-1][:4]
        
    elif fname[:5] == 'SBE09' or 'SBE19':     
        serienummer = fname.split('_')[-1][:4]
    
    else:
        sys.exit('could not get "serienummer" from file name %s, stops!' % fname)
           
    print 'serienummer: ',serienummer 
    
    # Open the header file or the xml-file (SBE19):
    with codecs.open(file_path,'r',encoding='cp1252') as f:
        allHeaderInfo = f.readlines()
    f.closed

    if fname[:5] == 'SBE09':    
        for rows in allHeaderInfo:
            #print rows
            if '* System UpLoad Time' in rows:
                datestring = rows[23:40]
            if '** Station:' in rows:
                stationname = rows[11:].strip(' \r\n')
            else:
                #CTDdata från Dana har stationsnamn men inget '** Station:'
                #stationname = ''
                pass
        print stationname
        #Feb 28 2012 16:13 -> 20120228_1613
        c = time.strptime(datestring,"%b %d %Y %H:%M")
        datum = time.strftime("%Y%m%d_%H%M",c)
    
    elif fname[:5] == 'SBE19':
        for rows in allHeaderInfo:
            #print rows
            if '* cast' in rows:
                datestring = rows[11:28]
            if '** Station:' in rows:
                stationname = rows[11:].strip(' \r\n')
            else:
                #CTDdata från Dana har stationsnamn men inget '** Station:'
                #stationname = ''
                pass
        print stationname
        #03 Sep 2020 13:38 -> 20200903_1338        
        c = time.strptime(datestring,"%d %b %Y %H:%M")
        datum = time.strftime("%Y%m%d_%H%M",c)
                    
    if fname[:2] == 'AR':
        new_fname = 'SBE09_' + ctd + '_' + datum + '_34_01_' + serienummer
    elif fname[:2] == 'ME':    
        new_fname = 'SBE09_' + ctd + '_' + datum + '_34_02_' + serienummer
    elif fname[:2] == 'AU':    
        new_fname = 'SBE09_' + ctd + '_' + datum + '_34_07_' + serienummer
    elif fname[:4] == '26DA':
        new_fname = 'SBE09_' + ctd + '_' + datum + '_26_01_' + serienummer
    elif fname[:5] == 'SBE09': 
        new_fname = fname.split('.')[0]
    elif fname[:2] == 'SV': #nytt Svea, 2019-10-02 jkro
        new_fname = 'SBE09_' + ctd + '_' + datum + '_77_10_' + serienummer
        #SBE19_6164_20110801_1550_77_10_0053...old format
    elif fname[:5] == 'SBE19'and ctd in ['6164','6929'] and '77SE' not in fname:    
        new_fname = 'SBE19_' + ctd + '_' + datum + '_77_10_' + serienummer
        #SBE19_6164_20110801_1550_77SE_01_0053....new format
    elif fname[:5] == 'SBE19'and ctd in ['6164','6929'] and '77SE' in fname:    
        new_fname = 'SBE19_' + ctd + '_' + datum + '_77SE_' + cruise + '_' + serienummer                
    elif fname[:5] == 'SBE19' and ctd == '6537':    
        new_fname = fname.split('.')[0]
        #Kollar om man skrivit in rätt datum        
        if new_fname != fname[:-4] and ctd !='6537':
            print new_fname
            print fname
            sys.exit('Fel datum i filnamnet på SBE19! Jämför headerinfo och datum i filnamet')                        
    else:
        sys.exit('Fel format serienummer!')
      
    print new_fname
    #fname = 'SBE19_0745_20110409_0522_77_28_0053.hex'
    
    #Hämta aktuell xmlcon fil och kopierar den till rätt ställe.    
    file_path_xmlcon = tkFileDialog.askopenfilename(title="Open file", initialdir="C:\\ctdSBE19\\setup",
    filetypes=[("xmlcon",".xmlcon")]) 
    
    shutil.copy(file_path_xmlcon,path + '/' + new_fname + '.xmlcon')
        
    
    #fname = os.path.basename(file_path)
    sub_str = new_fname.split('_')
    #sub_str = fname.split('_')
    #Kontrollera filnames längd:
    #SBE19_6164_20110801_1550_77_01_0053.hex
    if fname[:5] == 'SBE19' and ctd == '6537':    
        print 'Skip test, name as original'
        serieNo = fname.split('_')[-1][:4]
        print serieNo
    else:
        counter = 0
        for part in sub_str:  
            counter = counter + 1    
            if counter == 1:
                #kontrollera filnamn, ev behöver vi lägga in en bättre kontroll
                #print counter        
                #print part            
                if part not in ['SBE09', 'SBE19']:        
                    sys.exit('Fel instrumentnamn!')                          
            if counter == 2:
                #print counter        
                if part not in ['0745','1044','0817','0403','0827', '1387','6164','6537','6929']:        
                    sys.exit('Fel intrument serienummer!')                      
            if counter == 3:
                #print counter        
                if len(part) != 8:        
                    sys.exit('Fel datumformat!')
            if counter == 4:
                #print counter        
                if len(part) != 4:        
                    sys.exit('Fel tidsformat!')
            if counter == 5:
                #print counter        
                if part == 34:        
                    sys.exit('Fel landkod!')
            if counter == 6:
                #print counter        
                if part == 01:        
                    sys.exit('Fel fartygskod!')
            if counter == 7:
                #print counter
                serieNo = part.split('.')[0]
                print serieNo    
                if len(part.split('.')[0]) != 4:        
                    sys.exit('Fel format serienummer!') 
    #            if part.split('.')[1] != 'hex':
    #                sys.exit('Fel filformat skall vara *.hex!') 
    #print fname
    #print new_fname
    #print 'Done 1' 
    #Ändrar namnet på filerna men enbart om de är olika.   
    if fname.split('.')[0] != new_fname and ctd != '6537':
        #os.rename(file_path, path + '\\' + new_fname + '.hdr')
        #print path + '\\' + fname.rsplit('.',1)[0] + confile
        #print path + '\\' + new_fname + confile
        #path = path.replace('/','\\')
        # print (path + '\\' + fname.rsplit('.',1)[0] + confile, path + '\\' + new_fname + confile)
        # print('fname',fname)
        # print(fname.rsplit('.',1)[0])
        # print('confile',confile)
        # print('path',path)
        # print('new_fname',new_fname)
        # print('file',path + '\\' + fname.rsplit('.',1)[0] + confile.lower())
        print(path, fname, new_fname, confile) #nytt för test
        os.rename(path + '\\' + fname.rsplit('.',1)[0] + confile.lower(), path + '\\' + new_fname + confile.lower())
        os.rename(path + '\\' + fname.rsplit('.',1)[0] + '.hex', path + '\\' + new_fname + '.hex')
        os.rename(path + '\\' + fname.rsplit('.',1)[0] + '.bl', path + '\\' + new_fname + '.bl')    
    print 'Done with dialog_SBE19.py!'      
    return new_fname, serieNo, stationname

  
    #Korrekt namn format: Kontrollera namnet
    #SBE19plus_01906164_2011_08_03_0001.hex
    #SBE19_6164_20110801_1550_77_01_0053
