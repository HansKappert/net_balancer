import sqlite3
import logging
import time
from datetime                         import date, datetime, timedelta
from common.database_logging_handler  import database_logging_handler


class persistence:
    DBNAME = 'energy_mediator.db'
    def __init__(self) -> None:
        con = self.get_db_connection()
        cur = con.cursor()

        self.logger = logging.getLogger(__name__)
        
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)
        
        log_handler = database_logging_handler(self)
        log_handler.setLevel(logging.INFO)
        self.logger.addHandler(log_handler)

        result = cur.execute("PRAGMA auto_vacuum = FULL").fetchone()
        result = cur.execute("vacuum").fetchone()
        self.logger.debug ("Database connected")

        result = cur.execute("PRAGMA table_info(settings)").fetchall()
        if (result == None):
            self.logger.debug ("Creating table settings")
            cur.execute("CREATE TABLE settings (log_retention_days INTEGER, stats_retention_days INTEGER);")
            cur.execute("INSERT INTO  settings VALUES (40,40)")
            con.commit()
        else:
            for field in result:
                if field[1] == "surplus_delay_theshold":
                    cur.execute("DROP TABLE settings")
                    cur.execute("CREATE TABLE settings (log_retention_days INTEGER, stats_retention_days INTEGER);")
                    cur.execute("INSERT INTO  settings VALUES (40,40)")
                    con.commit()
                    
    
        result = cur.execute("PRAGMA table_info(readings)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table readings")
            cur.execute("CREATE TABLE readings(surplus INTEGER,current_consumption INTEGER,current_production INTEGER)") # deficient_delay_count is obsolete
            cur.execute("INSERT INTO  readings VALUES (0,0,0,0,0)")
            con.commit()

        result = cur.execute("PRAGMA table_info(consumer)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table consumer")
            cur.execute("CREATE TABLE consumer(name TEXT, consumption_max INTEGER, consumption_now INTEGER, balance BOOLEAN NOT NULL CHECK (balance IN (0, 1)), disabled BOOLEAN NOT NULL CHECK (disabled IN (0, 1)))")
            cur.execute("INSERT INTO  consumer VALUES ('Tesla', 3680, 0, 1, 0)")
            con.commit()
        else:
            result = cur.execute("PRAGMA table_info(consumer)").fetchall()
            if (result[3][1] == 'override'):
                cur.execute("ALTER TABLE consumer RENAME COLUMN override TO balance")
                con.commit()

        result = cur.execute("PRAGMA table_info(tesla)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table tesla")
            cur.execute("CREATE TABLE tesla(charge_until INTEGER, home_latitude REAL, home_longitude REAL, current_latitude REAL, current_longitude REAL)")
            cur.execute("INSERT INTO  tesla VALUES (80, 0.0, 0.0, 0.0, 0.0)")
            con.commit()
        else:
            result = cur.execute("PRAGMA table_info(tesla)").fetchall()
            if (len(result) == 5):
                cur.execute("ALTER TABLE tesla ADD COLUMN balance_above INTEGER")
                con.commit()
                cur.execute("UPDATE tesla SET balance_above = 50")
                con.commit()

        result = cur.execute("PRAGMA table_info(stats)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table stats")
            cur.execute("CREATE TABLE stats(tstamp INTEGER, current_production INTEGER, current_consumption INTEGER, tesla_consumption INTEGER)")
            con.commit()
        else:
            results = cur.execute("PRAGMA table_info(stats)").fetchall()
            for result in results:
                if (result[1] == 'current_surplus'):
                    cur.execute("ALTER TABLE stats RENAME COLUMN current_surplus TO current_consumption")
            if len(results) == 4:
                cur.execute("ALTER TABLE stats ADD COLUMN cost_price REAL")
                cur.execute("ALTER TABLE stats ADD COLUMN profit_price REAL")
                cur.execute("ALTER TABLE stats ADD COLUMN cost REAL")
                cur.execute("ALTER TABLE stats ADD COLUMN profit REAL")
                cur.execute("ALTER TABLE stats ADD COLUMN tesla_cost REAL")
            con.commit()


        result = cur.execute("PRAGMA table_info(event)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table event")
            cur.execute("CREATE TABLE event(log_date, levelname, source, message, occurrences)")
            con.commit()


        result = cur.execute("PRAGMA index_info(last_event)").fetchone()
        if (result == None):
            self.logger.debug ("Creating index last_event")
            cur.execute("create index last_event on event (log_date);")
            con.commit()

        result = cur.execute("PRAGMA table_info(prices)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table prices")
            cur.execute("CREATE TABLE prices(tstamp INTEGER, price REAL)")
            con.commit()

        con.close()


    def get_db_connection(self):
        conn = sqlite3.connect(persistence.DBNAME, timeout=60)
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
        con.close()
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


    #  consumer consumption_max
    def get_consumer_consumption_max(self, consumer_name):
        con = self.get_db_connection()
        result = con.execute("SELECT consumption_max FROM consumer WHERE name = :consumer_name",{"consumer_name":consumer_name}).fetchone()
        con.close()
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
        con.close()
        if result == None:
            return 0
        return int(result[0])
    def set_consumer_consumption_now(self, consumer_name, value):
        con = self.get_db_connection()
        result = con.execute("UPDATE consumer SET consumption_now = :value WHERE name = :consumer_name",{"value":value, "consumer_name":consumer_name})
        con.commit()
        con.close()

    # consumer balance_above
    def get_tesla_balance_above(self):
        con = self.get_db_connection()
        result = con.execute("SELECT balance_above FROM tesla").fetchone()
        con.close()
        return int(result[0])
    def set_tesla_balance_above(self, value):
        con = self.get_db_connection()
        result = con.execute("UPDATE tesla SET balance_above = :value",{"value":value})
        con.commit()
        con.close()

    # consumer charge_until
    def get_tesla_charge_until(self):
        con = self.get_db_connection()
        result = con.execute("SELECT charge_until FROM tesla").fetchone()
        con.close()
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
        con.close()
        return int(result[0])
    def set_consumer_balance(self, consumer_name, value):
        con = self.get_db_connection()  
        result = con.execute("UPDATE consumer SET balance = :value WHERE name = :consumer_name",{"value":value, "consumer_name":consumer_name})
        if (result == None):
            print("update of consumer setting successful")
        else:
            print("update of consumer setting failed")
        con.commit()
        con.close()



    #  log retention
    def get_log_retention(self):
        con = self.get_db_connection()
        result = con.execute("SELECT log_retention_days FROM settings").fetchone()
        con.close()
        return int(result[0])
    def set_log_retention(self, value):
        con = self.get_db_connection()  
        result = con.execute("UPDATE settings SET log_retention_days = :value ",{"value":value})
        con.commit()
        con.close()


    #  stats retention
    def get_stats_retention(self):
        con = self.get_db_connection()
        result = con.execute("SELECT stats_retention_days FROM settings").fetchone()
        con.close()
        return int(result[0])

    def set_stats_retention(self, value):
        con = self.get_db_connection()  
        result = con.execute("UPDATE settings SET stats_retention_days = :value ",{"value":value})
        con.commit()
        con.close()


    def get_log_lines(self):
        con = self.get_db_connection()
        result = con.execute("SELECT * FROM event ORDER BY log_date DESC").fetchall()
        con.close()
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
        con.close()
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
        con.close()
        return (result[0],result[1])

    def set_tesla_current_coords(self, current_latitude, current_longitude):
        con = self.get_db_connection()
        result = con.execute("UPDATE tesla SET current_latitude = :current_latitude, current_longitude = :current_longitude",{"current_latitude":current_latitude,"current_longitude":current_longitude})
        con.commit()
        con.close()

    def write_statistics(self, when, current_production, current_consumption, tesla_consumption, cost_price, profit_price, cost, profit, tesla_cost ):
        con = self.get_db_connection()
        tstamp = time.mktime(when.timetuple())
        result = con.execute("INSERT INTO stats VALUES (:tstamp, :current_production, :current_consumption, :tesla_consumption, :cost_price, :profit_price, :cost, :profit, :tesla_cost)",
                                                       {"tstamp"             : tstamp, 
                                                        "current_production" : current_production, 
                                                        "current_consumption": current_consumption, 
                                                        "tesla_consumption"  : tesla_consumption,
                                                        "cost_price"         : cost_price, 
                                                        "profit_price"       : profit_price, 
                                                        "cost"               : cost, 
                                                        "profit"             : profit, 
                                                        "tesla_cost"         : tesla_cost
                                                        })
        con.commit()
         
        stats_retention_days = self.get_stats_retention()
        dt = datetime.now() - timedelta(days=stats_retention_days)
        unix_ts = time.mktime(dt.timetuple())
        result = con.execute("DELETE FROM stats WHERE tstamp < :tstamp",{"tstamp":unix_ts})
        con.commit()
        con.close()

    def write_prices(self, when: datetime, price: float):
        con = self.get_db_connection()
        unix_ts = time.mktime(when.timetuple())
        result = con.execute("INSERT INTO prices VALUES (:tstamp, :price)",
                                                       {"tstamp" : unix_ts, 
                                                        "price"  : price})
        con.commit()
        con.close()

    def get_price_at_datetime(self, when: date):
        con = self.get_db_connection()
        try:
            unix_ts = time.mktime(when.timetuple())
            result = con.execute("SELECT price FROM prices WHERE tstamp = (SELECT MAX(tstamp) FROM prices WHERE tstamp <= :tstamp)",{"tstamp":unix_ts}).fetchone()
            con.close()
            if result:
                result = result[0]
            return result
        except Exception as e:
            self.logger.exception(e)
            return None

    def get_historical_prices(self, minutes):
        con = self.get_db_connection()
        dt = datetime.now() - timedelta(minutes=minutes)
        unix_ts = time.mktime(dt.timetuple())
        result = con.execute("SELECT * FROM prices WHERE tstamp >= :tstamp ORDER BY tstamp",{"tstamp":unix_ts}).fetchall()
        con.close()
        return result

    def get_day_prices(self, from_dt:datetime):
        con = self.get_db_connection()
        today = datetime(from_dt.year,from_dt.month,from_dt.day,0,0,0)
        from_ts = time.mktime(today.timetuple())
        until_dt = today + timedelta(hours=23)
        until_ts = time.mktime(until_dt.timetuple())
        
        result = con.execute("SELECT * FROM prices WHERE tstamp between :from_tstamp and :to_tstamp ORDER BY tstamp",
                    {"from_tstamp":from_ts,
                     "to_tstamp"  :until_ts}).fetchall()
        con.close()
        return result


    def get_history(self, minutes):
        con = self.get_db_connection()
        dt = datetime.now() - timedelta(minutes=minutes)
        unix_ts = time.mktime(dt.timetuple())
        result = con.execute("SELECT * FROM stats WHERE tstamp > :tstamp ORDER BY tstamp",{"tstamp":unix_ts}).fetchall()
        con.close()
        return result

    def get_summarized_euro_history_from_to(self, from_datetime:datetime, to_datetime:datetime):
        from_ts = time.mktime(from_datetime.timetuple())
        until_ts = time.mktime(to_datetime.timetuple())
        
        con = self.get_db_connection()
        result = con.execute("SELECT sum(cost), sum(profit), sum(tesla_cost) FROM stats WHERE tstamp between :from_tstamp and :until_tstamp",
                    {"from_tstamp"  :from_ts,
                     "until_tstamp" :until_ts}).fetchall()
        con.close()
        return result

