import sys
from typing import Set
import pyautogui,pyaudio,audioop,threading,time,win32api,configparser,mss,mss.tools,cv2,numpy
#from dearpygui.core import *
#from dearpygui.simple import *
import random,os,time

#Loads Settings
parser = configparser.ConfigParser()
try:
    parser.read('settings.ini')
except :
    print("not exist!")

debugmode = parser.getboolean('Settings','debug')
resolution = parser.getint('Settings', 'game_resolution')
max_volume = parser.getint('Settings','Volume_Threshold')
screen_area = parser.get('Settings','tracking_zone')
coord_bait = parser.get('Settings','bait_inventory')
detection_threshold = parser.getfloat('Settings','detection_threshold')
dist_launch_time = parser.getfloat('Settings', 'launch_time')
cast_time = parser.getint('Settings', 'cast_time')
food_time = parser.getint('Settings', 'food_time')
max_catch_time = parser.getint('Settings', 'max_catch_time')
screen_area = screen_area.strip('(')
screen_area = screen_area.strip(')')
cordies = screen_area.split(',')
screen_area = int(cordies[0]),int(cordies[1]),int(cordies[2]),int(cordies[3])
bobber_img = ('bobber-1024-768.png', 'bobber-1280x720.png', 'bobber-1600x1024.png')
#print(bobber_img[0])
#screen_area = x1,y1,x2,y2
#resolution game
resolutions = ["1024x768", "1080x720", "1600x1024"]
#Coords for fishing spots
coords = []

#print(coord_bait)
coord_bait = coord_bait.strip('(')
coord_bait = coord_bait.strip(')')
#(coord_bait)
xy_bait = coord_bait.split(',')
coord_bait = int(xy_bait[0]),int(xy_bait[1])
#Sound Volume
total = 0

#Current Bot State
STATE = "IDLE"

#Thread Stopper
stop_button = False

#Stuff for mouse events
state_left = win32api.GetKeyState(0x01)
state_right = win32api.GetKeyState(0x02)

#fish counters
fish_count = 0

bait_counter = 0
food_bait = 0
food_timer = 0

##########################################################
#
#   These Functions handle bot state / minigame handling
#
##########################################################

#Scans the current input volume
def check_volume():
    global total,STATE,max_volume,stop_button
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,channels=2,rate=44100,input=True,frames_per_buffer=1024)
    current_section = 0
    while 1:
        if stop_button == False:
            total=0
            for i in range(0,2):
                data=stream.read(1024)
                if True:
                    reading=audioop.max(data, 2)
                    total=total+reading
                    if total > max_volume and STATE != "SOLVING" and STATE != "DELAY" and STATE != "CASTING":
                        do_minigame()
        else:
            break

def get_new_spot():
    return random.choice(coords)
#Runs the casting function
def cast_hook():
    global STATE, stop_button
    while 1:
        if stop_button == False:
            if STATE == "CASTING" or STATE == "STARTED":
                time.sleep(2.6)
                pyautogui.mouseUp()
                x,y = get_new_spot()
                pyautogui.moveTo(x,y,tween=pyautogui.linear,duration=0.2)
                time.sleep(0.7)
                log_info(f"Casted towards:{x,y}",logger="Information")
                pyautogui.mouseDown()
                time.sleep(random.uniform(dist_launch_time-0.2,dist_launch_time))
                pyautogui.mouseUp()
                time.sleep(2.5)
                STATE = "CAST"
            elif STATE == "CAST":
                time.sleep(cast_time)
                if STATE == "CAST":
                    log_warning(f"Seems to be stuck on cast. Recasting",logger="Information")
                    pyautogui.click(clicks= 2, interval=0.15)
                    time.sleep(0.25)
                    STATE = "CASTING"
                    cast_hook()
        else:
            break

#Uses obj detection with OpenCV to find and track bobbers left / right coords
def do_minigame():
    global STATE,fish_count,bait_counter
    if STATE != "CASTING" and STATE != "STARTED":
        STATE = "SOLVING"
        log_debug(f'Attempting Minigame',logger="Information")
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        #Initial scan. Waits for bobber to appear
        time.sleep(0.25)
        valid,location,size = Detect_Bobber()
        if valid == "TRUE":
            fish_count += 1
            bait_counter += 1
            t0 = time.time()
            while 1:
                valid,location,size = Detect_Bobber()
                t1 = time.time() - t0
                if valid == "TRUE":
                    if t1 > max_catch_time:
                        pyautogui.mouseUp()
                    elif location[0] < size / 2:
                        pyautogui.mouseDown()
                    else:
                        pyautogui.mouseUp()
                else:
                    if STATE != "CASTING":
                        STATE = "CASTING"
                        pyautogui.mouseUp()
                        break
        else:
            STATE = "CASTING"
