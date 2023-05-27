import pychromecast
from time import sleep
from flask import Flask, request, render_template

class Queue:
    def __init__(self):
        self.queue = []

    def addFunc(self, func):
        if self.queue and self.queue[-1] == func:
            return
        else:
            self.queue.append(func)

    def tryExecute(self): #doesnt have check if execution fails
        if self.queue:
            self.queue.pop(0)()
    
    def not_empty(self):
        return bool(self.queue)

class Listener:
    def __init__(self, mediaFunc=None, connectionFunc=None):
        self.mediaFunc = mediaFunc
        self.connectionFunc = connectionFunc

    def new_media_status(self, data):
        if self.mediaFunc is not None:
            self.mediaFunc(data)

    def new_connection_status(self, data):
        if self.connectionFunc is not None:
            self.connectionFunc(data)

class Chromecast:
    def __init__(self, device):
        self.device = device
        self.cast = None
        self.mc = None
        self.chromecasts = None
        self.browser = None
        self.url = None
        self.newUrl = False
        self.isProcessing = False
        self.turnBackOn = False
        self.expectedStatus = "UNKNOWN"
        self.commandQueue = Queue()
        self.listener = Listener(self.new_media_status_handler, self.new_connection_status_handler)
        self.connect()

    #RANDOM FUNCTIONS
    def waitUntilTrue(self, variable, timeout, period):
        while not eval(variable) and timeout > 0:
            timeout -= period
            sleep(period)


    #LISTENER HANDLER
    def new_media_status_handler(self, data):
        print("NEW STATUS: ", data.player_state)

    def new_connection_status_handler(self, data):
        print("NEW CONNECTION STATUS: ", data)
    
        #Turn back on after disconnect
        if self.cast is not None:
            if self.turnBackOn and data.status == "CONNECTED":
                self.turnBackOn = False
                self.connect()
                self.play()

        if data.status == "LOST" and self.expectedStatus == "PLAYING":
            self.turnBackOn = True


    #CHROMECAST
    def connect(self, tries=0):
        if self.isProcessing:
            return

        self.processing(True)
        try:
            self.disconnect()
        except:
            print("disconnect unsuccessful")
        chromecasts, self.browser = pychromecast.get_listed_chromecasts(friendly_names=[self.device])
        print(chromecasts)
        if not chromecasts:
            print(f'No chromecast with name "{self.device}" discovered {tries + 1}')
            tries += 1
            if tries > 5:
                self.processing(False)
                return
            self.connect(tries=tries)
            return

        self.cast = chromecasts[0]
        self.cast.wait()
        print('Chromecast ready')
        self.mc = self.cast.media_controller
        self.cast.socket_client.register_connection_listener(self.listener)
        self.mc.register_status_listener(self.listener)
        self.processing(False)

    def setMedia(self):
        if self.isProcessing:
            return

        if self.checkConnection() and self.url is not None:
            self.processing(True)
            self.newUrl = False
            
            self.mc.play_media(self.url, 'audio/mp3', stream_type="LIVE", autoplay=False)
            self.mc.block_until_active()
            print("Trying to play: ", self.url)

            if self.mc.status.player_is_paused:
                self.waitUntilTrue('self.mc.status.player_is_idle', 15, 0.01)
            
            self.waitUntilTrue('self.mc.status.player_is_paused', 30, 0.01)
            print("UNBLOCKED")
            self.processing(False)

    def processing(self, bool):
        if bool:
            self.isProcessing = True
        else:
            self.isProcessing =  False

    def checkConnection(self):
        if self.cast is None:
            self.connect()

        if self.cast.socket_client.is_stopped:
            print('No chromecast connected, trying to connect')
            self.connect()
            if self.cast.socket_client.is_stopped:
                print('Connection unsuccessful')
                return False
        return True
    
    def checkMedia(self):
        if self.mc is None:
            return False

        if self.mc.status.player_state == "UNKNOWN" or self.mc.status.player_is_idle or self.newUrl:
            print('No or new media, setting up')
            self.setMedia()
            if self.mc.status.player_state == "UNKNOWN":
                print('media setup unsuccessful')
                return False
        return True

    def checkProcessing(self, command=None):
        if self.isProcessing:
            if command is not None:
                self.commandQueue.addFunc(command)
            return True
        return False

    def checkAll(self, command=None):
        processing = self.checkProcessing(command)
        if processing:
            return False

        return self.checkConnection() and self.checkMedia()


    def setUrl(self, url):
        if self.url != url:
            self.url = url
            self.newUrl = True

    #chromecast control functions
    def pause(self):
        if self.checkAll(self.pause):
            print('pausingg')
            self.mc.pause()
            self.expectedStatus = "PAUSED"
            self.commandQueue.tryExecute()
    
    def play(self):
        self.newUrl = True  #to always set new media and so radio is live
        if self.checkAll(self.play):
            self.mc.play()
            self.expectedStatus = "PLAYING"
            self.commandQueue.tryExecute()

    def stop(self):
        if self.checkAll(self.stop):
            self.mc.stop()
            self.expectedStatus = "IDLE"
            self.commandQueue.tryExecute()

    def setVolume(self, value):
        if self.checkAll():
            self.cast.set_volume(value/100)
            #after disconnect doesnt resume playback (not implemented)

    def disconnect(self):
        self.cast.disconnect()

    def connectNew(self):
        self.connect()


    def is_playing(self):
        if self.checkConnection():
            self.waitUntilTrue('self.mc.status.player_state != "UNKNOWN"', 2, 0.01)
            if self.mc.status.player_is_playing:
                return True
        return False

    def get_url(self):
        return self.url
    
    def get_volume(self):
        if self.checkConnection():
            return self.cast.status.volume_level
        return -1


#FLASK
app = Flask("SmartHomeRadio")

@app.route("/")
def index():
    return render_template('RadioGui.html')

@app.route("/chromecast", methods=["POST"])
def ajax():
    action = request.form.get('action')
    print(f'{action} command received')

    if action == 'url':
        chromecast.setUrl(request.form.get('url'))
    
    elif action == 'play':
        chromecast.play()
    
    elif action == 'pause':
        chromecast.pause()

    elif action == 'stop':
        chromecast.stop()

    elif action == 'volume':
        chromecast.setVolume(float(request.form.get("value")))

    elif action == 'disconnect':
        chromecast.disconnect()

    elif action == 'connect':
        chromecast.connectNew()

    else:
        return ('Bad Data', 400)

    print('')
    return "Success"

@app.route("/setup", methods=["GET"])
def setup():
    data = {
        "is_playing": chromecast.is_playing(),
        "url": chromecast.get_url(),
        "volume": round(chromecast.get_volume()*100)}
    return data


#OTHER
chromecast = Chromecast("Audio-Pracovna")


# "Audio-Pracovna" 
# 'https://stream.funradio.sk:18443/fun192.mp3'
# 'https://stream.bauermedia.sk/rock-hi.mp3'
# 'https://stream.bauermedia.sk/europa2-hi.mp3?aw_0_req.gdpr=false'
# 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4'
# 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4'