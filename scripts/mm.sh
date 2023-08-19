#!/bin/sh

#########
###pin###
#########
himm 0x112f00ac 0x401 ;  himm 0x112f0020 0x404; himm 0x12090000 0x001001e0

echo 64 > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio64/direction
echo 0 > /sys/class/gpio/gpio64/value


#This is the GPIO for the blue power led, set to output and off, we use it as an indicator in our server app
echo 89 > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio89/direction
echo 0 > /sys/class/gpio/gpio89/value

#########
###net###
#########

#This is the default config from china, since the R8152 eth1, we comment out the config for eth0, ensuring that eth1 is our main ethernet port
#ifconfig eth0 up ;ifconfig eth0 192.168.1.243
#mount -t nfs -o nolock -o tcp 192.168.1.213:/nfs /mnt ;

#Start the telnet daemon
telnetd

#########
###drv###
#########
cd /komod                                                                                                                          
./load3516av300  -i -sensor0 imx307  -sensor1  imx307 
insmod alpu_c_drv.ko
insmod _io.ko


#########
###app###
#########
export HOME='/root';
export LD_LIBRARY_PATH='/usr/local/lib:/usr/lib:/qt_lib:/qt_lib/plugins/imageformats';
export LOGNAME='root';
export OLDPWD='/qt_lib';
export PATH='/usr/bin:/usr/sbin:/bin:/sbin';
export PWD='/opt';export QT_PLUGIN_PATH='/qt_lib/plugins';
export QT_QWS_FONTDIR='/qt_lib/fonts';
export QWS_DISPLAY='LinuxFb:/dev/fb0';
export TERM='vt100';export USER='root';

#This is the main camera app
/opt/camera &
#Comment out the horrible chinese Qt app
#/opt/qt_app -qws -C212 &


#Now that all drivers are loaded and good to go we can configure eth1 that is our usb interface. 
#NOTE hot plugging the usb ethernet adapter, or not having it present at boot looses config and thus access to the camera. TODO implement autoload. 
ifconfig eth1 up ;ifconfig eth1 192.168.1.10

#For some reason, the server app quits, with no error if we start it to early, no idea why. Adding some delay so the system until system is ready
sleep 3
#Start our server, -p set the port it listens to(Default no args is 1234)
#/server -p 420 -d 2>&1 > /debug.txt &
/server -p 420 &
