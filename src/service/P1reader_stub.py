from datetime import datetime
from webbrowser import Error
import logging
from service.abc_P1data_reader import P1data_reader


class P1reader_stub(P1data_reader):
    def __init__(self, port) -> None:
        # make sure the length of the two following arrays are equal.
        self.leveringen = [1000,500,100,100,  0,   0,  0,300,500]
        self.gebruik    = [250 ,230,250,400,300, 330,250,250,280]
        self.gas_usages = [0.001,0.002,0.002,0.003,0.002,0.002,0.001,0.0,0.0,0.3]
        self.index = 0
        self.gasmeter = 100
        self.meter_reading_delivered_by_client_low    = 1000
        self.meter_reading_delivered_by_client_normal = 1000
        self.meter_reading_delivered_to_client_low    = 1000
        self.meter_reading_delivered_to_client_normal = 1000
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

        data_frame.append(f'0-1:24.2.1(210529150000S)({self.gasmeter:09.3f}*m3)')

        data_frame.append(f'1-0:1.8.1({self.meter_reading_delivered_to_client_low:010.3f}*kWh)')
        data_frame.append(f'1-0:1.8.2({self.meter_reading_delivered_to_client_normal:010.3f}*kWh)')
        data_frame.append(f'1-0:2.8.1({self.meter_reading_delivered_by_client_low:010.3f}*kWh)')
        data_frame.append(f'1-0:2.8.2({self.meter_reading_delivered_by_client_normal:010.3f}*kWh)')
        
        self.gasmeter += self.gas_usages[self.index]
        self.meter_reading_delivered_by_client_low    += (self.leveringen[self.index]/1000)
        self.meter_reading_delivered_by_client_normal += (self.leveringen[self.index]/1000)
        self.meter_reading_delivered_to_client_low    += (self.gebruik[self.index]/1000)
        self.meter_reading_delivered_to_client_normal += (self.gebruik[self.index]/1000)

        self.index += 1
        if self.index >= len(self.leveringen):
            self.index = 0


        return data_frame, err
    
