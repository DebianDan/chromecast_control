import pychromecast
import logging

CHROMECAST_NAME = 'Living Room'
cast = None
chromecast_ip = None

logging.basicConfig(level=logging.DEBUG,
	format='%(asctime)s %(levelname)s %(message)s',
	filename='chromecast_control.log')

try:
	with open('.living_room_chromecast_ip', 'r') as f:
		chromecast_ip = f.read()
except Exception as e:
	print e
	pass

if chromecast_ip:
	logging.debug("Retrieved saved Living Room Chromecast IP of: " + str(chromecast_ip))
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
		cast = next(cc for cc in chromecasts if cc.device.friendly_name == chromecast_name)
		cast.wait()

if cast and cast.device:
	with open('.living_room_chromecast_ip', 'w') as f:
		f.write(cast.host)
		logging.debug("Stored Living Room Chromecast IP of: " + str(cast.host))
	mc = cast.media_controller
	mc.block_until_active()
	if mc.status.player_is_playing:
		mc.pause()
		logging.info("Paused " + chromecast_name)
	elif mc.status.player_is_paused:
		if mc.status.supports_seek:
			mc.seek(max(0, mc.status.current_time - 10))
			logging.info("Rewinded 10 secs " + chromecast_name)
		mc.play()	
		logging.info("Played " + chromecast_name)
else:
	logging.error("Could not establish connection with Living Room Chromecast..")