#use_food
def use_food():
    global stop_button
    while True:
        if stop_button == False:
            time.sleep(food_time*60)
            pyautogui.press("2")
            log_info(f"Food is used.",logger="Information")
        else:
            break
##########################################################
#
#   These Functions are all Callbacks used by DearPyGui
#
##########################################################

#Generates the areas used for casting
def generate_coords(sender,data):
    global coords,STATE,state_left
    amount_of_choords = get_value("Amount Of Spots")
    for n in range(int(amount_of_choords)):
        n = n+1
        temp = []
        log_info(f'[spot:{n}]|Press Spacebar over the spot you want',logger="Information")
        time.sleep(1)
        while True:
            a = win32api.GetKeyState(0x20)  
            if a != state_left:
                state_left = a 
                if a < 0:
                    break
            time.sleep(0.001) 
        x,y = pyautogui.position()
        temp.append(x)
        temp.append(y)
        coords.append(temp)
        log_info(f'Position:{n} Saved. | {x,y}',logger="Information")
#generate location bait inventory
def bait_coords(sender,data):
    global coord_bait,STATE,state_left
    for n in range(1):
        n = n+1
        temp = []
        log_info(f'[Bait:{n}]|Press Spacebar over the bait in inventory',logger="Information")
        time.sleep(1)
        while True:
            a = win32api.GetKeyState(0x20)  
            if a != state_left:
                state_left = a 
                if a < 0:
                    break
            time.sleep(0.001) 
        x,y = pyautogui.position()
        coord_bait = x,y
        log_info(f'Updated bait inventory to {coord_bait}',logger="Information")
#Sets tracking zone for image detection
def Grab_Screen(sender,data):
    global screen_area
    state_left = win32api.GetKeyState(0x20)
    image_coords = []
    log_info(f'Please hold and drag space over tracking zone (top left to bottom right)',logger="Information")
    while True:
        a = win32api.GetKeyState(0x20)
        if a != state_left:  # Button state changed
            state_left = a
            if a < 0:
                x,y = pyautogui.position()
                image_coords.append([x,y])
            else:
                x,y = pyautogui.position()
                image_coords.append([x,y])
                break
        time.sleep(0.001)
    start_point = image_coords[0]
    end_point = image_coords[1]
    screen_area = start_point[0],start_point[1],end_point[0],end_point[1]
    log_info(f'Updated tracking area to {screen_area}',logger="Information")

#Detects bobber in tracking zone using openCV
def change_bober(val):
    if val == 0:
        return cv2.imread(bobber_img[0])
    elif val == 1:
        return cv2.imread(bobber_img[1])
    elif val == 2:
        return cv2.imread(bobber_img[2])
    else:
        log_info(f'Please Select Game Resolution',logger="Information")
        return cv2.imread('bobber.png')
    
        
        

