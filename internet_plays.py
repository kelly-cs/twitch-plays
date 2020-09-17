'''
Internet Plays 
Controller

This script controls the "internet plays" series, allowing users from multiple platforms (youtube, twitch, facebook, discord, steam, etc)
to send game input through a unified chat.

'''

# issue:
# multiple aliases for buttons don't work for some reason

import time
import requests
import sys
import asyncio
import json
import os
import socket # for twitch IRC client
import websockets # for restream http ws client 
import threading
import aiohttp
import re # for parsing twitch messages in regex
import pyvjoy # for screen movement
import pydirectinput
#from multiprocessing import Pool, Process, Queue

BOT_NAME = "LikaiCK"
CHANNEL_NAME = "#likaick"
OAUTH_TOKEN = sys.argv[1]
TWITCH_SERVER = "irc.chat.twitch.tv"
TWITCH_PORT = 6667

# acceptable commands get routed to X360CE emulator
j = pyvjoy.VJoyDevice(1)
socket_timeout = 120
directory = os.path.dirname(__file__)
command_queue = [] # list of commands extracted from chat
acceptable_commands = {
    "w":"w",# treat as stick
    "ww":"w",# treat as stick
    "www":"w",# treat as stick
    "wwww":"w",# treat as stick
    "a":"a",# treat as stick
    "aa":"a",# treat as stick
    "aaa":"a",# treat as stick
    "aaaa":"a",# treat as stick
    "s":"s",# treat as stick
    "ss":"s",# treat as stick
    "sss":"s",# treat as stick
    "ssss":"s",# treat as stick
    "d":"d",# treat as stick
    "dd":"d",# treat as stick
    "ddd":"d",# treat as stick
    "dddd":"d",# treat as stick
    "j":"j", # turning left
    "jj":"jj", # turning lefta lot
    "jjj":"jjj", # turning lefta lot
    "jjjj":"jjjj", # turning lefta lot
    "l":"l", # turn right
    "ll":"ll", # turn right
    "lll":"lll", # turn right
    "llll":"llll", # turn right
    "i":"i", # turn up
    "ii":"ii", # turn up up
    "iii":"iii", # turn up up
    "iiii":"iiii", # turn up up
    "k":"k", # turn down
    "kk": "kk", # turn down down
    "kkk": "kkk", # turn down down
    "kkkk": "kkkk", # turn down down
    "r":1,#r # tap to reload
    "reload":1, # tap to reload
    "use":1, # hold to interact
    "flip":1,
    "pickup":1,
    "reloadleft":2, # tap to reload
    "dualwieldleft":2, # press longer to pickup weapon
    "dualwieldright":1, # press longer to pickup weapon
    "shootleft":3, # hold to shoot
    "melee":3,
    "shootright": 4, # hold to shoot
    "shoot":4, # hold to shoot
    "shootlong":4, # hold to shoot, longer duration, for weapons like spartan laser
    "aim":5, # press right stick down
    "crouch":6, # press left stick down
    "swap":7, #y
    "swapweapon":7, #y
    "equipment":8, #x
    "g":9,
    "grenade":9, #b
    "jump":10, #a
    "flashlight":11 #up dpad

    #"shift":"shiftleft", # shift
    #"ability":"shiftleft", # shift
    #"nvg":"4" # 4 reach only
}


def play_function(X,Y,Z,XRot,YRot,ZRot,j):
    MAX_VJOY = 32767
    MIDDLE_VJOY = int(32767/2)
    
    if X != None:
        j.set_axis(pyvjoy.HID_USAGE_X, int(X * MAX_VJOY))
    if Y != None:
        j.set_axis(pyvjoy.HID_USAGE_Y, int(Y * MAX_VJOY))
    if Z != None:
        j.set_axis(pyvjoy.HID_USAGE_Z, int(Z * MAX_VJOY))
    if XRot != None:
        j.set_axis(pyvjoy.HID_USAGE_RX, int(XRot * MAX_VJOY))
    if YRot != None:
        j.set_axis(pyvjoy.HID_USAGE_RY, int(YRot * MAX_VJOY))
    if ZRot != None:
        j.set_axis(pyvjoy.HID_USAGE_RZ, int(ZRot * MAX_VJOY))
    return True

