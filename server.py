from flask import Flask, Response,render_template, request
import flask
import pyaudio
import wave
import threading  
import datetime

app = Flask(__name__)

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

def schedule_reminder(filename, extension):
    filename_with_extension = filename + extension
    reminder_time_millis = date_string_to_milliseconds(filename)

    import sched, time

    def play_reminder():
      import requests
      xml = "<play_info><app_key>CMwhZOwJsgUUclRmJ7k8dpv2KF2F8Qgr</app_key><url>http://192.168.1.85:5000/get_reminder/" + filename_with_extension + "</url><service>service text</service><reason>reason text</reason><message>message text</message><volume>50</volume></play_info>"
      headers = {'Content-Type': 'application/xml'} # set what your server accepts
      requests.post('http://192.168.1.251:8090/speaker', data=xml, headers=headers)

    print("Scheduling", filename_with_extension, "...")

    # Set up scheduler
    s = sched.scheduler(time.time, time.sleep)
    # Schedule when you want the action to occur
    s.enterabs(float(reminder_time_millis)//1000, 0, play_reminder)
    # Block until the action has been run
    s.run()

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

        stream = audio1.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        data = wav_header + stream.read(CHUNK)
        while True:
            yield (data)
            data = stream.read(CHUNK)

    return Response(sound())

"""
Main route for livestream
"""
@app.route('/')
def index():
    return render_template('index.html')

"""
Route to render the main UI of the app
"""
@app.route('/ui')
def ui():
    return render_template('ui.html')

"""
Route to get list of reminder file names
"""
@app.route('/get_all_reminders')
def get_all_reminders():
    import os
    all_recordings = []
    # List all files in a directory using os.listdir
    basepath = 'reminders/'
    for entry in os.listdir(basepath):
        if os.path.isfile(os.path.join(basepath, entry)):
            all_recordings.append(entry)
    myDict = {"recordings": all_recordings}
    print(myDict)
    return myDict


"""
Route to get mp3 or wav file of your reminder, given filename (either text-to-speech or recorded)
"""
@app.route('/get_reminder/<name>')
def get_reminder(name):
    return flask.send_file("reminders/" + name)

"""
Route to send recording from client
"""
@app.route('/send_recording', methods=['POST'])
def send_recording():
    print("Received recording from client.")
    time = request.headers["time"]
    data = request.data
    filename = str(milliseconds_to_readable_date(time))

    f = open("reminders/" + filename + ".wav", 'wb')
    f.write(data)
    f.close()

    schedule_reminder(filename, ".wav")

    return "Recording received, reminder scheduled."

"""
Route to send text for text-to-speech
"""
@app.route('/send_text', methods=['POST'])
def send_text():
    print("Received text from client.")
    mytext = request.form.get('text')
    mytime = request.form.get('time')

    from gtts import gTTS  
    import time

    myobj = gTTS(text=mytext, lang='en', slow=False)
    filename = str(milliseconds_to_readable_date(mytime))
    myobj.save("reminders/" + filename + ".mp3")

    schedule_reminder(filename, ".mp3")

    return "Text received, reminder scheduled."

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, threaded=True, port=5000)