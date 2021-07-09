# slimmemeter-rpi
zie ook

http://gejanssen.com/howto/Slimme-meter-uitlezen/index.html
en
http://gejanssen.com/howto/rpi-rrd-power/index.html

## Installeer software

```
./packages.sh
```

Installeren van
* cu
* Python-serial

Zet de rechten van de seriele poort open. (pi is de user die toegevoegd wordt aan de dialout group)

```
gej@rpi-backup:~/slimmemeter-rpi $ sudo usermod -a -G dialout www-data pi
```

