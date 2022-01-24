import sqlite3
import logging
from datetime import datetime, timedelta


class persistence:
    DBNAME = 'energy_mediator.db'
    def __init__(self) -> None:
        con = sqlite3.connect(persistence.DBNAME)
        logging.debug ("Database connected")
    
        cur = con.cursor()
        result = cur.execute("PRAGMA table_info(settings)").fetchone()
        if (result == None):
            logging.debug ("Creating table settings")
            cur.execute("CREATE TABLE settings (surplus_delay_theshold INTEGER, deficient_delay_theshold INTEGER, log_retention_days INTEGER);")
            cur.execute("INSERT INTO  settings VALUES (40,40,1)")
            con.commit()
    
        cur = con.cursor()
        result = cur.execute("PRAGMA table_info(readings)").fetchone()
        if (result == None):
            logging.debug ("Creating table readings")
            cur.execute("CREATE TABLE readings(surplus INTEGER,current_consumption INTEGER,current_production INTEGER,surplus_delay_count INTEGER,deficient_delay_count INTEGER)")
            cur.execute("INSERT INTO  readings VALUES (0,0,0,0,0)")
            con.commit()

        result = cur.execute("PRAGMA table_info(consumer)").fetchall()
        if (result == None):
            logging.debug ("Creating table consumer")
            cur.execute("CREATE TABLE consumer(name TEXT, consumption_max INTEGER, consumption_now INTEGER, balance BOOLEAN NOT NULL CHECK (balance IN (0, 1)), disabled BOOLEAN NOT NULL CHECK (disabled IN (0, 1)))")
            cur.execute("INSERT INTO  consumer VALUES ('Tesla', 3680, 0, 1, 0)")
            con.commit()
        else:
            if (result[3][1] == 'override'):
                cur.execute("ALTER TABLE consumer RENAME COLUMN override TO balance")
                con.commit()

        cur = con.cursor()
        result = cur.execute("PRAGMA table_info(tesla)").fetchone()
        if (result == None):
            logging.debug ("Creating table tesla")
            cur.execute("CREATE TABLE tesla(charge_until INTEGER, home_latitude REAL, home_longitude REAL, current_latitude REAL, current_longitude REAL)")
            cur.execute("INSERT INTO  tesla VALUES (80, 0.0, 0.0, 0.0, 0.0)")
            con.commit()


        cur = con.cursor()
        result = cur.execute("PRAGMA table_info(event)").fetchone()
        if (result == None):
            logging.debug ("Creating table event")
            cur.execute("CREATE TABLE event(log_date, levelname, source, message, occurrences)")
            con.commit()


        cur = con.cursor()
        result = cur.execute("PRAGMA index_info(last_event)").fetchone()
        if (result == None):
            logging.debug ("Creating index last_event")
            cur.execute("create index last_event on event (log_date);")
            con.commit()
        con.close()


    def get_db_connection(self):
        conn = sqlite3.connect(persistence.DBNAME)
        conn.row_factory = sqlite3.Row
        return conn

    def log_event(self, levelname:str, source:str, message:str):
        con = self.get_db_connection()
        result = con.execute("SELECT log_date, message FROM event ORDER BY log_date DESC").fetchone()
        log_date = datetime.now()
        if not result == None and result[1] == message:
                result = con.execute("UPDATE event SET log_date = :new_log_date, occurrences = occurrences + 1 WHERE log_date = :old_log_date",{"new_log_date": log_date, "old_log_date": result[0]})
        else:
            result = con.execute("INSERT INTO event VALUES (:log_date, :levelname, :source, :message, 1)",{"log_date": log_date, "levelname":levelname, "source":source, "message":message})
        con.commit()
        con.close()

    def __get_reading_column_value(self, column_name):
        con = self.get_db_connection()
        result = con.execute("SELECT " + column_name + " FROM readings").fetchone()
        return result[0]
    
    def __set_reading_column_value(self, column_name, value):
        con = self.get_db_connection()
        result = con.execute("UPDATE readings SET " + column_name + " = :value",{"value":value})
        con.commit()
        con.close()
    
    def get_surplus(self):
        return self.__get_reading_column_value("surplus")
    def set_surplus(self,value):
        self.__set_reading_column_value("surplus", value)


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
        con = self.get_db_connection()
        result = con.execute("SELECT surplus_delay_theshold FROM settings").fetchone()
        return result[0]
    def set_surplus_delay_theshold(self, value):
        con = self.get_db_connection()
        result = con.execute("UPDATE settings SET surplus_delay_theshold = :value",{"value":value})
        con.commit()
        con.close()
    
    def get_deficient_delay_theshold(self):
        con = self.get_db_connection()
        result = con.execute("SELECT deficient_delay_theshold FROM settings").fetchone()
        return result[0]
    def set_deficient_delay_theshold(self, value):
        con = self.get_db_connection()
        result = con.execute("UPDATE settings SET deficient_delay_theshold = :value",{"value":value})
        con.commit()
        con.close()

    #  consumer consumption_max
    def get_consumer_consumption_max(self, consumer_name):
        con = self.get_db_connection()
        result = con.execute("SELECT consumption_max FROM consumer WHERE name = :consumer_name",{"consumer_name":consumer_name}).fetchone()
        if result == None:
            return 0
        return int(result[0])
    def set_consumer_consumption_max(self, consumer_name, value):
        con = self.get_db_connection()
        result = con.execute("UPDATE consumer SET consumption_max = :value WHERE name = :consumer_name",{"value":value, "consumer_name":consumer_name})
        con.commit()
        con.close()

    # consumer consumption_now
    def get_consumer_consumption_now(self, consumer_name):
        con = self.get_db_connection()
        result = con.execute("SELECT consumption_now FROM consumer WHERE name = :consumer_name",{"consumer_name":consumer_name}).fetchone()
        if result == None:
            return 0
        return int(result[0])
    def set_consumer_consumption_now(self, consumer_name, value):
        con = self.get_db_connection()
        result = con.execute("UPDATE consumer SET consumption_now = :value WHERE name = :consumer_name",{"value":value, "consumer_name":consumer_name})
        con.commit()
        con.close()

    # consumer charge_until
    def get_tesla_charge_until(self):
        con = self.get_db_connection()
        result = con.execute("SELECT charge_until FROM tesla").fetchone()
        return int(result[0])
    def set_tesla_charge_until(self, value):
        con = self.get_db_connection()
        result = con.execute("UPDATE tesla SET charge_until = :value",{"value":value})
        con.commit()
        con.close()

    #  consumer balance
    def get_consumer_balance(self, consumer_name):
        con = self.get_db_connection()
        result = con.execute("SELECT balance FROM consumer WHERE name = :consumer_name",{"consumer_name":consumer_name}).fetchone()
        return int(result[0])
    def set_consumer_balance(self, consumer_name, value):
        con = self.get_db_connection()  
        result = con.execute("UPDATE consumer SET balance = :value WHERE name = :consumer_name",{"value":value, "consumer_name":consumer_name})
        con.commit()
        con.close()

    #  consumer disabled
    def get_consumer_disabled(self, consumer_name):
        con = self.get_db_connection()
        result = con.execute("SELECT disabled FROM consumer WHERE name = :consumer_name",{"consumer_name":consumer_name}).fetchone()
        return int(result[0])
    def set_consumer_disabled(self, consumer_name, value):
        con = self.get_db_connection()  
        result = con.execute("UPDATE consumer SET disabled = :value WHERE name = :consumer_name",{"value":value, "consumer_name":consumer_name})
        con.commit()
        con.close()


    #  log retention
    def get_log_retention(self):
        con = self.get_db_connection()
        result = con.execute("SELECT log_retention_days FROM settings").fetchone()
        return int(result[0])
    def set_log_retention(self, value):
        con = self.get_db_connection()  
        result = con.execute("UPDATE settings SET log_retention_days = :value ",{"value":value})
        con.commit()
        con.close()


    def get_log_lines(self):
        con = self.get_db_connection()
        result = con.execute("SELECT * FROM event ORDER BY log_date DESC").fetchall()
        return result

    def remove_old_log_lines(self):
        con = self.get_db_connection()
        result = con.execute("select log_retention_days from settings").fetchone()
        log_retention_hours = int(result[0])
        result = con.execute("DELETE FROM event WHERE log_date < datetime('now', '-{} hours')".format(log_retention_hours))
        con.commit()
        con.close()
        return result

    # tesla home_coords
    def get_tesla_home_coords(self):
        con = self.get_db_connection()
        result = con.execute("SELECT home_latitude, home_longitude FROM tesla").fetchone()
        return (result[0],result[1])
    def set_tesla_home_coords(self, home_latitude, home_longitude):
        con = self.get_db_connection()
        result = con.execute("UPDATE tesla SET home_latitude = :home_latitude, home_longitude = :home_longitude",{"home_latitude":home_latitude,"home_longitude":home_longitude})
        con.commit()
        con.close()

    # tesla current_coords
    def get_tesla_current_coords(self):
        con = self.get_db_connection()
        result = con.execute("SELECT current_latitude, current_longitude FROM tesla").fetchone()
        return (result[0],result[1])
    def set_tesla_current_coords(self, current_latitude, current_longitude):
        con = self.get_db_connection()
        result = con.execute("UPDATE tesla SET current_latitude = :current_latitude, current_longitude = :current_longitude",{"current_latitude":current_latitude,"current_longitude":current_longitude})
        con.commit()
        con.close()
