import RPi.GPIO as GPIO
import pychromecast
import argparse
import logging
import time
import os

#IDLE_APP_ID = 'E8C28D3C'

def main_control(chromecast_name, chromecast_ip=None, rewind_padding=10, pause_delay=0):	

	start_time = time.time()	
	cast = None
	
	# Direct connect by IP (preferred) ~1 second
	if chromecast_ip:
		logging.info("Looking up Chromecast by IP: " + chromecast_ip)
		ping_result = os.system("ping -c 1 -w 2 " + chromecast_ip + " > /dev/null 2>&1")	
		if ping_result == 0:
			logging.info("Successful ping, trying direct connect now")
			try:
				cast = pychromecast.Chromecast(chromecast_ip)
			except Exception as e:
				logging.error("Exception encountered while directly connecting: " + str(e), exc_info=True)
		else:
			raise logging.warning("Unsuccessful ping, skipping direct connect")

	# Search via zeroconf (fallback) ~10 seconds
	if not cast or cast.device.friendly_name != chromecast_name:
		logging.info("Discovering all chromecasts instead, fallback for direct connect")
		chromecasts = pychromecast.get_chromecasts()
		if chromecasts:
			cast = next(cc for cc in chromecasts if cc.device.friendly_name == chromecast_name)
	
	# Main pause, rewind, play functionality
	if cast and cast.device:
		cast.wait()
		mc = cast.media_controller
		mc.block_until_active()
		casted_app = cast.status.display_name.lower()
		#check if something is playing
		#if cast.status is None or cast.app_id in (None, IDLE_APP_ID):
		if mc.status.player_is_playing:
			mc.pause()
			pause_delay = int(time.time() - start_time)
			logging.info("Paused " + chromecast_name + ", delay was " + str(pause_delay) + " seconds")
			return pause_delay
		elif mc.status.player_is_paused:
			if casted_app in ('netflix','hulu','hbo go') and mc.status.supports_seek:
				rewind_time = pause_delay + REWIND_PADDING if pause_delay else REWIND_PADDING
				mc.seek(max(0, mc.status.current_time - rewind_time))
				logging.info("Rewinded " + chromecast_name + " " + str(rewind_time) + " seconds")				
			else:
				mc.play()	
				logging.info("Played " + chromecast_name)
		#mc.tear_down()
		cast.disconnect()
	else:
		logging.warning("Could not establish connection with Chromecast")
		blink_for_error()
	# default return
	return 0

def blink_for_error():
	for _ in range(3):
		GPIO.output(22, GPIO.LOW)
		time.sleep(0.3)
		GPIO.output(22, GPIO.HIGH)
		time.sleep(0.3)

def main():
	parser = argparse.ArgumentParser(description='Single physical button application to pause a chromecast then rewind and play')
	parser.add_argument("chromecast_name", help="Name of the Chromecast", metavar="CHROMECAST_NAME")
	parser.add_argument("--chromecast-ip", dest="chromecast_ip", help="IP of the Chromecast for faster lookups (protip: use a DHCP reservation)", metavar="IP")
	parser.add_argument("--rewind-padding", dest="rewind_padding", type=int, default=10, help="Number of seconds to rewind after resuming show", metavar="SECS")
	args = parser.parse_args()

	logging.basicConfig(level=logging.INFO,
		format='%(asctime)s %(levelname)s %(message)s',
		filename='chromecast_control.log')
	
	logging.info("[+] Chromecast controller started")

	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(22, GPIO.OUT, initial=GPIO.LOW)
	GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	pause_delay = 0
	while True:
		try:
			GPIO.wait_for_edge(17, GPIO.FALLING)
			GPIO.output(22, GPIO.HIGH)
			pause_delay = main_control(args.chromecast_name, args.chromecast_ip, args.rewind_padding, pause_delay)
		except KeyboardInterrupt:				
			logging.info("KeyboardInterrupt ended program...")
			break
		except Exception as e:
			logging.error("Encountered exception in main while loop: " + str(e), exc_info=True)
			blink_for_error()
		finally:
			GPIO.output(22, GPIO.LOW)
	GPIO.cleanup()
	logging.info("[-] Chromecast controller finished running")

if __name__ == '__main__':
	main()
