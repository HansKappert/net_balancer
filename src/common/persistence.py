import sqlite3
import logging
import time
from pytz                             import timezone
from datetime                         import date, datetime, timedelta
from common.database_logging_handler  import database_logging_handler


class persistence:
    DBNAME = 'energy_mediator.db'

    stats_collect_qry = """
    SELECT :year, :month, :day, :hour, 
            round((max(meter_reading_delivered_by_client_low   ) - min(meter_reading_delivered_by_client_low   )) +
                  (max(meter_reading_delivered_by_client_normal) - min(meter_reading_delivered_by_client_normal))
                  ,3) as current_production,
            round((max(meter_reading_delivered_to_client_low   ) - min(meter_reading_delivered_to_client_low   )) +
                  (max(meter_reading_delivered_to_client_normal) - min(meter_reading_delivered_to_client_normal))
                  ,3) as current_consumption,        
            round(sum(tesla_consumption)/1000.0/360.0, 6) as tesla_consumption, 
            round(avg(cost_price)  ,2) as cost_price, 
            round(avg(profit_price),2) as profit_price, 
            round(avg(cost_price) * (
                                (max(meter_reading_delivered_to_client_low   ) - min(meter_reading_delivered_to_client_low   )) +
                                (max(meter_reading_delivered_to_client_normal) - min(meter_reading_delivered_to_client_normal))
                              )
                    ,2) as cost, 
            round(avg(cost_price) * (
                                (max(meter_reading_delivered_by_client_low   ) - min(meter_reading_delivered_by_client_low   )) +
                                (max(meter_reading_delivered_by_client_normal) - min(meter_reading_delivered_by_client_normal))
                              )
                    ,2) as profit, 
            round(sum(tesla_cost)  ,2) as tesla_cost, 
            round(max(gas_reading) - min(gas_reading),6)  as gas_consumption
        FROM stats 
        WHERE meter_reading_delivered_by_client_low    > 0 
        AND   meter_reading_delivered_by_client_normal > 0 
        AND   meter_reading_delivered_to_client_low    > 0 
        AND   meter_reading_delivered_to_client_normal > 0 
        AND   gas_reading > 0
        AND tstamp between :from_tstamp and :until_tstamp"""

    def __init__(self) -> None:
        db_con = self.get_db_connection()
        cur = db_con.cursor()

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
        if (len(result) == 0):
            self.logger.debug ("Creating table settings")
            cur.execute("CREATE TABLE settings (log_retention_days INTEGER, stats_retention_days INTEGER);")
            cur.execute("INSERT INTO  settings VALUES (40,40)")
            db_con.commit()
        else:
            for field in result:
                if field[1] == "surplus_delay_theshold":
                    cur.execute("DROP TABLE settings")
                    cur.execute("CREATE TABLE settings (log_retention_days INTEGER, stats_retention_days INTEGER);")
                    cur.execute("INSERT INTO  settings VALUES (40,40)")
                    db_con.commit()
                    
    
        result = cur.execute("PRAGMA table_info(readings)").fetchall()
        if len(result) != 18:
            self.logger.debug ("Re-Creating table readings")
            cur.execute("DROP TABLE IF EXISTS  readings")
            cur.execute("""CREATE TABLE readings(
                surplus INTEGER, 
                current_consumption INTEGER, 
                current_production INTEGER, 
                current_gas_reading REAL, 
                meter_reading_delivered_by_client_low REAL, 
                meter_reading_delivered_by_client_normal REAL, 
                meter_reading_delivered_to_client_low REAL, 
                meter_reading_delivered_to_client_normal REAL)""") 
            cur.execute("INSERT INTO  readings VALUES (0,0,0,0,0,0,0,0)")
            db_con.commit()

        result = cur.execute("PRAGMA table_info(consumer)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table consumer")
            cur.execute("CREATE TABLE consumer(name TEXT, consumption_max INTEGER, consumption_now INTEGER, balance BOOLEAN NOT NULL CHECK (balance IN (0, 1)), disabled BOOLEAN NOT NULL CHECK (disabled IN (0, 1)))")
            cur.execute("INSERT INTO  consumer VALUES ('Tesla', 3680, 0, 1, 0)")
            db_con.commit()
        else:
            result = cur.execute("PRAGMA table_info(consumer)").fetchall()
            if (result[3][1] == 'override'):
                cur.execute("ALTER TABLE consumer RENAME COLUMN override TO balance")
                db_con.commit()

        result = cur.execute("PRAGMA table_info(tesla)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table tesla")
            cur.execute("CREATE TABLE tesla(charge_until INTEGER, home_latitude REAL, home_longitude REAL, current_latitude REAL, current_longitude REAL, balance_above INTEGER, price_percentage INTEGER, status TEXT)")
            cur.execute("INSERT INTO  tesla VALUES (80, 0.0, 0.0, 0.0, 0.0, 30, 80, '')")
            db_con.commit()
        else:
            result = cur.execute("PRAGMA table_info(tesla)").fetchall()
            if (len(result) == 5):
                cur.execute("ALTER TABLE tesla ADD COLUMN balance_above INTEGER")
                db_con.commit()
                cur.execute("UPDATE tesla SET balance_above = 50")
                db_con.commit()
            result = cur.execute("PRAGMA table_info(tesla)").fetchall()
            if (len(result) == 6):
                cur.execute("ALTER TABLE tesla ADD COLUMN price_percentage INTEGER")
                db_con.commit()
                cur.execute("UPDATE tesla SET price_percentage = 50")
                db_con.commit()
            if (len(result) == 7):
                cur.execute("ALTER TABLE tesla ADD COLUMN status TEXT")
                db_con.commit()

        result = cur.execute("PRAGMA table_info(stats)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table stats")
            cur.execute("CREATE TABLE stats(tstamp INTEGER, current_production INTEGER, current_consumption INTEGER, tesla_consumption INTEGER, cost_price REAL, profit_price REAL, cost REAL, profit REAL, tesla_cost REAL, gas_reading REAL, meter_reading_delivered_to_client_low REAL, meter_reading_delivered_to_client_normal REAL, meter_reading_delivered_by_client_low REAL, meter_reading_delivered_by_client_normal REAL)")
            db_con.commit()
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
            if len(results) == 9:
                cur.execute("ALTER TABLE stats ADD COLUMN gas_reading REAL")
            if len(results) == 10:
                self.logger.debug ("Adding column gas_consumption") 
                cur.execute("ALTER TABLE stats ADD COLUMN meter_reading_delivered_to_client_low    REAL")
                cur.execute("ALTER TABLE stats ADD COLUMN meter_reading_delivered_to_client_normal REAL")
                cur.execute("ALTER TABLE stats ADD COLUMN meter_reading_delivered_by_client_low    REAL")
                cur.execute("ALTER TABLE stats ADD COLUMN meter_reading_delivered_by_client_normal REAL")
            db_con.commit()

        result = cur.execute("PRAGMA table_info(cum_stats)").fetchall()
        # for f in result:
        #    print(f'{f[0]} {f[1]}')
        if len(result) == 0:
            self.logger.debug ("Creating table cum_stats")
            cur.execute("CREATE TABLE cum_stats(year INTEGER, month INTEGER, day INTEGER, hour INTEGER, current_production INTEGER, current_consumption INTEGER, tesla_consumption INTEGER, cost_price REAL, profit_price REAL, cost REAL, profit REAL, tesla_cost REAL, gas_consumption REAL)")
            db_con.commit()
        if len(result) == 12:
            self.logger.debug ("Adding column gas_consumption") 
            cur.execute("ALTER TABLE cum_stats ADD COLUMN gas_consumption REAL")
            db_con.commit()
        

        result = cur.execute("PRAGMA table_info(event)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table event")
            cur.execute("CREATE TABLE event(log_date, levelname, source, message, occurrences)")
            db_con.commit()


        result = cur.execute("PRAGMA index_info(last_event)").fetchone()
        if (result == None):
            self.logger.debug ("Creating index last_event")
            cur.execute("create index last_event on event (log_date);")
            db_con.commit()

        result = cur.execute("PRAGMA table_info(prices)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table prices")
            cur.execute("CREATE TABLE prices(tstamp INTEGER, price REAL)")
            db_con.commit()

        result = cur.execute("PRAGMA table_info(mediation_service)").fetchone()
        if (result == None):
            self.logger.debug ("Creating table mediation_service")
            cur.execute("CREATE TABLE mediation_service(status TEXT)")
            cur.execute("INSERT INTO mediation_service VALUES('')")
            db_con.commit()
        
        cur.execute("update cum_stats set current_consumption = -1 * current_consumption where current_consumption < 0")
        cur.execute("update     stats set current_consumption = -1 * current_consumption where current_consumption < 0")
        db_con.commit()

        db_con.close()

    def vacuum(self):
        db_con = self.get_db_connection()
        db_con.execute("VACUUM")
        db_con.commit()        
        db_con.close()

    def get_db_connection(self):
        conn = sqlite3.connect(persistence.DBNAME, timeout=60)
        conn.row_factory = sqlite3.Row
        return conn

    def log_event(self, levelname:str, source:str, message:str):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT log_date, message FROM event ORDER BY log_date DESC").fetchone()
        log_date = datetime.now()
        if not result == None and result[1] == message:
                result = db_con.execute("UPDATE event SET log_date = :new_log_date, occurrences = occurrences + 1 WHERE log_date = :old_log_date",{"new_log_date": log_date, "old_log_date": result[0]})
        else:
            result = db_con.execute("INSERT INTO event VALUES (:log_date, :levelname, :source, :message, 1)",{"log_date": log_date, "levelname":levelname, "source":source, "message":message})
        db_con.commit()
        db_con.close()

    def __get_reading_column_value(self, column_name):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT " + column_name + " FROM readings").fetchone()
        db_con.close()
        return result[0]
    
    def __set_reading_column_value(self, column_name, value):
        db_con = self.get_db_connection()
        result = db_con.execute("UPDATE readings SET " + column_name + " = :value",{"value":value})
        db_con.commit()
        db_con.close()
    
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

    def get_current_gas_reading(self):
        return self.__get_reading_column_value("current_gas_reading")
    def set_current_gas_reading(self,value):
        self.__set_reading_column_value("current_gas_reading", value)

    def get_meter_reading_delivered_by_client_low(self):
        return self.__get_reading_column_value("meter_reading_delivered_by_client_low")
    def set_meter_reading_delivered_by_client_low(self,value):
        self.__set_reading_column_value("meter_reading_delivered_by_client_low", value)

    def get_meter_reading_delivered_by_client_normal(self):
        return self.__get_reading_column_value("meter_reading_delivered_by_client_normal")
    def set_meter_reading_delivered_by_client_normal(self,value):
        self.__set_reading_column_value("meter_reading_delivered_by_client_normal", value)

    def get_meter_reading_delivered_to_client_low(self):
        return self.__get_reading_column_value("meter_reading_delivered_to_client_low")
    def set_meter_reading_delivered_to_client_low(self,value):
        self.__set_reading_column_value("meter_reading_delivered_to_client_low", value)

    def get_meter_reading_delivered_to_client_normal(self):
        return self.__get_reading_column_value("meter_reading_delivered_to_client_normal")
    def set_meter_reading_delivered_to_client_normal(self,value):
        self.__set_reading_column_value("meter_reading_delivered_to_client_normal", value)


   

    #  mediation service status
    def get_mediation_service_status(self):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT status FROM mediation_service").fetchone()
        db_con.close()
        return result[0]
    def set_mediation_service_status(self, value):
        db_con = self.get_db_connection()
        result = db_con.execute("UPDATE mediation_service SET status = :value",{"value":value})
        db_con.commit()
        db_con.close()




    #  consumer consumption_max
    def get_consumer_consumption_max(self, consumer_name):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT consumption_max FROM consumer WHERE name = :consumer_name",{"consumer_name":consumer_name}).fetchone()
        db_con.close()
        if result == None:
            return 0
        return int(result[0])
    def set_consumer_consumption_max(self, consumer_name, value):
        db_con = self.get_db_connection()
        result = db_con.execute("UPDATE consumer SET consumption_max = :value WHERE name = :consumer_name",{"value":value, "consumer_name":consumer_name})
        db_con.commit()
        db_con.close()

    # consumer consumption_now
    def get_consumer_consumption_now(self, consumer_name):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT consumption_now FROM consumer WHERE name = :consumer_name",{"consumer_name":consumer_name}).fetchone()
        db_con.close()
        if result == None:
            return 0
        return int(result[0])
    def set_consumer_consumption_now(self, consumer_name, value):
        db_con = self.get_db_connection()
        result = db_con.execute("UPDATE consumer SET consumption_now = :value WHERE name = :consumer_name",{"value":value, "consumer_name":consumer_name})
        db_con.commit()
        db_con.close()

    # consumer balance_above
    def get_tesla_balance_above(self):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT balance_above FROM tesla").fetchone()
        db_con.close()
        if result:
            return int(result[0])
        else:
            return 0
    def set_tesla_balance_above(self, value):
        db_con = self.get_db_connection()
        result = db_con.execute("UPDATE tesla SET balance_above = :value",{"value":value})
        db_con.commit()
        db_con.close()

    # consumer price_percentage
    def get_tesla_price_percentage(self):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT price_percentage FROM tesla").fetchone()
        db_con.close()
        if result:
            return int(result[0])
        else:
            return 0
        
    def set_tesla_price_percentage(self, value):
        db_con = self.get_db_connection()
        result = db_con.execute("UPDATE tesla SET price_percentage = :value",{"value":value})
        db_con.commit()
        db_con.close()

    # consumer charge_until
    def get_tesla_charge_until(self):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT charge_until FROM tesla").fetchone()
        db_con.close()
        if result:
            return int(result[0])
        else:
            return 0
        
    def set_tesla_charge_until(self, value):
        db_con = self.get_db_connection()
        result = db_con.execute("UPDATE tesla SET charge_until = :value",{"value":value})
        db_con.commit()
        db_con.close()

    #  consumer balance
    def get_consumer_balance(self, consumer_name):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT balance FROM consumer WHERE name = :consumer_name",{"consumer_name":consumer_name}).fetchone()
        db_con.close()
        if result:
            return int(result[0])
        else:
            return 0
    def set_consumer_balance(self, consumer_name, value):
        db_con = self.get_db_connection()  
        result = db_con.execute("UPDATE consumer SET balance = :value WHERE name = :consumer_name",{"value":value, "consumer_name":consumer_name})
        if (result == None):
            print("update of consumer setting successful")
        else:
            print("update of consumer setting failed")
        db_con.commit()
        db_con.close()

    #  consumer balance
    def get_consumer_status(self, consumer_name):
        db_con = self.get_db_connection()
        if consumer_name == 'Tesla':
            result = db_con.execute("SELECT status FROM tesla").fetchone()
            db_con.close()
            return result[0]
        else:
            return ''
    def set_consumer_status(self, consumer_name, value):
        db_con = self.get_db_connection() 
        if consumer_name == 'Tesla':
            db_con.execute("UPDATE tesla SET status = :value",{"value":value})
        db_con.commit()
        db_con.close()
        

    #  log retention
    def get_log_retention(self):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT log_retention_days FROM settings").fetchone()
        db_con.close()
        if result:
            return int(result[0])
        else:
            return 0
    def set_log_retention(self, value):
        db_con = self.get_db_connection()  
        result = db_con.execute("UPDATE settings SET log_retention_days = :value ",{"value":value})
        db_con.commit()
        db_con.close()

    #  stats retention
    def get_stats_retention(self):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT stats_retention_days FROM settings").fetchone()
        db_con.close()
        return int(result[0])

    def set_stats_retention(self, value):
        db_con = self.get_db_connection()  
        result = db_con.execute("UPDATE settings SET stats_retention_days = :value ",{"value":value})
        db_con.commit()
        db_con.close()

    def get_log_lines(self):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT * FROM event ORDER BY log_date DESC").fetchall()
        db_con.close()
        return result

    def remove_old_log_lines(self):
        db_con = self.get_db_connection()
        result = db_con.execute("select log_retention_days from settings").fetchone()
        log_retention_hours = int(result[0])
        result = db_con.execute("DELETE FROM event WHERE log_date < datetime('now', '-{} hours')".format(log_retention_hours))
        db_con.commit()
        db_con.close()
        return result

    # tesla home_coords
    def get_tesla_home_coords(self):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT home_latitude, home_longitude FROM tesla").fetchone()
        db_con.close()
        if result:
            return (result[0],result[1])
        else:
            self.logger.debug("No home location set.")
            return (0,0)

    def set_tesla_home_coords(self, home_latitude, home_longitude):
        db_con = self.get_db_connection()
        result = db_con.execute("UPDATE tesla SET home_latitude = :home_latitude, home_longitude = :home_longitude",{"home_latitude":home_latitude,"home_longitude":home_longitude})
        db_con.commit()
        db_con.close()

    # tesla current_coords
    def get_tesla_current_coords(self):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT current_latitude, current_longitude FROM tesla").fetchone()
        db_con.close()
        if result:
            return (result[0],result[1])
        else:
            self.logger.debug("Current location unknown.")
            return (0,0)

    def set_tesla_current_coords(self, current_latitude, current_longitude):
        db_con = self.get_db_connection()
        result = db_con.execute("UPDATE tesla SET current_latitude = :current_latitude, current_longitude = :current_longitude",{"current_latitude":current_latitude,"current_longitude":current_longitude})
        db_con.commit()
        db_con.close()

    def write_statistics(self, 
                        when, 
                        current_production, 
                        current_consumption, 
                        tesla_consumption, 
                        price, 
                        tesla_cost, 
                        gas_reading = 0,
                        meter_reading_delivered_to_client_low    = 0,
                        meter_reading_delivered_to_client_normal = 0,
                        meter_reading_delivered_by_client_low    = 0,
                        meter_reading_delivered_by_client_normal = 0
                        ):
        db_con = self.get_db_connection()
        tstamp = time.mktime(when.timetuple())
        result = db_con.execute("""
        INSERT INTO stats 
        (        
            tstamp, 
            current_production, 
            current_consumption, 
            tesla_consumption, 
            cost_price, 
            profit_price,            
            tesla_cost, 
            gas_reading, 
            meter_reading_delivered_to_client_low, 
            meter_reading_delivered_to_client_normal, 
            meter_reading_delivered_by_client_low, 
            meter_reading_delivered_by_client_normal
        )
        VALUES (
            :tstamp, 
            :current_production, 
            :current_consumption, 
            :tesla_consumption, 
            :cost_price, 
            :profit_price,  
            :tesla_cost, 
            :gas_reading,
            :meter_reading_delivered_to_client_low,
            :meter_reading_delivered_to_client_normal,
            :meter_reading_delivered_by_client_low,
            :meter_reading_delivered_by_client_normal
        )""",
            {"tstamp"            : tstamp, 
            "current_production" : current_production, 
            "current_consumption": current_consumption, 
            "tesla_consumption"  : tesla_consumption,
            "cost_price"         : price, 
            "profit_price"       : price, 
            "tesla_cost"         : tesla_cost,
            "gas_reading"        : gas_reading,
            "meter_reading_delivered_to_client_low"    : meter_reading_delivered_to_client_low,
            "meter_reading_delivered_to_client_normal" : meter_reading_delivered_to_client_normal,
            "meter_reading_delivered_by_client_low"    : meter_reading_delivered_by_client_normal,
            "meter_reading_delivered_by_client_normal" : meter_reading_delivered_by_client_low
            })
        db_con.commit()
         
        stats_retention_days = self.get_stats_retention()
        dt = datetime.now() - timedelta(days=stats_retention_days)
        unix_ts = time.mktime(dt.timetuple())
        result = db_con.execute("DELETE FROM stats WHERE tstamp < :tstamp",{"tstamp":unix_ts})
        db_con.commit()
        db_con.close()

    def write_prices(self, when: datetime, price: float):
        db_con = self.get_db_connection()
        unix_ts = time.mktime(when.timetuple())
        result = db_con.execute("INSERT INTO prices VALUES (:tstamp, :price)",
                                                       {"tstamp" : unix_ts, 
                                                        "price"  : price})
        db_con.commit()
        db_con.close()

    def get_price_at_datetime(self, when: date):
        db_con = self.get_db_connection()
        try:
            unix_ts = time.mktime(when.timetuple())
            result = db_con.execute("SELECT price FROM prices WHERE tstamp = (SELECT MAX(tstamp) FROM prices WHERE tstamp <= :tstamp)",{"tstamp":unix_ts}).fetchone()
            db_con.close()
            if result:
                return result[0]
            return None
        except Exception as e:
            self.logger.exception(e)
            return None

    def get_historical_prices(self, minutes):
        db_con = self.get_db_connection()
        dt = datetime.now() - timedelta(minutes=minutes)
        unix_ts = time.mktime(dt.timetuple())
        result = db_con.execute("SELECT * FROM prices WHERE tstamp >= :tstamp ORDER BY tstamp",{"tstamp":unix_ts}).fetchall()
        db_con.close()
        return result

    def get_day_prices(self, from_dt:datetime):
        db_con = self.get_db_connection()
        today = datetime(from_dt.year,from_dt.month,from_dt.day,0,0,0)
        from_ts = time.mktime(today.timetuple())
        until_dt = today + timedelta(hours=23)
        until_ts = time.mktime(until_dt.timetuple())
        
        result = db_con.execute("SELECT * FROM prices WHERE tstamp between :from_tstamp and :to_tstamp ORDER BY tstamp",
                    {"from_tstamp":from_ts,
                     "to_tstamp"  :until_ts}).fetchall()
        db_con.close()
        return result

    def get_history(self, minutes):
        db_con = self.get_db_connection()
        dt = datetime.now() - timedelta(minutes=minutes)
        unix_ts = time.mktime(dt.timetuple())
        result = db_con.execute("SELECT * FROM stats WHERE tstamp > :tstamp ORDER BY tstamp",{"tstamp":unix_ts}).fetchall()
        db_con.close()
        return result

    def get_stats_for_date_hour(self, date_hour:datetime):

        # datehour contains a local time, but no timezone info. 
        # we must add the CET timezone info in order to do correct conversion to the timestamps
        amsterdam = timezone('Europe/Amsterdam')
        date_hour = date_hour.astimezone(amsterdam)
        from_ts = time.mktime(date_hour.timetuple())
        until_ts = time.mktime(datetime.now().timetuple())
        
        db_con = self.get_db_connection()
        result = db_con.execute(self.stats_collect_qry
                ,
                    {"year"        : date_hour.year,
                    "month"        : date_hour.month,
                    "day"          : date_hour.day,
                    "hour"         : date_hour.hour,
                    "from_tstamp"  : from_ts,
                    "until_tstamp" : until_ts}).fetchall()
        
        db_con.close()
        return result
    def get_cum_stats_for_date_hour(self, date_hour:datetime):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT * FROM cum_stats WHERE year = :year AND month = :month AND day = :day AND hour = :hour",
                    {"year":date_hour.year,
                    "month":date_hour.month,
                    "day":date_hour.day,
                    "hour":date_hour.hour}).fetchall()
        db_con.close()
        return result

    def get_cum_stats_for_month(self, year: int, month: int):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT year, month, day, SUM(current_production), SUM(current_consumption), SUM(tesla_consumption), AVG(cost_price), AVG(profit_price), SUM(cost), SUM(profit), SUM(tesla_cost), SUM(gas_consumption) FROM cum_stats WHERE year = :year AND month = :month AND day = :day GROUP BY year, month, day ORDER BY year, month, day",
                    {"year":year,
                    "month":month}).fetchall()
        db_con.close()
        return result

    def get_cum_stats_for_year(self, year: int):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT year, month, day, SUM(current_production), SUM(current_consumption), SUM(tesla_consumption), AVG(cost_price), AVG(profit_price), SUM(cost), SUM(profit), SUM(tesla_cost), SUM(gas_consumption) FROM cum_stats WHERE year = :year AND month = :month AND day = :day GROUP BY year, month ORDER BY year, month",
                    {"year":date.year}).fetchall()
        db_con.close()
        return result

    def get_cum_stats(self):
        db_con = self.get_db_connection()
        result = db_con.execute("SELECT * FROM cum_stats ORDER BY year, month, day, hour").fetchall()
        db_con.close()
        return result

    
    def accumulate_date_hour(self, date_hour:datetime):
        from_ts = time.mktime(date_hour.timetuple())
        until_dt = date_hour + timedelta(hours=1)
        until_ts = time.mktime(until_dt.timetuple())
        
        db_con = self.get_db_connection()
        result = db_con.execute("""INSERT INTO cum_stats
                 (year,  month,  day,  hour,           
                 current_production,                            
                 current_consumption,                            
                 tesla_consumption,                            
                 cost_price,               
                 profit_price,               
                 cost,               
                 profit,               
                 tesla_cost    , 
                 gas_consumption) """ + self.stats_collect_qry
                ,
                    {"year"        : date_hour.year,
                    "month"        : date_hour.month,
                    "day"          : date_hour.day,
                    "hour"         : date_hour.hour,
                    "from_tstamp"  : from_ts,
                    "until_tstamp" : until_ts})
        db_con.commit()
        db_con.close()
        return result

