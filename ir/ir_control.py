#!/usr/bin/python3

import pychromecast
import evdev 
import argparse
import logging
import random
import time
import os
from pychromecast.controllers.youtube import YouTubeController

def cc_play_youtube(cast):
    # video_id is the last part of the url https://youtube.com/watch?v=video_id
    YT_VIDEOS = [
        'Wuo04iM3lbk'  # tounge remix
    ]

    yt = YouTubeController()
    cast.register_handler(yt)
    video_id = random.choice(YT_VIDEOS)
    yt.play_video(video_id)
    
    logging.info("Casted video " + video_id + " to youtube")


def cc_pause(mc, casted_app):
    mc.pause()
    logging.info("Paused " + casted_app)


def cc_play(mc, casted_app):
    rewinded = cc_rewind(mc, casted_app, 10)
    if not rewinded:
        mc.play()	
        logging.info("Played " + casted_app)


def cc_rewind(mc, casted_app, rewind_secs):
    if casted_app not in ('spotify') and mc.status.supports_seek:
        mc.seek(max(0, mc.status.current_time - rewind_secs))
        logging.info("Rewinded " + casted_app + " " + str(rewind_secs) + " seconds")
        # need to play after rewinding some apps
        if casted_app in ('hulu','google play movies'):
            mc.play()
            logging.info("Forced play on " + casted_app + " after rewinding")
        return True	
    else:
        logging.warning(casted_app + " does not support seeking")
        return False


def cc_control(key_code, cast):
    if key_code == 'KEY_D':
        cc_play_youtube(cast)
        return
    else:
        # Main pause, rewind, play functionality
        casted_app = cast.status.display_name.lower()
        logging.info("Casted app is " + casted_app)

        # FYI cast.is_idle does NOT work reliably so casted_app is a trial instead
        if casted_app != 'backdrop':
            mc = cast.media_controller
            mc.block_until_active() # TODO is this what locks up if nothing is playing currently? if so, is it necessary?
            
            if key_code == 'KEY_A':
                # check if something is playing
                if mc.status.player_is_playing:
                    cc_pause(mc, casted_app)
                elif mc.status.player_is_paused:
                    cc_play(mc, casted_app)
            elif key_code == 'KEY_B':
                cc_rewind(mc, casted_app, 30)
            elif key_code == 'KEY_C':
                cc_rewind(mc, casted_app, 86400) # TODO this is a quick hack to rewind to the beginning of any show that is < 24 hrs long ;)


def chromecast_connect(chromecast_name, chromecast_ip=None):	
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

    if cast:
        cast.wait()
        logging.info("Successfully connected to chromecast " + cast.name)
    else:
        logging.warning("Could not establish connection with Chromecast " + chromecast_name)
        blink_for_error()
    
    return cast


# TODO look into making a light on the board blink for an error
# https://www.raspberrypi.org/forums/viewtopic.php?t=12530
def blink_for_error():
    """for _ in range(3):
        GPIO.output(22, GPIO.LOW)
        time.sleep(0.3)
        GPIO.output(22, GPIO.HIGH)
        time.sleep(0.3)"""
    pass


def main():
    parser = argparse.ArgumentParser(description='Infared remote application to pause a chromecast then rewind and play')
    parser.add_argument("chromecast_name", help="Name of the Chromecast", metavar="CHROMECAST_NAME")
    parser.add_argument("--ip", dest="chromecast_ip", help="IP of the Chromecast for faster lookups (protip: use a DHCP reservation)", metavar="IP")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        filename='/home/pi/ir/chromecast_ir_control.log')

    logging.info("[+] Chromecast IR controller started")

    # PI zero only has one event device right now so this works
    ir_events = evdev.InputDevice('/dev/input/event0')
    """
        # Add code to get all input devices and determine the correct path by name
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            if device.name == 'gpio_ir_recv':
                ir_events = device
    """

    pause_delay = 0
    # https://python-evdev.readthedocs.io/en/latest/apidoc.html
    try:
        for ir_event in ir_events.read_loop(): 
            try:
                if ir_event.type == evdev.ecodes.EV_KEY:
                    key_event = evdev.categorize(ir_event)
                    logging.debug("[-] {}".format(key_event))

                    if key_event.keystate == 0: #0=up, 1=down, 2=hold, only trigger on release events
                        key_code = key_event.keycode
                        logging.info("[+] {} released.".format(key_code))
                        # Look into setting a repeat delay? Or possibly not register any other key up events 
                        # that happened while processing another to avoid duplicate actions

                        cast = chromecast_connect(args.chromecast_name, args.chromecast_ip)

                        if cast:
                            cc_control(key_code, cast)
                            # Clean up chromecast connection
                            #mc.tear_down() # TODO what would this do?
                            cast.disconnect() # TODO explore re-using cast instead of disconnect, what happens when it goes stale? 

            except Exception as e:
                logging.error("Encountered exception in main event read loop: " + str(e), exc_info=True)
                continue
    except KeyboardInterrupt:				
        logging.info("[-] KeyboardInterrupt ended program...")
    

if __name__ == "__main__":
    main()