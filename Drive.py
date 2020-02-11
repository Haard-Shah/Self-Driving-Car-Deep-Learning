import socketio
import eventlet
from flask import Flask
from keras.models import load_model
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import cv2

sio = socketio.Server() # our model is not on the server and the client (sim) will be listening to it
  
speed_limit = 10

# define App
app = Flask(__name__) # '__main__'

def img_preprocess(img):

  # Focuse the image onto the road only **
  img = img[60:135, :, :]
  
  # YUV color space
  img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)

  # Smoothing of the image
  img = cv2.GaussianBlur(img, (3, 3), 0)

  # resize
  img = cv2.resize(img, (200, 66))

  # normalise
  img = img/255

  return img

@sio.on('telemetry') # event handler - listening to event from client with id telemetry
def telemetry(sid, data):
    speed = float(data['speed'])
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    image = np.asarray(image)
    image = img_preprocess(image)
    image = np.array([image])

    steering_angle = float(model.predict(image))
    throttle = 1.0 - speed/speed_limit

    print('{} {} {}'.format(steering_angle, throttle, speed))

    send_control(steering_angle, 1.0) # send the command



@sio.on('connect') # message, disconnect are reseved
def connect(sid, environ):
    print('Connected')
    send_control(0, 0)

def send_control(steering_angle, throttle):
    sio.emit('steer', data = {
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })

if __name__ == '__main__':
    model = load_model('model_1.h5')
    app = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)
