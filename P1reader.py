#
# DSMR P1 uitlezer
# (c) 10-2012 - GJ - gratis te kopieren en te plakken

versie = "1.0"
import sys
import serial


class P1reader:
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
        #Open COM port
        try:
            self.ser.open()
        except:
            return data, "Fout bij het openen van %s. We gaan verder obv hard coded string."  % self.ser.name


        while p1_teller < 20:
            p1_line=''
        #Read 1 line
            try:
                p1_raw = self.ser.readline()
            except:
                sys.exit ("Seriele poort %s kan niet gelezen worden. Programma afgebroken." % self.ser.name ) 
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
            sys.exit ("Oops %s. Programma afgebroken." % self.ser.name )    

        return data_frame, ""
    
