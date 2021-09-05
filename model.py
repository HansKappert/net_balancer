from persistence import persistence
import abc_energy_consumer
class model:
    def __init__(self, db:persistence) -> None:
        self.persistence = db
        self._surplus = 0 # the last calculated value.
        self._override = 0
        # last readings
        self._current_consumption = 0
        self._current_production = 0

        # if there is enough surplus energy, we increase the surplus_delay_count
        # # when that value exceeds the threshold, we switch on the consumer, and
        # set the counter to 0. Similar rules apply to the deficient_delay.
        # These rules will prevent the consumers from switching on and off too often  
        self._surplus_delay_count = 0
        self._surplus_delay_theshold = 0

        self._deficient_delay_count = 0
        self._deficient_delay_theshold = 0
        self._consumers = []
        
    @property
    def surplus(self):
        self._surplus = self.persistence.get_surplus()
        return self._surplus
    @surplus.setter
    def surplus(self,value):
        self._surplus = value
        self.persistence.set_surplus(value)

    @property
    def override(self):
        self._override = self.persistence.get_override()
        return self._override
    @override.setter
    def override(self,value):
        self._override = value
        self.persistence.set_override(value)

    @property
    def current_consumption(self):
        self._current_consumption = self.persistence.get_current_consumption()
        return self._current_consumption
    @current_consumption.setter
    def current_consumption(self,value):
        self._current_consumption = value
        self.persistence.set_current_consumption(value)

    @property
    def current_production(self):
        self._current_production = self.persistence.get_current_production()
        return self._current_production
    @current_production.setter
    def current_production(self,value):
        self._current_production = value
        self.persistence.set_current_production(value)


    @property
    def surplus_delay_count(self):
        self._surplus_delay_count = self.persistence.get_surplus_delay_count()
        return self._surplus_delay_count
    @surplus_delay_count.setter
    def surplus_delay_count(self,value):
        self._surplus_delay_count = value
        self.persistence.set_surplus_delay_count(value)

    @property
    def surplus_delay_theshold(self):
        self._surplus_delay_threshold = self.persistence.get_surplus_delay_theshold()
        return self._surplus_delay_threshold
    @surplus_delay_theshold.setter
    def surplus_delay_theshold(self,value):
        self._surplus_delay_theshold = value
        self.persistence.set_surplus_delay_theshold(value)

    @property
    def deficient_delay_count(self):
        self._deficient_delay_count = self.persistence.get_deficient_delay_count()
        return self._deficient_delay_count
    @deficient_delay_count.setter
    def deficient_delay_count(self,value):
        self._deficient_delay_count = value
        self.persistence.set_deficient_delay_count(value)

    @property
    def deficient_delay_theshold(self):
        self._deficient_delay_theshold = self.persistence.get_deficient_delay_theshold()
        return self._deficient_delay_theshold
    @deficient_delay_theshold.setter
    def deficient_delay_theshold(self,value):
        self._deficient_delay_theshold = value
        self.persistence.set_deficient_delay_theshold(value)

    def add_consumer(self, consumer : abc_energy_consumer):
        self._consumers.append(consumer)
    