# pass button as string
# x, y, z, xr, yr, zr, xrot, yrot, xrrot, yrrot
def reset_function(button, j):
    MAX_VJOY = 32767
    MIDDLE_VJOY = int(MAX_VJOY/2)
    button_to_reset = button.strip() # whitespace might be messing this up
    try:
        print("resetting " + button)
        if button == "a" or button == "aa" or button == "aaa" or button == "aaaa" or button == "d" or button == "dd" or button == "ddd" or button == "dddd":
            button_to_reset = "xrot"
        elif button == "w" or button == "ww" or button == "www" or button == "wwww" or button == "s" or button == "ss" or button == "sss" or button == "ssss":
            button_to_reset = "yrot"
        elif button == "j" or button == "jj" or button == "jjj" or button == "jjjj" or button == "l" or button == "ll" or button == "lll" or button == "llll":
            button_to_reset = "x"
        elif button == "i" or button == "ii" or button == "iii" or button == "iiii" or button == "k" or button == "kk" or button == "kkk" or button == "kkkk":
            button_to_reset = "y"

        elif button_to_reset == None:
            j.set_axis(pyvjoy.HID_USAGE_X, MIDDLE_VJOY)
            j.set_axis(pyvjoy.HID_USAGE_Y, MIDDLE_VJOY)
            j.set_axis(pyvjoy.HID_USAGE_Z, MIDDLE_VJOY)
            j.set_axis(pyvjoy.HID_USAGE_RX, MIDDLE_VJOY)
            j.set_axis(pyvjoy.HID_USAGE_RY, MIDDLE_VJOY)
            j.set_axis(pyvjoy.HID_USAGE_RZ, MIDDLE_VJOY)
        if button_to_reset == "x":
            j.set_axis(pyvjoy.HID_USAGE_X, MIDDLE_VJOY)
            print("x reset")
        elif button_to_reset == "y":
            j.set_axis(pyvjoy.HID_USAGE_Y, MIDDLE_VJOY)
            print("y reset")
        elif button_to_reset == "z":
            j.set_axis(pyvjoy.HID_USAGE_Z, MIDDLE_VJOY)
            print("z reset")
        elif button_to_reset == "xrot":
            j.set_axis(pyvjoy.HID_USAGE_RX, MIDDLE_VJOY)
            print("xrot reset")
        elif button_to_reset == "yrot":
            j.set_axis(pyvjoy.HID_USAGE_RY, MIDDLE_VJOY)
            print("yrot reset")
        elif button_to_reset == "zrot":
            j.set_axis(pyvjoy.HID_USAGE_RZ, MIDDLE_VJOY)
            print("zrot reset")
        else:
            j.set_button(acceptable_commands[button], 0) # release the right button
        # j.update()
    except:
        print("tried to reset " + button + " but it was busy. Trying again")
        reset_function(button, j) # try again
    return True

def is_move_command(command):
    commandlist = ["w","ww","www","wwww","a","aa","aaa","aaaa","s","ss","sss","ssss","d","dd","ddd","dddd"]
    if command in commandlist:
        return True
    else:
        return False

def is_aim_command(command):
    commandlist = ["j","jj","jjj","jjjj","i","ii","iii","iiii","k","kk","kkk","kkkk","l","ll","lll","llll"]
    if command in commandlist:
        return True
    else:
        return False

