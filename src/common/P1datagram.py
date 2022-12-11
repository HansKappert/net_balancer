import datetime

class P1datagram:    
    def __init__(self) -> None:
        self.equipment_identifier = None                         # 0-0:96.1.1(4530303236333030303334303439363136)
        self.version_info_p1_output = 0                          # 1-3:0.2.8(42)
        self.datetime_stamp = ""                                 # 0-0:1.0.0(210529154722S) YYMMDDhhmmssX
        self.meter_reading_delivered_to_client_low = 0           # 1-0:1.8.1(011827.640*kWh)
        self.meter_reading_delivered_to_client_normal = 0        # 1-0:1.8.2(009437.621*kWh)
        self.meter_reading_delivered_by_client_low = 0           # 1-0:2.8.1(001798.980*kWh)
        self.meter_reading_delivered_by_client_normal = 0        # 1-0:2.8.2(004382.306*kWh)
        self.tarif_indicator_electricity = 0                     # 0-0:96.14.0(0001)  1=low, 2=normal tariff 
        self.actual_electricity_power_received = None            # 1-0:2.7.0(1.234*kW)  received from customer
        self.actual_electricity_power_delivered = None           # 1-0:1.7.0(0.215*kW)  devlived to customer
        self.nr_of_power_failures_any_phase = 0                  # 0-0:96.7.21(00000)
        self.nr_of_long_power_failures_any_phase = 0             # 0-0:96.7.9(00000)
        self.power_failure_event_log = ""                        # 1-0:99.97.0(1)(0-0:96.7.19)(000101000017W)(2147483647*s)
        self.nr_of_voltage_sags_in_phase_L1 = 0                  # 1-0:32.32.0(00008)
        self.nr_of_voltage_sags_in_phase_L2 = 0                  # 1-0:52.32.0(00008)
        self.nr_of_voltage_sags_in_phase_L3 = 0                  # 1-0:72.32.0(00011)
        self.nr_of_voltage_swells_in_phase_L1 = 0                # 1-0:32.36.0(00000)
        self.nr_of_voltage_swells_in_phase_L2 = 0                # 1-0:52.36.0(00000)
        self.nr_of_voltage_swells_in_phase_L3 = 0                # 1-0:72.36.0(00000)
        # undocumented      0-0:96.13.1()
        self.text_message_max = ""                               # 0-0:96.13.0()
        self.instantaneous_current_L1 = 0                        # 1-0:31.7.0(000*A)
        self.instantaneous_current_L2 = 0                        # 1-0:51.7.0(003*A)
        self.instantaneous_current_L3 = 0                        # 1-0:71.7.0(002*A)
        self.instantaneous_active_power_L1_PlusP = 0             # 1-0:21.7.0(00.002*kW)
        self.instantaneous_active_power_L2_PlusP = 0             # 1-0:41.7.0(00.000*kW)
        self.instantaneous_active_power_L3_PlusP = 0             # 1-0:61.7.0(00.000*kW)
        self.instantaneous_active_power_L1_MinusP = 0            # 1-0:22.7.0(00.000*kW)
        self.instantaneous_active_power_L2_MinusP = 0            # 1-0:42.7.0(00.780*kW)
        self.instantaneous_active_power_L3_MinusP = 0            # 1-0:62.7.0(00.470*kW)
        # undocumented      0-1:24.1.0(003)
        # undocumented      0-1:96.1.0(4730303332353631323838313236303137)
        self.gas_metering                         = 0            # 0-1:24.2.1(210529150000S)(03072.410*m3)

    def _strip_to_string(self, string_value):
        string_value = string_value[:-1]
        return string_value

    def _strip_to_number(self, string_value):
        string_value = string_value.strip(')').strip('*kWh').strip('*kW').strip('*A').replace(".","")
        return int(string_value)

    def _strip_gas_meter_value(self, string_value):
        string_value = string_value.strip('*m3)')
        gas_metering = float(string_value)
        return gas_metering

    def _strip_to_date(self, string_value):
        string_value = string_value.strip(')')
        # turn string with format YYMMDDhhmmssX into datetime
        datetimeobj=datetime.datetime.strptime(string_value[:-1], "%y%m%d%H%M%S")
        return datetimeobj

    def fill(self, raw_data_array):
        # put all data in a dictionary
        for entry in raw_data_array:
            pieces = entry.split('(')
            if len(pieces) == 2:
                obis_ref = pieces[0]
                obis_value = pieces[1]
                if obis_ref == "0-0:96.1.1":    self.equipment_identifier                      = self._strip_to_number(obis_value)
                elif obis_ref == "1-3:0.2.8":   self.version_info_p1_output                    = self._strip_to_number(obis_value)
                elif obis_ref == "0-0:1.0.0":   self.datetime_stamp                            = self._strip_to_date(obis_value)
                elif obis_ref == "1-0:1.8.1":   self.meter_reading_delivered_to_client_low     = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:1.8.2":   self.meter_reading_delivered_to_client_normal  = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:2.8.1":   self.meter_reading_delivered_by_client_low     = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:2.8.2":   self.meter_reading_delivered_by_client_normal  = self._strip_to_number(obis_value)
                elif obis_ref == "0-0:96.14.0": self.tarif_indicator_electricity               = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:2.7.0":   self.actual_electricity_power_received         = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:1.7.0":   self.actual_electricity_power_delivered        = self._strip_to_number(obis_value)
                elif obis_ref == "0-0:96.7.21": self.nr_of_power_failures_any_phase            = self._strip_to_number(obis_value)
                elif obis_ref == "0-0:96.7.9":  self.nr_of_long_power_failures_any_phase       = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:99.97.0": self.power_failure_event_log                   = entry[entry.find("("):]
                elif obis_ref == "1-0:32.32.0": self.nr_of_voltage_sags_in_phase_L1            = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:52.32.0": self.nr_of_voltage_sags_in_phase_L2            = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:72.32.0": self.nr_of_voltage_sags_in_phase_L3            = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:32.36.0": self.nr_of_voltage_swells_in_phase_L1          = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:52.36.0": self.nr_of_voltage_swells_in_phase_L2          = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:72.36.0": self.nr_of_voltage_swells_in_phase_L3          = self._strip_to_number(obis_value)
                elif obis_ref == "0-0:96.13.0": self.text_message_max                          = self._strip_to_string(obis_value)
                elif obis_ref == "1-0:31.7.0":  self.instantaneous_current_L1                  = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:51.7.0":  self.instantaneous_current_L2                  = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:71.7.0":  self.instantaneous_current_L3                  = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:21.7.0":  self.instantaneous_active_power_L1_PlusP       = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:41.7.":   self.instantaneous_active_power_L2_PlusP       = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:61.7.0":  self.instantaneous_active_power_L3_PlusP       = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:22.7.0":  self.instantaneous_active_power_L1_MinusP      = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:42.7.0":  self.instantaneous_active_power_L2_MinusP      = self._strip_to_number(obis_value)
                elif obis_ref == "1-0:62.7.0":  self.instantaneous_active_power_L3_MinusP      = self._strip_to_number(obis_value)  
            elif len(pieces) == 3:
                obis_ref = pieces[0]
                obis_value = pieces[2]
                if obis_ref == "0-1:24.2.1":  self.gas_metering                              = self._strip_gas_meter_value(obis_value)