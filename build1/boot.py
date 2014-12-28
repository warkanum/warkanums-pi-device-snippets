#!/usr/bin/python3
from threading import Thread

import RPi.GPIO as GPIO
import time
import datetime
import os
import sys
import dht11_sensor
import psycopg2

###-----------------Hardware Settings-----------------------

PIN_LC=25 #Light Sensor  (GPIO.IN,  pull_up_down=GPIO.PUD_UP)
PIN_MC=17 #Motion Sensor (GPIO.IN, pull_up_down=GPIO.PUD_UP)
PIN_TC=4  #Temp Sensor  (GPIO.IN, pull_up_down=GPIO.PUD_UP) 
PIN_TC_WP=7 #Temp Sensor #Wirepi pin 7
PIN_LED1=23 #LED Blue 1
PIN_LED2=24 #LED Blue 2


###------------------SQL Settings-----------------------------
SQL_SRV='127.0.0.1'
SQL_USER='pistats'
SQL_PASSWD='pistats'
SQL_DB='pistats'


#setup pins. Some are setup by functions below.
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_LED1,GPIO.OUT)
GPIO.setup(PIN_LED2,GPIO.OUT)

GPIO.setup(PIN_MC, GPIO.IN, pull_up_down=GPIO.PUD_UP)


#dim leds
GPIO.output(PIN_LED1,GPIO.LOW)
GPIO.output(PIN_LED2,GPIO.LOW)


def UnixLocalEpoch():
    dt = datetime.datetime.now()
    return int((dt - datetime.datetime(1970,1,1)).total_seconds())

def PhotoSensor(RCpin):
  reading = 0
  GPIO.setup(RCpin, GPIO.OUT)
  GPIO.output(RCpin, GPIO.LOW)
  time.sleep(0.1)
   
  GPIO.setup(RCpin, GPIO.IN)
  # This takes about 1 millisecond per loop cycle
  while (GPIO.input(RCpin) == GPIO.LOW):
    reading += 1
    
  return reading

def TempsensorRead():
    ### Loop through the temp sensor library until we get a valid reading ###

    for i in range(1,100):
        data = dht11_sensor.read(PIN_TC_WP)
        #print('Temp={0}*C  Humidity={1}%  Status={2}  Error={3}'.format(data['temperature'], data['humidity'], data['valid'], data['err']))
        if data['valid'] == 1:
            validData = data
            break

    if validData:
        return validData

    return None

def save_data(p_SensorValues):
    try:
        sql_con = psycopg2.connect(host=SQL_SRV, user=SQL_USER,password=SQL_PASSWD,database=SQL_DB)
        sql_cur = sql_con.cursor()

        if p_SensorValues.get('motion', None):
            sql_cur.execute("""select id, data_read from sensordata 
                where sensor_type = 'motion' and time_read > extract(epoch from now())::bigint - 240
                order by time_read desc limit 1""")
            data = sql_cur.fetchone()
            if not data or (data and str(data[1]) != str(p_SensorValues['motion']['data'])):
                sql_cur.execute("INSERT INTO sensordata (sensor_type, data_read, time_read) VALUES (%s, %s, %s)",
                     ('motion', p_SensorValues['motion']['data'], p_SensorValues['motion']['read'] ))
        
        if p_SensorValues.get('motion', None):
            sql_cur.execute("select id, data_read from sensordata where sensor_type = 'humanpresence' order by time_read desc limit 1")
            data = sql_cur.fetchone()
            if not data or (data and str(data[1]) != str(p_SensorValues['motion']['humanpresence'])):
                sql_cur.execute("INSERT INTO sensordata (sensor_type, data_read, time_read) VALUES (%s, %s, %s)",
                     ('humanpresence', p_SensorValues['motion']['humanpresence'], p_SensorValues['motion']['read'] ))

        if p_SensorValues.get('light', None):
            sql_cur.execute("select id, data_read from sensordata where sensor_type = 'light' order by time_read desc limit 1")
            data = sql_cur.fetchone()
            #we have a +- 10 variance on light.
            if not data or (data and (int(p_SensorValues['light']['data']) > int(data[1])+10 or int(p_SensorValues['light']['data']) < int(data[1]) - 10)  ):
                sql_cur.execute("INSERT INTO sensordata (sensor_type, data_read, time_read) VALUES (%s, %s, %s)",
                     ('light', p_SensorValues['light']['data'], p_SensorValues['light']['read'] ))
        
        if p_SensorValues.get('temperature', None):
            sql_cur.execute("select id, data_read from sensordata where sensor_type = 'temperature' order by time_read desc limit 1")
            data = sql_cur.fetchone()
            if not data or (data and str(data[1]) != str(p_SensorValues['temperature']['temperature'])):
                sql_cur.execute("INSERT INTO sensordata (sensor_type, data_read, time_read) VALUES (%s, %s, %s)",
                     ('temperature', p_SensorValues['temperature']['temperature'], p_SensorValues['temperature']['read'] ))

        if p_SensorValues.get('temperature', None):
            sql_cur.execute("select id, data_read from sensordata where sensor_type = 'humidity' order by time_read desc limit 1")
            data = sql_cur.fetchone()
            if not data or (data and str(data[1]) != str(p_SensorValues['temperature']['humidity'])):
                sql_cur.execute("INSERT INTO sensordata (sensor_type, data_read, time_read) VALUES (%s, %s, %s)",
                     ('humidity', p_SensorValues['temperature']['humidity'], p_SensorValues['temperature']['read'] ))

        sql_con.commit()
        sql_cur.close()
        sql_con.close()
    
    except psycopg2.Error as e:
        print("SQL error in save_data: " + str(e))

    except Exception as e:
        print("Unknown error in save_data: " + str(e))
    

