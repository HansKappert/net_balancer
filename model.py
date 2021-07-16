
class model:
    # the last calculated value.
    surplus = 0

    # if there is enough surplus energy, we increase the surplus_delay_count
    # # when that value exceeds the threshold, we switch on the consumer, and
    # set the counter to 0. Similar rules apply to the deficient_delay.
    # These rules will prevent the consumers from switching on and off too often  
    surplus_delay_count = 0
    surplus_delay_theshold = 20

    deficient_delay_count = 0
    deficient_delay_theshold = 20

