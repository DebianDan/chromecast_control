import RPi.GPIO as GPIO
import pychromecast
import logging
import time

def main_control():	
	
	CHROMECAST_NAME = 'Living Room'
	cast = None
	chromecast_ip = None
	
	try:
		with open('.living_room_chromecast_ip', 'r') as f:
			chromecast_ip = f.read()
	except Exception as e:
		logging.warning(str(e))
		pass
	
	if chromecast_ip:
		logging.info("Retrieved saved Living Room Chromecast IP of: " + str(chromecast_ip))
		try:
			cast = pychromecast.Chromecast(chromecast_ip)
		except Exception as e:
			logging.warning("Failed to connect directly: " + str(e))
			pass
		else:
			cast.wait()
	
	if not cast:
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
		if mc.status.player_is_playing:
			mc.pause()
			logging.info("Paused " + CHROMECAST_NAME)
		elif mc.status.player_is_paused:
			if mc.status.supports_seek:
				mc.seek(max(0, mc.status.current_time - 10))
				logging.info("Rewinded 10 secs " + CHROMECAST_NAME)
			time.sleep(.5)
			if mc.status.player_is_paused:
				mc.play()	
				logging.info("Played " + CHROMECAST_NAME)
	else:
		logging.error("Could not establish connection with Living Room Chromecast..")

def main():
	logging.basicConfig(level=logging.INFO,
		format='%(asctime)s %(levelname)s %(message)s',
		filename='chromecast_control.log')
	
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	
	while True:
		try:
			GPIO.wait_for_edge(17, GPIO.FALLING)
			main_control()
		except:
			break
	GPIO.cleanup()

if __name__ == '__main__':
	main()
