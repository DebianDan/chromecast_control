# Chromecast Control with TV Remote

This outlines the research and development to use a TV remote to control a chromecast.

## IR Setup

`sudo nano /boot/config.txt`
	
uncomment the following line: `#dtoverlay=gpio-ir,gpio_pin=14`

`sudo apt-get install ir-keytable`

`sudo ir-keytable -p nec -t`

## IR Testing

Testing the TV remote buttons in order A,B,C,D

	pi@raspi01:/lib/udev/rc_keymaps $ sudo ir-keytable -t
	Testing events. Please, press CTRL-C to abort.
	549.890038: lirc protocol(necx): scancode = 0x7076c
	549.890068: event type EV_MSC(0x04): scancode = 0x7076c
	549.890068: event type EV_SYN(0x00).
	551.100035: lirc protocol(necx): scancode = 0x70714
	551.100065: event type EV_MSC(0x04): scancode = 0x70714
	551.100065: event type EV_SYN(0x00).
	552.180038: lirc protocol(necx): scancode = 0x70715
	552.180063: event type EV_MSC(0x04): scancode = 0x70715
	552.180063: event type EV_SYN(0x00).
	553.280035: lirc protocol(necx): scancode = 0x70716
	553.280060: event type EV_MSC(0x04): scancode = 0x70716
	553.280060: event type EV_SYN(0x00).


## Create Key Mapping

sudo nano /etc/rc_keymaps/samsung_bn59

	# table samsung_bn59, type: NEC
	0x7076c	KEY_A
	0x70714 KEY_B
	0x70715 KEY_C
	0x70716	KEY_D

sudo nano /etc/rc.local
	Add the following line: sudo /usr/bin/ir-keytable -p nec -c -w /etc/rc_keymaps/samsung_bn59

## Capture IR Events in Python

pip install evdev

Follow [this tutorial on evdev](https://python-evdev.readthedocs.io/en/latest/usage.html#reading-events-from-a-device).
	