def main():
    SensorValue = {}
    CNT_LT = 99 #light check delay counter
    CNT_TMP = 999 #temp check delay counter

    while True:
      CNT_LT += 1
      CNT_TMP += 1
      changed = False

      motionData = GPIO.input(PIN_MC)
      if not SensorValue.get('motion', None):
          SensorValue['motion'] = {'data': motionData , 'read': UnixLocalEpoch(), 'changed': UnixLocalEpoch()}
      else:
          if SensorValue['motion'].get('data', 0) != motionData :
            changed = True
            SensorValue['motion']['changed'] = UnixLocalEpoch()

          SensorValue['motion']['data'] = motionData
          SensorValue['motion']['read'] = UnixLocalEpoch()
        

      if (SensorValue['motion']['data'] > 0):
        GPIO.output(PIN_LED1,GPIO.HIGH)  #flash led
        SensorValue['motion']['lastmotion'] = UnixLocalEpoch()
      else:
        GPIO.output(PIN_LED1,GPIO.LOW) #flash led stop
  
      #see if there are a moving presence in the room
      if SensorValue.get('motion', None):
          if (SensorValue['motion'].get('lastmotion', 0) > UnixLocalEpoch() - 60):
            SensorValue['motion']['humanpresence'] = 1
          else:
            SensorValue['motion']['humanpresence'] = 0
  
      #Measure Light
      if not SensorValue.get('light', None):
          SensorValue['light'] = {'data': PhotoSensor(PIN_LC) , 'read': UnixLocalEpoch() } 

      if (CNT_LT > 100):
         CNT_LT = 0 
         lightData = PhotoSensor(PIN_LC) 
         if SensorValue['light'].get('data', 0) != lightData :
            changed = True
            SensorValue['light']['changed'] = UnixLocalEpoch()
         SensorValue['light']['data'] = lightData
         SensorValue['light']['read'] = UnixLocalEpoch()

      #Measure  Temprature, this might hold the thread for a few seconds at most.
      if (CNT_TMP > 1000):
         CNT_TMP = 0 
         print('temperature reading...')
         if not SensorValue.get('temperature', None):
             SensorValue['temperature'] = {}

         tempData = TempsensorRead()
         if tempData:
            if (SensorValue['temperature'].get('temperature', 0) != tempData['temperature'] 
            or SensorValue['temperature'].get('humidity', 0) != tempData['humidity']):
                SensorValue['temperature']['changed'] = UnixLocalEpoch()
                SensorValue['temperature']['temperature'] = tempData['temperature']
                SensorValue['temperature']['humidity'] = tempData['humidity']
                changed = True

            SensorValue['temperature']['read'] = UnixLocalEpoch()

      if changed:
          t = Thread(target=save_data, args=(SensorValue,))
          t.start()
      
      time.sleep(0.01)

if __name__ == '__main__':
    sys.exit(main())