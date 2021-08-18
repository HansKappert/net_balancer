import sqlite3
import logging

class persistence:
    DBNAME = 'energy_mediator.db'
    def __init__(self) -> None:
        con = sqlite3.connect(persistence.DBNAME)
        logging.debug ("Database connected")
    
        cur = con.cursor()
        result = cur.execute("PRAGMA table_info(settings)").fetchone()
        if (result == None):
            logging.debug ("Creating table settings")
            cur.execute("CREATE TABLE settings(surplus_delay_theshold,deficient_delay_theshold)")
            cur.execute("INSERT INTO  settings VALUES (0,0)")
            con.commit()
    
        result = cur.execute("PRAGMA table_info(readings)").fetchone()
        if (result == None):
            logging.debug ("Creating table readings")
            cur.execute("CREATE TABLE readings(surplus,current_consumption,current_production,surplus_delay_count,deficient_delay_count,override)")
            cur.execute("INSERT INTO  readings VALUES (0,0,0,0,0,0)")
            con.commit()
            con.close()


    def __get_reading_column_value(self, column_name):
        cur = sqlite3.connect(persistence.DBNAME).cursor() ## TODO: is dit veilig genoeg (geen conflict met update cursor, oude data etc.?)
        result = cur.execute("SELECT " + column_name + " FROM readings").fetchone()
        return result[0]
    
    def __set_reading_column_value(self, column_name, value):
        con = sqlite3.connect(persistence.DBNAME)
        cur = con.cursor()
        result = cur.execute("UPDATE readings SET " + column_name + " = :value",{"value":value})
        con.commit()
        con.close()
    
    def get_surplus(self):
        return self.__get_reading_column_value("surplus")
    def set_surplus(self,value):
        self.__set_reading_column_value("surplus", value)

    def get_override(self):
        return self.__get_reading_column_value("override")
    def set_override(self,value):
        self.__set_reading_column_value("override", value)


    def get_current_production(self):
        return self.__get_reading_column_value("current_production")
    def set_current_production(self,value):
        self.__set_reading_column_value("current_production", value)

    def get_current_consumption(self):
        return self.__get_reading_column_value("current_consumption")
    def set_current_consumption(self,value):
        self.__set_reading_column_value("current_consumption", value)

    def get_surplus_delay_count(self):
        return self.__get_reading_column_value("surplus_delay_count")
    def set_surplus_delay_count(self,value):
        self.__set_reading_column_value("surplus_delay_count", value)


    def get_deficient_delay_count(self):
        return self.__get_reading_column_value("deficient_delay_count")
    def set_deficient_delay_count(self,value):
        self.__set_reading_column_value("deficient_delay_count", value)


    def get_surplus_delay_theshold(self):
        cur = sqlite3.connect(persistence.DBNAME).cursor()
        result = cur.execute("SELECT surplus_delay_theshold FROM settings").fetchone()
        return result[0]
    def set_surplus_delay_theshold(self, value):
        con = sqlite3.connect(persistence.DBNAME)
        cur = con.cursor()
        result = cur.execute("UPDATE settings SET surplus_delay_theshold = :value",{"value":value})
        con.commit()
        con.close()
    
    def get_deficient_delay_theshold(self):
        cur = sqlite3.connect(persistence.DBNAME).cursor()
        result = cur.execute("SELECT deficient_delay_theshold FROM settings").fetchone()
        return result[0]
    def set_deficient_delay_theshold(self, value):
        con = sqlite3.connect(persistence.DBNAME)
        cur = con.cursor()
        result = cur.execute("UPDATE settings SET deficient_delay_theshold = :value",{"value":value})
        con.commit()
        con.close()

