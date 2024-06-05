from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect   
import time
import random
import serial
import math

async_mode = None

app = Flask(__name__)
app.config['DEBUG'] = True

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 

ser = None

#ser = serial.Serial("/dev/ttyS0", 9600)
 
 
def background_thread(args):
    count = 0       
    dataList = [] 
    povol = 1
    A = 'Null'
    btnV = 'Null'
    prep = 'Null'
    global ser
            
    while True:
        print(args)
        
        if args:
            A = dict(args).get('A')
            btnV = dict(args).get('btn_value')
            prep = dict(args).get('dir_value')
        else:
            btnV = 'Null'

        if povol == 1:
            ser = serial.Serial("/dev/ttyS0", 9600)
            time.sleep(1) 
            povol = 0
 
        #die("diestring endit")
        #socketio.sleep(0.7)
        count += 1
        
        Uart = ser.readline().strip().decode('utf-8')
        value = Uart.split(',')
        
        try:
            but = int(value[0])   
            hodpot1 = int(value[1])
            hodpot2 = int(value[2])
        except IndexError:
            print("Index out of range, skipping assignment.")
            print(value)
            
        if(btnV == "start"):
            print(f"UART Data: {Uart}")
            socketio.emit('my_response', {'BUT':but,'POT1': hodpot1, 'POT2':hodpot2, 'count': count}, namespace='/test')
        else:
            time.sleep(0.1)
          
            
            
@app.route('/')
def index():
    return render_template('Tabs.html', async_mode=socketio.async_mode)

@socketio.on('click_event', namespace='/test')
def handle_angle_event(message):   
    global ser
    if ser:
        ser.write(f"{message['value']}\n".encode())
        time.sleep(2.2)
    else:
        print("Serial not defined")

 
 
@socketio.on('click_start', namespace='/test')
def handle_start(message):   
    session['btn_value'] = message['value'] 

@socketio.on('click_stop', namespace='/test')
def handle_stop(message):   
    session['btn_value'] = message['value']   
    
    
    
@socketio.on('rot_event', namespace='/test')
def handle_event(message):
    session['dir_value'] = message['value']
    global ser
    if ser:
        if message['value'] == "right":
            print("Otočenie 180 stupnov")
            ser.write(f"{202}\n".encode()) 
            time.sleep(3)
        else:
            print("Otočenie 0 stupnov")
            ser.write(f"{204}\n".encode()) 
            time.sleep(3)
    else:
        print("Serial not defined")    
    
    
@socketio.on('set_servo', namespace='/test')
def handle_servo(message):
    session['ser_value'] = message['value']
    global ser
    if ser:
        ser.write(f"{message['value']}\n".encode())
        time.sleep(4)
    else:
        print("Serial not defined")
        
 
@socketio.on('disconnect_request', namespace='/test')
def handle_disconnect_request():
    emit('my_response', {'state': 'Disconnected!'})
    #session['receive_count'] = session.get('receive_count', 0) + 1
    #emit('my_response', {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()



@socketio.on('connect', namespace='/test')
def handle_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
#    emit('my_response', {'data': 'Connected', 'count': 0})
   

@socketio.on('disconnect', namespace='/test')
def handle_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug = True)