def handle_aim_command(button, j, **kwargs):
    print(kwargs)
    moveduration_single = 0.02
    moveduration_double = 0.06
    moveduration_triple = 0.175
    moveduration_quad = 0.35
    if button == "j": 
        play_function(0,None,None,None,None,None,j) # turn left on x axis
        return moveduration_single
        # time.sleep(moveduration_single)
        # reset_function("x", j)
        #pydirectinput.move(-175, 0)
    elif button == "jj":
        play_function(0,None,None,None,None,None,j) # turn left on x axis
        return moveduration_double
        # time.sleep(moveduration_double)
        # reset_function("x", j)
        #pydirectinput.move(-350, 0)
    elif button == "jjj":
        play_function(0,None,None,None,None,None,j) # turn left on x axis
        return moveduration_triple
        # time.sleep(moveduration_double)
        # reset_function("x", j)
        #pydirectinput.move(-350, 0)
    elif button == "jjjj":
        play_function(0,None,None,None,None,None,j) # turn left on x axis
        return moveduration_quad
        # time.sleep(moveduration_double)
        # reset_function("x", j)
        #pydirectinput.move(-350, 0)
    elif button == "l":
        play_function(1,None,None,None,None,None,j) # turn right on x axis
        return moveduration_single
        # time.sleep(moveduration_single)
        # reset_function("x", j)
        #pydirectinput.move(175, 0)
    elif button == "ll":
        play_function(1,None,None,None,None,None,j) # turn right on x axis
        return moveduration_double
        # time.sleep(moveduration_double)
        # reset_function("x", j)
        #pydirectinput.move(350, 0)
    elif button == "lll":
        play_function(1,None,None,None,None,None,j) # turn right on x axis
        return moveduration_triple
        # time.sleep(moveduration_double)
        # reset_function("x", j)
        #pydirectinput.move(350, 0)
    elif button == "llll":
        play_function(1,None,None,None,None,None,j) # turn right on x axis
        return moveduration_quad
        # time.sleep(moveduration_double)
        # reset_function("x", j)
        #pydirectinput.move(350, 0)
    elif button == "i":
        play_function(None,1,None,None,None,None,j) # turn up on y axis
        return moveduration_single
        # time.sleep(moveduration_single)
        # reset_function("y", j)
        #pydirectinput.move(0,-175)
    elif button == "ii":
        play_function(None,1,None,None,None,None,j) # turn up on y axis
        return moveduration_double
        # time.sleep(moveduration_double)
        # reset_function("y", j)
        #pydirectinput.move(0,-350)
    elif button == "iii":
        play_function(None,1,None,None,None,None,j) # turn up on y axis
        return moveduration_triple
        # time.sleep(moveduration_double)
        # reset_function("y", j)
        #pydirectinput.move(0,-350)
    elif button == "iiii":
        play_function(None,1,None,None,None,None,j) # turn up on y axis
        return moveduration_quad
        # time.sleep(moveduration_double)
        # reset_function("y", j)
        #pydirectinput.move(0,-350)
    elif button == "k":
        play_function(None,0,None,None,None,None,j) # turn down on y axis
        return moveduration_single
        # time.sleep(moveduration_single)
        # reset_function("y", j)
        #pydirectinput.move(0,175)
    elif button == "kk":
        play_function(None,0,None,None,None,None,j) # turn down on y axis
        return moveduration_double
        # time.sleep(moveduration_double)
        # reset_function("y", j)
        #pydirectinput.move(0,350)
    elif button == "kkk":
        play_function(None,0,None,None,None,None,j) # turn down on y axis
        return moveduration_triple
        # time.sleep(moveduration_double)
        # reset_function("y", j)
        #pydirectinput.move(0,350)
    elif button == "kkkk":
        play_function(None,0,None,None,None,None,j) # turn down on y axis
        return moveduration_quad
        # time.sleep(moveduration_double)
        # reset_function("y", j)
        #pydirectinput.move(0,350)
    return 0

