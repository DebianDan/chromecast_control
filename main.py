import pychromecast

CHROMECAST_NAME = 'Living Room'
cast = None
chromecast_ip = None

try:
	with open('.living_room_chromecast_ip', 'r') as f:
		chromecast_ip = f.read()
except Exception as e:
	print e
	pass

if chromecast_ip:
	print "DEBUG: Retrieved saved Living Room Chromecast IP of: " + str(chromecast_ip)
	try:
		cast = pychromecast.Chromecast(chromecast_ip)
	except Exception as e:
		print "WARN: Failed to connect directly: " + str(e)
		pass
	else:
		cast.wait()

if not cast:
	print "INFO: Attempting to discover all chromecasts, fallback for direct connect"
	chromecasts = pychromecast.get_chromecasts()
	if chromecasts:
		cast = next(cc for cc in chromecasts if cc.device.friendly_name == CHROMECAST_NAME)
		cast.wait()

if cast and cast.device:
	with open('.living_room_chromecast_ip', 'w') as f:
		f.write(cast.host)
		print "DEBUG: Stored Living Room Chromecast IP of: " + str(cast.host)
	mc = cast.media_controller
	mc.block_until_active()
	if mc.status.player_is_playing:
		mc.pause()
		print "INFO: Paused " + CHROMECAST_NAME
	elif mc.status.player_is_paused:
		if mc.status.supports_seek:
			mc.seek(max(0, mc.status.current_time - 10))
			print "INFO: Rewinded 10 secs " + CHROMECAST_NAME
		mc.play()	
		print "INFO: Played " + CHROMECAST_NAME
else:
	print "ERROR: Could not establish connection with Living Room Chromecast.."
