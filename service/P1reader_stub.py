#
# DSMR P1 uitlezer
# (c) 10-2012 - GJ - gratis te kopieren en te plakken

versie = "1.0"
import sys
from webbrowser import Error
import serial
import logging
from service.abc_P1data_reader import P1data_reader


class P1reader_stub(P1data_reader):
    def __init__(self, port) -> None:
        self.leveringen = [2500,2500,2500,2500,2500,1000,1000,1000,1000,1000]
        self.index = 0
        pass

    def read_data(self):
        data_frame=[]
        err = ""
        
        afname = 0
        data_frame.append(f'1-0:1.7.0({afname/1000:.3f}*kW)')
                
        data_frame.append(f'1-0:2.7.0({self.leveringen[self.index]/1000:.3f}*kW)')
        
        self.index += 1
        if self.index >= len(self.leveringen):
            self.index = 0

        return data_frame, err
    