def handle_move_command(button, j, **kwargs):
    #j = pyvjoy.VJoyDevice(1)
    print(kwargs)
    moveduration_single = 0.4
    moveduration_double = 0.8
    moveduration_triple = 2.2
    moveduration_quad = 3.2
    if button == "w": 
        play_function(None,None,None,None,1,None,j) # turn up on y axis
        return moveduration_single
        #time.sleep(moveduration_single)
        #reset_function("yrot", j)
        #pydirectinput.move(-175, 0)
    elif button == "ww": 
        play_function(None,None,None,None,1,None,j) # turn up on y axis
        return moveduration_double
        #time.sleep(moveduration_double)
        #reset_function("yrot", j)
        #pydirectinput.move(-175, 0)
    elif button == "www": 
        play_function(None,None,None,None,1,None,j) # turn up on y axis
        return moveduration_triple
        #time.sleep(moveduration_triple)
        #reset_function("yrot", j)
        #pydirectinput.move(-175, 0)
    elif button == "wwww": 
        play_function(None,None,None,None,1,None,j) # turn up on y axis
        return moveduration_quad
        #time.sleep(moveduration_triple)
        #reset_function("yrot", j)
        #pydirectinput.move(-175, 0)
    elif button == "a":
        play_function(None,None,None,0,None,None,j) # turn left on x axis
        return moveduration_single
        #time.sleep(moveduration_single)
        #reset_function("xrot", j)
        #pydirectinput.move(-350, 0)
    elif button == "aa":
        play_function(None,None,None,0,None,None,j) # turn left on x axis
        return moveduration_double
        #time.sleep(moveduration_double)
        #reset_function("xrot", j)
        #pydirectinput.move(-350, 0)
    elif button == "aaa":
        play_function(None,None,None,0,None,None,j) # turn left on x axis
        return moveduration_triple
        #time.sleep(moveduration_triple)
        #reset_function("xrot", j)
        #pydirectinput.move(-350, 0)
    elif button == "aaaa":
        play_function(None,None,None,0,None,None,j) # turn left on x axis
        return moveduration_quad
        #time.sleep(moveduration_triple)
        #reset_function("xrot", j)
        #pydirectinput.move(-350, 0)
    elif button == "s":
        play_function(None,None,None,None,0,None,j) # turn down on y axis
        return moveduration_single
        #time.sleep(moveduration_single)
        #reset_function("yrot", j)
        #pydirectinput.move(175, 0)
    elif button == "ss":
        play_function(None,None,None,None,0,None,j) # turn down on y axis
        return moveduration_double
        #time.sleep(moveduration_double)
        #reset_function("yrot", j)
        #pydirectinput.move(175, 0)
    elif button == "sss":
        play_function(None,None,None,None,0,None,j) # turn down on y axis
        return moveduration_triple
        #time.sleep(moveduration_triple)
       # reset_function("yrot", j)
        #pydirectinput.move(175, 0)
    elif button == "ssss":
        play_function(None,None,None,None,0,None,j) # turn down on y axis
        return moveduration_quad
        #time.sleep(moveduration_triple)
       # reset_function("yrot", j)
        #pydirectinput.move(175, 0)
    elif button == "d":
        play_function(None,None,None,1,None,None,j) # turn right on x axis
        return moveduration_single
        #time.sleep(moveduration_single)
        #reset_function("xrot", j)
        #pydirectinput.move(350, 0)
    elif button == "dd":
        play_function(None,None,None,1,None,None,j) # turn right on x axis
        return moveduration_double
        #time.sleep(moveduration_double)
        #reset_function("xrot", j)
        #pydirectinput.move(350, 0)
    elif button == "ddd":
        play_function(None,None,None,1,None,None,j) # turn right on x axis
        return moveduration_triple
        #time.sleep(moveduration_triple)
        #reset_function("xrot", j)
        #pydirectinput.move(350, 0)
    elif button == "dddd":
        play_function(None,None,None,1,None,None,j) # turn right on x axis
        return moveduration_quad
        #time.sleep(moveduration_triple)
        #reset_function("xrot", j)
        #pydirectinput.move(350, 0)
    return 0

# press the button it tells you to
def handle_action_command(button, j, **kwargs):
    press_duration = 2
    shoot_duration = 1.5
    shoot_long_duration = 3
    tap_duration = 0.08
    print(kwargs)
    if button in acceptable_commands:
        print("handling action: " + button)
        if button == "shoot" or button == "shootleft":
            j.set_button(acceptable_commands[button], 1) # press the right button
            return shoot_duration
        elif button == "crouch" or button == "aim" or button == "swap" or button == "swapweapon" or button == "reload" or button == "r" or button == "reloadleft" or button == "melee":
            j.set_button(acceptable_commands[button], 1) # press the right button
            return tap_duration
        elif button == "shootlong":
            j.set_button(acceptable_commands[button], 1) # press the right button
            return shoot_long_duration
        elif button == "use" or button == "dualwieldleft" or button == "dualwieldright" or button == "reloadleft":
            j.set_button(acceptable_commands[button], 1) # press the right button
            return press_duration
        else:
            j.set_button(acceptable_commands[button], 1) # press the right button
            return tap_duration
    else:
        return 0

# this is a callback function ran when a threading.Timer completes
# essentially it just runs a reset on the command that was done
def reset_completed_commands(command):
    reset_function(command, j)
    return True

# https://www.learndatasci.com/tutorials/how-stream-text-data-twitch-sockets-python/
def get_twitch_message(resp):
    #print("get_twitch_message: " + resp)
    response = resp
    try:
        msg = response.split(":",2)[2].strip().partition(" ")[0]  # allows duplicate commands in form of w juisdnfjsdn w jbnfjhdsf etc
        return msg
    except IndexError:
         return "PING"
         
# https://www.learndatasci.com/tutorials/how-stream-text-data-twitch-sockets-python/
def get_twitch_author(resp):
    #print("get_twitch_author: " + resp)
    response = resp
    try:
        author = response.split(":",2)[1].strip()
        return author
    except IndexError: # assume it's a PING and just send a PONG
        return "PING"

