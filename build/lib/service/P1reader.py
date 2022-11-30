#
# DSMR P1 uitlezer
# (c) 10-2012 - GJ - gratis te kopieren en te plakken

versie = "1.0"
import sys
from webbrowser import Error
import serial
import logging
from service.abc_P1data_reader import P1data_reader

class P1reader(P1data_reader):
    def __init__(self, port="/dev/ttyUSB0") -> None:
        #Set COM port config
        self.ser = serial.Serial()
        self.ser.baudrate = 115200
        self.ser.bytesize=serial.EIGHTBITS
        self.ser.parity=serial.PARITY_NONE
        self.ser.stopbits=serial.STOPBITS_ONE
        self.ser.xonxoff=0
        self.ser.rtscts=0
        self.ser.timeout=20
        self.ser.port=port

    def read_data(self):
        data = []
        p1_teller=0
        data_frame=[]
        err = ""
        #Open COM port
        try:
            self.ser.open()
        except Exception as e:
            err = "Error while opening serial device {}: {}".format(self.ser.name, e)
            logging.error(err)
            return data, err


        while p1_teller < 36:
            p1_line=''
        #Read 1 line
            try:
                p1_raw = self.ser.readline()
                logging.debug(p1_raw)
            except:
                err = ("Cannot read serial port %s. Incomplete data frame returned." % self.ser.name)
                logging.error(err) 
                return data_frame, err
            #p1_str=str(p1_raw)
            p1_str=str(p1_raw, "utf-8")
            p1_line=p1_str.strip()
            data_frame.append(p1_line)
            #print (p1_line)
            p1_teller = p1_teller +1

        
        #Close port and show status
        try:
            self.ser.close()
        except:
            err = ("Cannot close serial port %s." % self.ser.name)
            logging.error(err)    

        return data_frame, err
    
