from datetime import datetime
from webbrowser import Error
import logging
from service.abc_P1data_reader import P1data_reader


class P1reader_stub(P1data_reader):
    def __init__(self, port) -> None:
        # make sure the length of the two following arrays are equal.
        self.leveringen = [1000,500,100,100,  0,   0,  0,300,500]
        self.gebruik    = [250 ,230,250,400,300, 330,250,250,280]
        self.index = 0
        pass

    def read_data(self):
        data_frame=[]
        err = ""
        
        afname = 0
        data_frame.append('0-0:96.1.1(4530303236333030303334303439363136')
        version_info_p1_output = 0
        now = datetime.now()                         
        date_time_string = now.strftime("%y%m%d%H%M%S")
        data_frame.append(f'0-0:1.0.0({date_time_string}S)')
        data_frame.append('1-3:0.2.8(42)')
        data_frame.append('0-0:96.14.0(0001)')
        data_frame.append(f'1-0:1.7.0({self.gebruik[self.index]/1000:.3f}*kW)')              
        data_frame.append(f'1-0:2.7.0({self.leveringen[self.index]/1000:.3f}*kW)')
        
        self.index += 1
        if self.index >= len(self.leveringen):
            self.index = 0

        return data_frame, err
    