async def listen_to_chat():
    max_move_commands = 2
    max_aim_commands = 1
    max_action_commands = 2
    max_tasks = 5
    aim_lock = threading.Lock() 
    movement_semaphore = threading.BoundedSemaphore(max_move_commands)
    action_lock = threading.Lock() # only 1 action at a time
    vjoy_lock = threading.Lock() # only 1 thing can update vjoy, add/remove at a time.
    tasks = {} # list of tasks being performed, in dicts ["w" : timer] where num is time remaining before reset is issued
    currently_listening = True
    start_time = time.time()
    last_command_time = time.time()
    twitch_sock = socket.socket()
    twitch_sock.connect((TWITCH_SERVER, TWITCH_PORT))
    twitch_sock.send(f"PASS {OAUTH_TOKEN}\n".encode("utf-8"))
    twitch_sock.send(f"NICK {BOT_NAME}\n".encode("utf-8"))
    twitch_sock.send(f"JOIN {CHANNEL_NAME}\n".encode("utf-8"))
    # connects to twitch IRC

    while currently_listening:
        msg = twitch_sock.recv(2048).decode('utf-8')
        command = get_twitch_message(msg)
        author = get_twitch_author(msg)
        print(command + " | " + author)
        timestart = time.time()
        if command == "PING":
            twitch_sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            print("sent a pong to maintain connection!")
        if is_aim_command(command):
            if(aim_lock.acquire(blocking=False)): # check and see if the lock is available. Ignore if not.
                if(vjoy_lock.acquire(blocking=False)):
                    try:
                        print("aimlock acquired")
                        print(command)
                        timestart = time.time()
                        time_to_wait_in_secs = handle_aim_command(command,j)
                        if time_to_wait_in_secs > 0:
                            if command in tasks: # if it's already running, make a new one
                                tasks[command].cancel()
                            # always create a new timer, whether or not it had to cancel an existing command's timer
                            timer = threading.Timer(time_to_wait_in_secs, reset_completed_commands, args=[command])
                            tasks[command] = timer
                            tasks[command].start()

                    except:
                        print("something tried to access vjoy at the same time. IGNORE..")
                        pass
                    finally:
                        aim_lock.release()
                        vjoy_lock.release()
                        print("aimlock freed")
            else:
                print('ignored an aim command, lock unavailable')
        elif is_move_command(command):
            if(movement_semaphore.acquire(blocking=False)):
                if(vjoy_lock.acquire(blocking=False)):
                    try:
                        print(command)
                        timestart = time.time()
                        time_to_wait_in_secs = handle_move_command(command,j)
                        if time_to_wait_in_secs > 0:
                            if command in tasks: # if it's already running, make a new one - TODO: THJIS WILL RUN EVERY TIME, WE DON'T DELETE IT FROM THE DICT
                                tasks[command].cancel()
                            # always create a new timer, whether or not it had to cancel an existing command's timer
                            timer = threading.Timer(time_to_wait_in_secs, reset_completed_commands, args=[command])
                            tasks[command] = timer
                            tasks[command].start()
                    except:
                        print("something tried to access vjoy at the same time. IGNORE..")
                        pass
                    finally:
                        movement_semaphore.release()
                        vjoy_lock.release()
                        print("movement semaphore lock released")
                else:
                    print('ignored move command, locks unavailable')
        elif command in acceptable_commands: # any other command
            if(action_lock.acquire(blocking=False)): # check and see if Action lock is available
                if(vjoy_lock.acquire(blocking=False)):
                    try:
                        print(print(command))
                        print("action lock acquired")
                        timestart = time.time()
                        time_to_wait_in_secs = handle_action_command(command,j)
                        if time_to_wait_in_secs > 0:
                            if command in tasks: # if it's already running, make a new one
                                tasks[command].cancel()
                            # always create a new timer, whether or not it had to cancel an existing command's timer
                            timer = threading.Timer(time_to_wait_in_secs, reset_completed_commands, args=[command])
                            tasks[command] = timer
                            tasks[command].start()
                    except:
                        print("something tried to access vjoy at the same time. IGNORE..")
                        pass
                    finally:
                        action_lock.release()
                        vjoy_lock.release()
                        print("action lock freed")
                else:
                    print("ignored action command, lock unavailable")

    print('exiting listen loop')
    twitch_sock.close()


if __name__ == "__main__": # try loading a refresh/intial token locally first:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(listen_to_chat()) #twitch
    loop.close()
