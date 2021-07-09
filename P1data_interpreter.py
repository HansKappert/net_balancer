def raw_to_dictionary(raw_data_array):
    data = {}

    # put all data in a dictionary
    for entry in raw_data_array:
        pieces = entry.split('(')
        if len(pieces) == 2:
            data[pieces[0]] = pieces[1].strip(')').strip('*kWh').strip('*kW')

    return data