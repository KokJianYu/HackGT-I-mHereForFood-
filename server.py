from flask import Flask, Response,render_template, request
from flask_cors import CORS
from multiprocessing import Manager
import flask
import pyaudio
import wave
import time

import threading  
import datetime

currVolume = 0

import socket
IP = socket.gethostbyname(socket.gethostname())
SPEAKER_IP = 'http://192.168.1.251:8090'

app = Flask(__name__)
CORS(app)

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024

audio1 = pyaudio.PyAudio()

""" 
Some util methods
"""
def milliseconds_to_readable_date(millis):
    date_string = datetime.datetime.fromtimestamp(int(millis)//1000)
    return date_string.strftime("%Y-%m-%d %X")

def date_string_to_milliseconds(date_string):
    return int(datetime.datetime.strptime(date_string, "%Y-%m-%d %X").timestamp()*1000)

def schedule_reminder(filename, extension, volume):
    filename_with_extension = filename + extension
    reminder_time_millis = date_string_to_milliseconds(filename)

    import sched, time

    def play_reminder():
      import os
      if not os.path.exists("reminders/" + filename_with_extension):
        return

      import requests
      xml = "<play_info><app_key>CMwhZOwJsgUUclRmJ7k8dpv2KF2F8Qgr</app_key><url>http://" + IP + ":5000/get_reminder/" + filename_with_extension.replace(" ", "%20") + "</url><service>service text</service><reason>reason text</reason><message>message text</message><volume>" + str(volume) + "</volume></play_info>"
      print(xml)
      headers = {'Content-Type': 'application/xml'} # set what your server accepts
      requests.post(SPEAKER_IP + '/speaker', data=xml, headers=headers)

    print("Scheduling", filename_with_extension, "...")

    # Set up scheduler
    s = sched.scheduler(time.time, time.sleep)
    # Schedule when you want the action to occur
    s.enterabs(float(reminder_time_millis)//1000, 0, play_reminder)
    # Block until the action has been run
    s.run()

def get_current_vol():
    import requests
    global currVolume
    response = requests.get(SPEAKER_IP + '/volume').content.decode('utf-8')
    currVolume = int(response.split("<actualvolume>")[1].split("</actualvolume>")[0])

"""
Livestream
"""
def genHeader(sampleRate, bitsPerSample, channels):
    datasize = 2000*10**6
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o

@app.route('/audio')
def audio():
   
    def sound():
        CHUNK = 1024
        sampleRate = 44100
        bitsPerSample = 16
        channels = 2
        wav_header = genHeader(sampleRate, bitsPerSample, channels)

        # stream = audio1.open(format=FORMAT, channels=CHANNELS,
        #                     rate=RATE, input=True,
        #                     frames_per_buffer=CHUNK)
        # data = wav_header + stream.read(CHUNK)
        # for i in range(10):
        #     while len(queue) == 0:
        #         pass
        #     queue.pop(0)

        while len(queue) == 0:
            pass

        data = wav_header + queue.pop(0)
        
        while True:
            if len(queue) == 0:
                continue
            yield (data)
            data = queue.pop(0)

    return Response(sound())

@app.route('/goLive')
def goLive():
    import requests

    # time.sleep(1)
    xml = "<play_info><app_key>CMwhZOwJsgUUclRmJ7k8dpv2KF2F8Qgr</app_key><url>http://" + IP + ":5000/audio</url><service>service text</service><reason>reason text</reason><message>message text</message><volume>35</volume></play_info>"
    headers = {'Content-Type': 'application/xml'} # set what your server accepts
    requests.post(SPEAKER_IP + '/speaker', data=xml, headers=headers)

    response = flask.Response("ok")
    #headers = {'Content-Type': 'application/xml'} # set what your server accepts
    # response.headers["Referrer-Policy"] = "unsafe-url"
    return response

@app.route('/stopLive')
def stopLive():
    import requests

    # time.sleep(1)
    xml = "<key state=\"press\" sender=\"Gabbo\">NEXT_TRACK</key>"
    headers = {'Content-Type': 'application/xml'} # set what your server accepts
    requests.post(SPEAKER_IP + '/key', data=xml, headers=headers)

    response = flask.Response("ok")
    queue = manager.list()
    #headers = {'Content-Type': 'application/xml'} # set what your server accepts
    # response.headers["Referrer-Policy"] = "unsafe-url"
    return response

@app.route('/volumeUp')
def volumeUp():
    import requests
    global currVolume
    currVolume += 5
    xml = "<volume>" + str(currVolume) + "</volume>"
    headers = {'Content-Type': 'application/xml'} # set what your server accepts
    requests.post(SPEAKER_IP + '/volume', data=xml, headers=headers)
    response = flask.Response("ok")
    return response

@app.route('/volumeDown')
def volumeDown():
    import requests
    global currVolume
    currVolume -= 5
    xml = "<volume>" + str(currVolume) + "</volume>"
    headers = {'Content-Type': 'application/xml'} # set what your server accepts
    requests.post(SPEAKER_IP + '/volume', data=xml, headers=headers)
    response = flask.Response("ok")
    return response

@app.route('/live', methods=['POST'])
def live():
    # print("received audio")
    data = request.data
    # print(data)
    f = open('test.wav', 'wb')
    f.write(data)
    f.close()
    wf = wave.open('test.wav', 'rb')
    chunk = wf.readframes(wf.getnframes())
    wf.close()
    queue.append(chunk)
    response = flask.Response("ok")
    #headers = {'Content-Type': 'application/xml'} # set what your server accepts
    # response.headers["Referrer-Policy"] = "unsafe-url"
    return response

@app.route('/')
def index():
    return render_template('index.html')

"""
Route to render the main UI of the app
"""
@app.route('/ui')
def ui():
    # if request.url.startswith('http://'):
    #     url = request.url.replace('http://', 'https://', 1).replace("5000", "5001", 1)
    #     code = 301
    #     return flask.redirect(url, code=code)
    return render_template('ui.html')

"""
Route to render the live UI of the app
"""
@app.route('/live_ui')
def live_ui():
    # if request.url.startswith('http://'):
    #     url = request.url.replace('http://', 'https://', 1).replace("5000", "5001", 1)
    #     code = 301
    #     return flask.redirect(url, code=code)
    return render_template('live.html')

"""
Route to get list of reminder file names
"""
@app.route('/get_all_reminders')
def get_all_reminders():
    import os, time
    all_recordings = []
    # List all files in a directory using os.listdir
    basepath = 'reminders/'
    for entry in os.listdir(basepath):
        if os.path.isfile(os.path.join(basepath, entry)):
            date_string = entry[0:-4]
            millis = date_string_to_milliseconds(date_string)
            millis_now = time.time()*1000
            if millis > millis_now:
                # pending reminder, add to all recordings
                all_recordings.append(entry)
            else:
                # already expired reminder, just remove
                os.remove("reminders/" + entry)
    myDict = {"recordings": all_recordings}
    return myDict

"""
Route to get mp3 or wav file of your reminder, given filename (either text-to-speech or recorded)
"""
@app.route('/get_reminder/<name>')
def get_reminder(name):
    return flask.send_file("reminders/" + name)

"""
Route to delete reminder
"""
@app.route('/delete_reminder/<name>', methods=['POST'])
def delete_reminder(name):
    import os
    os.remove("reminders/" + name)
    return "File Removed!"

"""
Route to send recording from client
"""
@app.route('/send_recording', methods=['POST'])
def send_recording():
    print("Received recording from client.")
    time = request.headers["time"]
    volume = request.headers["volume"]
    data = request.data
    filename = str(milliseconds_to_readable_date(time))

    f = open("reminders/" + filename + ".wav", 'wb')
    f.write(data)
    f.close()

    schedule_reminder(filename, ".wav", volume)

    return "Recording received, reminder scheduled."

"""
Route to send text for text-to-speech
"""
@app.route('/send_text', methods=['POST'])
def send_text():
    print("Received text from client.")
    mytext = request.form.get('text')
    mytime = request.form.get('time')
    myvolume = request.form.get('volume')

    from gtts import gTTS  
    import time

    myobj = gTTS(text=mytext, lang='en', slow=False)
    filename = str(milliseconds_to_readable_date(mytime))
    myobj.save("reminders/" + filename + ".mp3")

    schedule_reminder(filename, ".mp3", myvolume)

    return "Text received, reminder scheduled."

def http_app(q):
    global queue
    queue = q
    app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False, port=5000)
    #app.run(host='0.0.0.0', debug=True, threaded=True, port=5001, ssl_context=("ssl/domain.crt", "ssl/domain.key"))

if __name__ == "__main__":
    from multiprocessing import Process
    manager = Manager()
    q = manager.list()
    Process(target=http_app,daemon=True, args=(q,)).start()
    queue = q
    get_current_vol()
    app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False, port=5001, ssl_context=("ssl/domain.crt", "ssl/domain.key"))
