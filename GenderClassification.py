# Import Dependencies
import cv2
import os
import numpy as np
import warnings
from keras.utils import np_utils
from keras.models import Sequential, load_model
from keras.layers import Dense,Activation,Flatten,Dropout
from keras.layers import Conv2D, MaxPooling2D
from keras.callbacks import ModelCheckpoint
from sklearn.model_selection import train_test_split

data_path   = 'datasets'
# Categories in the folder
categories  = os.listdir(data_path)
labels      = [ i for i in range(len(categories))]
# Dictionary files are created by the zip folder
label_dict  = dict(zip(categories,labels))

# print(label_dict) # to: {'female': 0, 'male': 1}
# print(categories) # to: ['female', 'male']
# print(labels)     # to: [0, 1]

img_size = 32
data     = []
target   = []

# facial detection
cascade  = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


for category in categories:
    folder_path   = os.path.join(data_path,category)
    img_names     = os.listdir(folder_path)
#picking from the categories
    for img_name in img_names:
        img_path    = os.path.join(folder_path,img_name)
        img         = cv2.imread(img_path)
        faces       = cascade.detectMultiScale(img)

        try:
            for f in faces:
                # Detect co-ordinates
                x,y,w,h   = [v for v in f]
                # Cut the co-ordinate of the picture
                sub_face  = img[y:y+h, x:x+w]
                # Convert the picture into gray scale
                gray      = cv2.cvtColor(sub_face, cv2.COLOR_BGR2GRAY)
                # Cut down the image into 32bytes x 32bytes
                resized   = cv2.resize(gray, (img_size,img_size))
                # Append to data list
                data.append(resized)
                # Append to target list
                target.append(label_dict[category])
        except Exception as e:
            print('Exception:',e)

warnings.filterwarnings('ignore')
# Convert into the range, 0 and 1
data  = np.array(data)/255.0
data  = np.reshape(data, (data.shape[0],img_size,img_size,1))
target= np.array(target)

new_target  = np_utils.to_categorical(target)

# Saving to the folder; training
np.save('./training/data', data)
np.save('./training/target', new_target)

data   = np.load('./training/data.npy')
target = np.load('./training/target.npy')

# Creating Model
noOfFilters    = 64
sizeOfFilter1  = (3,3)
sizeOfFilter2  = (3,3)
sizeOfPool     = (2,2)
noOfNode       = 64

# Defining the model
model = Sequential()

#Adding Layers
model.add((Conv2D(32, sizeOfFilter1, input_shape=data.shape[1:], activation='relu')))
model.add((Conv2D(32, sizeOfFilter1, activation='relu'))) 
model.add(MaxPooling2D(pool_size=sizeOfPool))

model.add((Conv2D(64, sizeOfFilter2, activation='relu')))
model.add((Conv2D(64, sizeOfFilter2, activation='relu')))
model.add(MaxPooling2D(pool_size=sizeOfPool))
model.add(Dropout(0.5))

model.add(Flatten()) #For the Linear Format
model.add(Dense(noOfNode,activation='relu'))
model.add(Dropout(0.5))
# (Female and male) classes number softmax-helps in binary classification
model.add(Dense(2, activation='softmax')) 

#Compiling the general model 
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# Seperate data into train and test data
train_data, test_data, train_target, test_target = train_test_split(data,target,test_size=0.1)

# Checkpoint initialization(saving each model  in training folder)
checkpoint  = ModelCheckpoint('./training/model-{epoch:03d}.model', monitor='val_loss', verbose=0, save_best_only=True, mode='auto')
history     = model.fit(train_data, train_target, epochs=30, callbacks=[checkpoint], validation_split=0.2)

# Loading a model from the training folder
model       = load_model('./training/model-010.model')
# Face detect
face_clsfr  = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
# opencv video capture
cap         = cv2.VideoCapture(0)

label_dict  = {0:'Female', 1:'Male'}
color_dict  = {0:(0,0,255),1:(0,255,0)}

while True:

    ret,img = cap.read()
    gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces   = face_clsfr.detectMultiScale(gray,1.3,3)

    for (x,y,w,h) in faces:
        face_img   = gray[y:y+w, x:x+w]
        resized    = cv2.resize(face_img, (32,32))
        normalized = resized/255.0
        reshaped   = np.reshape(normalized, (1,32,32,1))

        # Predicting the results 
        result     = model.predict(reshaped)
        # Helps to give output
        label      = np.argmax(result,axis=1)[0]

        # Rectangle of our faces
        cv2.rectangle(img, (x,y), (x+w, y+h), color_dict[label],2)
        # Rectangle of label
        cv2.rectangle(img, (x,y-40), (x+w,y), color_dict[label], -1)
        cv2.putText(img, label_dict[label], (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

    cv2.imshow('Result', img)
    k  = cv2.waitKey(1)

    if k == ord("q"):
        break

cv2.destroyAllWindows()
cap.release()



 



            
