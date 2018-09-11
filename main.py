import RPi.GPIO as GPIO
import pychromecast
import logging
import time
import os

def main_control(pause_delay=0):	

	start_time = time.time()	
	#IDLE_APP_ID = 'E8C28D3C'
	REWIND_PADDING = 10
	CHROMECAST_NAME = 'Living Room'
	cast = None
	chromecast_ip = None
	
	try:
		with open('.living_room_chromecast_ip', 'r') as f:
			chromecast_ip = f.read().strip()
	except Exception as e:
		logging.warning(str(e))
		pass
	
	if chromecast_ip:
		logging.info("Retrieved saved Living Room Chromecast IP of: " + str(chromecast_ip))
		try:
			ping_result = os.system("ping -c 1 -w2 " + chromecast_ip + " > /dev/null 2>&1")	
			if ping_result == 0:
				logging.info("Successfully pinged " + str(chromecast_ip) + ", attempting direct connect")
				cast = pychromecast.Chromecast(chromecast_ip)
			else:
				raise Exception("Ping unsuccessful, skipping direct connect")
		except Exception as e:
			logging.info("Unable to connect directly: " + str(e))
			pass
		else:
			cast.wait()
	
	if not cast or cast.device.friendly_name != CHROMECAST_NAME:
		logging.info("Attempting to discover all chromecasts, fallback for direct connect")
		chromecasts = pychromecast.get_chromecasts()
		if chromecasts:
			cast = next(cc for cc in chromecasts if cc.device.friendly_name == CHROMECAST_NAME)
			cast.wait()
	
	if cast and cast.device:
		with open('.living_room_chromecast_ip', 'w') as f:
			f.write(cast.host)
			logging.info("Stored Living Room Chromecast IP of: " + str(cast.host))
		mc = cast.media_controller
		mc.block_until_active()
		casted_app = cast.status.display_name.lower()
		#check if something is playing
		#if cast.status is None or cast.app_id in (None, IDLE_APP_ID):
		if mc.status.player_is_playing:
			mc.pause()
			pause_delay = int(time.time() - start_time)
			logging.info("Paused " + CHROMECAST_NAME + ", delay was " + str(pause_delay) + " seconds")
			return pause_delay
		elif mc.status.player_is_paused:
			if casted_app in ('netflix','hulu','hbo go','google play movies','youtube'):
				if mc.status.supports_seek:
					rewind_time = pause_delay + REWIND_PADDING
					mc.seek(max(0, mc.status.current_time - rewind_time))
					logging.info("Rewinded " + str(rewind_time) + " secs " + CHROMECAST_NAME)
					# need to play after rewinding some apps
					if casted_app in ('hulu','google play movies'):
						mc.play()
						logging.info("Played " + CHROMECAST_NAME)
				else:
					mc.play()	
					logging.info("Played " + CHROMECAST_NAME)					
			else:
				logging.info("App '" + str(casted_app) + "' not rewinded, consider adding")
				mc.play()	
				logging.info("Played " + CHROMECAST_NAME)
		#mc.tear_down()
		cast.disconnect()
	else:
		logging.error("Could not establish connection with Living Room Chromecast..")
		blink_for_error()
	# added in the case that it doesn't play from a paused state
	return pause_delay

def blink_for_error():
	for _ in range(4):
		GPIO.output(22, GPIO.LOW)
		time.sleep(0.3)
		GPIO.output(22, GPIO.HIGH)
		time.sleep(0.3)

def main():
	logging.basicConfig(level=logging.INFO,
		format='%(asctime)s %(levelname)s %(message)s',
		filename='/home/dan/chromecast_control/chromecast_control.log')
	
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(22, GPIO.OUT, initial=GPIO.LOW)
	GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	pause_delay = 0
	while True:
		try:
			GPIO.wait_for_edge(17, GPIO.FALLING)
			GPIO.output(22, GPIO.HIGH)
			pause_delay = main_control(pause_delay)
		except KeyboardInterrupt:				
			logging.info("KeyboardInterrupt ended program...")
			break
		except Exception as e:
			logging.error("Encountered exception in main while loop: " + str(e))
			blink_for_error()
		finally:
			GPIO.output(22, GPIO.LOW)
	GPIO.cleanup()

if __name__ == '__main__':
	main()