def Detect_Bobber():
    global detection_threshold
    start_time = time.time()
    with mss.mss() as sct:
        base = numpy.array(sct.grab(screen_area))
        base = numpy.flip(base[:, :, :3], 2)  # 1
        base = cv2.cvtColor(base, cv2.COLOR_RGB2BGR)
        bobber = change_bober(resolution)        
        bobber = numpy.array(bobber, dtype=numpy.uint8)
        bobber = numpy.flip(bobber[:, :, :3], 2)  # 1
        bobber = cv2.cvtColor(bobber, cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(base,bobber,cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        #if max_val > 0.5:
        if max_val > detection_threshold:
            print(f"Bobber Found!. certainty:{round(max_val,4)}")
            print("%s s to calculate" % (round(time.time() - start_time,4)))
            return ["TRUE",max_loc,base.shape[1]]
        else:
            print(f"Bobber not found. certainty:{round(max_val,4)}")
            print("%s s to calculate" % (round(time.time() - start_time, 4)))
            return ["FALSE",max_loc,base.shape[1]]

#Starts the bots threads
def start(data,sender):
    global max_volume,stop_button,STATE
    STATE = "STARTING"
    stop_button = False
    volume_manager = threading.Thread(target = check_volume, name= "VOLUME CHECK MANAGE")
    hook_manager = threading.Thread(target = cast_hook, name = "CAST HOOK MANAGE")
    food_manager = threading.Thread(target = use_food, name = "FOOD MANAGER")
    if stop_button == False:
        max_volume = get_value("Set Volume Threshold")
        if len(coords) == 0:
            log_info(f'Please Select Fishing Coords first',logger="Information")
            return
        else:
            pyautogui.mouseUp()
            x,y = get_new_spot()
            pyautogui.moveTo(x,y,tween=pyautogui.linear,duration=0.2)
            time.sleep(0.25)
            pyautogui.mouseDown()
            time.sleep(0.15)
            pyautogui.mouseUp()
            time.sleep(0.15)
            pyautogui.press('1')
            time.sleep(0.8)
            pyautogui.press('2')
            time.sleep(2.2)
            food_manager.start()
            log_info(f'Food Manager Started',logger="Information")
            time.sleep(0.2)
            volume_manager.start()
            log_info(f'Volume Scanner Started',logger="Information")
            hook_manager.start()
            log_info(f'Hook Manager Started',logger="Information")
            log_info(f'Bot Started',logger="Information")
        STATE = "STARTED"
    else:
        log_error(f'Invalid KEY',logger="Information")


#Stops the bot and closes active threads
def stop(data,sender):
    global stop_button,STATE
    STATE = "STOPPING"
    stop_button = True
    log_info(f'Stopping Hook Manager',logger="Information")
    log_info(f'Stopping Volume Scanner',logger="Information")
    pyautogui.mouseUp()
    STATE = "STOPPED"
    coords.clear()
    log_info(f'Stopped Bot. Please re-spot!',logger="Information")

#Updates Bot Volume
def save_volume(sender,data):
    global max_volume
    max_volume = get_value("Set Volume Threshold")
    log_info(f'Max Volume Updated to :{max_volume}',logger="Information")

#Set detection threshold
def save_threshold(sender,data):
    global detection_threshold
    detection_threshold = get_value("Set Detection Threshold")
    log_info(f'Detection Threshold Updated to :{detection_threshold}',logger="Information")
#Set time launch dist
def save_dist_launch_time(sender,data):
    global dist_launch_time
    dist_launch_time = get_value("Set Time Lauch Distance")
    log_info(f'Dist time launch Updated to :{dist_launch_time}',logger="Information")
def save_cast_time(sender,data):
    global cast_time
    cast_time = get_value("Set Cast Time")
    log_info(f'Cast time Updated to :{cast_time}',logger="Information")
def save_food_time(sender,data):
    global food_time
    food_time = get_value("Set Food Time")
    log_info(f'Food time Updated to :{food_time}',logger="Information")
def save_max_catch_time(sender,data):
    global max_catch_time
    max_catch_time = get_value("Set Max Catch Time")
    log_info(f'Max Catch time Updated to :{max_catch_time}',logger="Information")
# save modify resolution bobber
def save_resolution(sender,data):
    global resolution
    resolution = get_value("Set Game Resolution")
    log_info(f'Resolution Game Updated to :{resolutions[resolution]}',logger="Information")

#Title Tracking
def Setup_title():
    global bait_counter
    global food_bait
    while 1:
        set_main_window_title(f"Fisherman | Status:{STATE} | Fish Hits:{fish_count} |Current Volume: {total} / {max_volume}  |")
        time.sleep(0.05)
        if bait_counter >= 10:
            bait_counter = 0
            food_bait += 1
            cal_bait = 10 - food_bait
            log_info(f'Using Bait!. Proximaly reload: {cal_bait}', logger="Information")
            pyautogui.press('1')
            if food_bait == 10:
                pyautogui.press('i')
                x = int(coord_bait[0])
                y = int(coord_bait[1])
                pyautogui.moveTo(x,y,tween=pyautogui.linear,duration=0.2)
                time.sleep(0.3)
                log_info(f'Reloading bait...', logger = "Information")
                pyautogui.click(button='right', interval=0.25)
                time.sleep(0.3)
                pyautogui.press('i')
                food_bait =0

def Setup():
    if os.path.exists('first_run.txt'):
        return
    else:
        print("Detected first run...\nChecking Files.")        
        if os.path.exists('bobber.png'):
            print('\U0001f44d' + ' Found bobber.png')
        else:
            print('ERROR | No bobber.png found. Please obtain the bobber.png and restart.')
            exit('bobber error')
        for i in bobber_img:
            if os.path.exists(i):
                print('\U0001f44d' + str(i))
            else:
                print('ERROR | No '+str(i) + ' found. Please obtain the bobber.png and restart.')
                exit('bobber error')
        if os.path.exists('settings.ini'):
            print('\U0001f44d' + ' Found settings.ini')
        else:
            print('ERROR | No settings.ini found. Please obtain the settings file and restart.')
            exit('settings error')
        f = open('first_run.txt','w')
        f.write('ran = true')
        f.close()



#Saves settings to settings.ini
def save_settings(sender,data):
    fp = open('settings.ini')
    p = configparser.ConfigParser()
    p.read_file(fp)
    p.set('Settings', 'game_resolution', str(resolution))
    p.set('Settings', 'volume_threshold', str(max_volume))
    p.set('Settings','tracking_zone',str(screen_area))
    p.set('Settings', 'bait_inventory', str(coord_bait))
    p.set('Settings','detection_threshold',str(detection_threshold))
    p.set('Settings','launch_time',str(dist_launch_time))
    p.set('Settings','cast_time',str(cast_time))
    p.set('Settings','food_time',str(food_time))
    p.set('Settings','max_catch_time',str(max_catch_time))
    p.write(open(f'Settings.ini', 'w'))
    log_info(f'Saved New Settings to settings.ini',logger="Information")

#Settings for DearPyGui window
set_main_window_size(600,500)
set_style_window_menu_button_position(0)
set_theme("Gold")
set_global_font_scale(1)
set_main_window_resizable(False)

#Creates the DearPyGui Window
with window("Fisherman Window",width = 600,height = 500):
    set_window_pos("Fisherman Window",0,0)
    add_input_int("Amount Of Spots",max_value=10,min_value=0,tip = "Amount of Fishing Spots")
    add_input_int("Set Volume Threshold",max_value=100000,min_value=0,default_value=int(max_volume),callback = save_volume ,tip = "Volume Threshold to trigger catch event")
    add_input_float("Set Detection Threshold",min_value=0.1,max_value=2.5,default_value=detection_threshold,callback=save_threshold)
    #add_spacing(count = 3)
    add_slider_float("Set Time Lauch Distance",min_value=0.3,max_value=1.0,default_value=dist_launch_time,callback=save_dist_launch_time, tip = "Time to determine the launch distance")
    add_slider_int("Set Cast Time",min_value=1,max_value=60,default_value=int(cast_time),callback= save_cast_time, tip = "time to determine how long without getting fish")
    add_slider_int("Set Food Time",min_value=1,max_value=60,default_value=int(food_time),callback= save_food_time, tip = "time to use food. Is minutes")
    add_slider_int("Set Max Catch Time",min_value=1,max_value=60,default_value=int(max_catch_time),callback= save_max_catch_time, tip = "Maxmimum time before releasing the rod. Useful if fish can't be caught.")
    add_listbox("Set Game Resolution", items=resolutions, default_value=int(resolution),callback=save_resolution)
    add_spacing(count = 3)
    add_button("Set Fishing Spots",width=130,callback=generate_coords,tip = "Starts function that lets you select fishing spots")
    add_same_line()
    add_button("Set Tracking Zone",callback=Grab_Screen,tip="Sets zone bot tracks for solving fishing minigame")
    add_same_line()
    add_button("Set Bait Inventory",callback=bait_coords,tip="Sets zone bot bait inventory")
    add_spacing(count = 5)
    add_button("Start Bot",callback=start,tip = "Starts the bot. Or press f1")
    add_same_line()
    add_button("Stop Bot",callback = stop,tip = "Stops the bot. Or press f2")
    add_same_line()
    add_button("Save Settings",callback=save_settings,tip = "Saves bot settings to settings.ini")
    add_spacing(count = 5)

    add_logger("Information",log_level=0)
    log_info(f'Loaded Settings. Volume Threshold:{max_volume},Tracking Zone:{screen_area},Launch Time: {dist_launch_time}, Cast Time: {cast_time},Debug Mode:{debugmode}',logger="Information")

Setup()
threading.Thread(target = Setup_title).start()
start_dearpygui()
