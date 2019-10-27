# Streaming and Reminders with BOSE!
## For HackGT 2019

This is a repo for HackGT 2019 hackathon event. 

Building an application utilizing Bose SoundTouch API.

## Pre-requisites

This application is built with Python 3.7.4. It is recommended that you are using Python version 3 with a virtual environment. 

Bose Soundtouch APIs only work in a local network setting. Ensure that your speaker and your device is connected to the same network.

## Install and run 

Run the following commands

```
git clone --single-branch --branch local-release https://github.com/KokJianYu/HackGT-I-mHereForFood-.git
pip install -r requirements.txt
python server.py
```

Navigate to `localhost:5000` on your web browser. You should be able to see the UI.

## Features

### Record a reminder!

1. Choose a date and time for your reminder.
2. Click on "Record", speak into your device and click "Stop" when done. 
3. Reminder will be scheduled, and you should see it under "Pending Reminders"
4. Reminder will play on speaker at scheduled timing.

### Write a reminder!

1. Choose a date and time for your reminder.
2. Type in a text you want to save as a reminder, and click "Send". 
3. Reminder will be scheduled, and you should see it under "Pending Reminders"
4. Reminder will play on speaker at scheduled timing.

### Try out live streaming audio!

1. Click on "Live Streaming" and you will be directed to another page.
2. Simply click the record button to start live streaming audio to your speakers!