import os
import time
import csv
import datetime as dt
import smbus
#import paho.mqtt.client as mqtt
#import paho.mqtt.publish as publish
import json
from tkinter import *
from tkinter.messagebox import *
import threading

#used for graphing features
import numpy as np
import matplotlib.pyplot as plt
import csv
from collections import defaultdict

#used for Sensor Alert Hardware
import RPi.GPIO as GPIO

###################################################################
# TMP117 sensor with temperature
##################################################################
class TMP117Sensor(object):
    tmp117_temp_max_value = 25
    
    i2c_ch = 1
    # TMP117 address on the I2C bus
    i2c_address = 0x48
    # Register addresses
    reg_temp = 0x00
    reg_config = 0x01
    # Initialize I2C (SMBus)
    bus = smbus.SMBus(i2c_ch)
    
    def init_i2c_smbus(self):   
        # Read the CONFIG register (2 bytes)
        val = TMP117Sensor.bus.read_i2c_block_data(TMP117Sensor.i2c_address, TMP117Sensor.reg_config, 2)
        print("Old CONFIG:", val)
        #val2 = bus.read_i2c_block_data(i2c_address2, reg_config2, 2)
        # Set to 4 Hz sampling (CR1, CR0 = 0b10)
        val[1] = val[1] & 0b00111111
        val[1] = val[1] | (0b10 << 6)

        # Write 4 Hz sampling back to CONFIG
        TMP117Sensor.bus.write_i2c_block_data(TMP117Sensor.i2c_address, TMP117Sensor.reg_config, val)

        # Read CONFIG to verify that we changed it
        val = TMP117Sensor.bus.read_i2c_block_data(TMP117Sensor.i2c_address, TMP117Sensor.reg_config, 2)
        print("New CONFIG:", val)
        
    # Read temperature registers and calculate Celsius from the TMP117 sensor
    def read_temp(self):
        # Read temperature registers
        val = TMP117Sensor.bus.read_i2c_block_data(TMP117Sensor.i2c_address, TMP117Sensor.reg_temp, 2)
        temp_c = (val[0] << 8) | (val[1] )
        # Convert registers value to temperature (C)
        temp_c = temp_c * 0.0078125

        return temp_c
    # write header to csv file
    def write_csv_header(self, filename, header1, header2):
        with open(filename, mode = 'w') as f:
            f_writer = csv.writer(f, delimiter = ',')
            f_writer.writerow([header1, header2])
     
    # write data to csv file
    def write_csv_data(self, filename, t_data, time_data):
        with open(filename, mode = 'a') as f:
            f_writer = csv.writer(f, delimiter = ',')
            f_writer.writerow([t_data, time_data])
    
    # check if temperature cross max value
    def check_cross_max(self):
        if self.read_temp() > TMP117Sensor.tmp117_temp_max_value :
            return True
        else:
            return False

#############################################################################
# SHTC3 sensor with temparature and humidity
# OS shell commands to register the SHTC3 sensor at 0x70
#os.system("sudo su")
#os.system("echo shtc1 0x70 > /sys/bus/i2c/devices/i2c-1/new_device")
#os.system("exit")
# can install lm-sensors to verfiy the temperator/humidity with this software
#
# Group1 message:
# This class has been modified by the group so that we can instantiate objects for our project
#
#############################################################################
class SHTC3Sensor(object):
    def __init__(self):
        self.temperature_data_path = "/sys/class/hwmon/hwmon1/temp1_input"
        self.humidity_data_path = "/sys/class/hwmon/hwmon1/humidity1_input"
    
        self.shtc3_temp_max_value = 24
        self.shtc3_humid_max_value = 20
    
    #read humidity value and temperature from the SHTC3 sensor
    def read_humidity(self):
        humidity = open(self.humidity_data_path,'r')
        h_data = int(humidity.read())/1000   
        return h_data

    def read_temperature(self):
        temperature = open(self.temperature_data_path,'r')
        t_data = int(temperature.read())/1000  
        return t_data

    # write to csv file
    def write_csv_data(self, filename, t_data, h_data, time_data):
        with open(filename, mode = 'a') as f:
            f_writer = csv.writer(f, delimiter = ',')
            f_writer.writerow([t_data, h_data, time_data])

    def write_csv_header(self, filename, header1, header2, header3):
        with open(filename, mode = 'w') as f:
            f_writer = csv.writer(f, delimiter = ',')
            f_writer.writerow([header1, header2, header3])
    
   # check if temperature cross max value
    def check_cross_max_temp(self):
        if self.read_temperature() > self.shtc3_temp_max_value :
            return True
        else:
            return False
    # check if humidity cross max value
    def check_cross_max_humid(self):
        if self.read_humidity() > self.shtc3_humid_max_value :
            return True
        else:
            return False
        
    # send MQTT message to the broker
    def sendMQTT(self,temperature, humidity, time):
        topic_name = "NhanIOT/test/"
        mqtt_host = "test.mosquitto.org"
        
        data_dict = {"Temperature": temperature, "Humidity": humidity,"time": str(dt.datetime.now())}
        data_out = json.dumps(data_dict)
        publish.single(topic_name, data_out, hostname = mqtt_host)
        
    def sendMQTT_alarm(self, temperature):
        topic_name = "NhanIOT/test/alarm"
        mqtt_host = "test.mosquitto.org"
        
        data_dict = {"Temperature": temperature, "Humidity": humidity,"time": str(dt.datetime.now())}
        data_out = json.dumps(data_dict)
        publish.single(topic_name, data_out, hostname = mqtt_host)
        msg = "Temperature cross max value " + str(SHTC3Sensor.shtc3_temp_max_value)
        publish.single(topic_name, msg, hostname = mqtt_host)

class ConnectTH( SHTC3Sensor ):
    def __init__( self, csv_filename, header1='temperature',header2='humidity',header3 = 'time'):
        """ initialize instance of ConnectTH """
        SHTC3Sensor.__init__(self)
        self.collecting = False             # to know if connected and collecting data 
        self.switchCollecting = False       # to know if threading is taking place - switch on/off true/false   
        self.csv_filename = csv_filename    # name of output file
        self.header1 = header1              # first field header of output file
        self.header2 = header2              # second field header of output file
        self.header3 = header3              # third field header of output file
        self.temperature = '--'             # holder for last temperature reading
        self.humidity = '--'                # holder for last humidity reading
        self.isCelcius = True               # flag to know if using Celcius or Farenheit scale
        self.tempAlert = False              # flag to know if there is a temperature alert
        self.tempAlertThreshold = 30        # default threshold for temperature alert
        self.humAlert = False               # flag to know if there is a humidity alert
        self.humAlertThreshold = 50         # default threshold for humidity alert

    def set_tempAlertThreshold(self, threshold):
        """ used to set the temperature alert threshold - optional """
        self.tempAlertThreshold = threshold

    def set_humAlertThreshold(self, threshold):
        """ used to set the humidity alert threshold - optional """        
        self.humAlertThreshold = threshold

    def flipScale(self):
        """ used to change temperature scale C/F """
        self.isCelcius = not self.isCelcius        

    def isCollecting( self ):
        """ used to validate collect buttons """
        if self.collecting:
            return True
        else:
            showinfo("Message", "Please connect first")
            return False

    def convert_C2F(self, temperature):
        """ convert celcius to farenheit - celcius is the default temperature """
        return float(int((temperature * 9/5 + 32) *10)/10)

    def readSensorTemperature( self ):
        """
            read temperature from sensor
            set temperature alert flag if needed
            convert temperature from celcius to farenheit if needed
        """
        temp = round(self.read_temperature(),1)
        if temp >= self.tempAlertThreshold:
            self.tempAlert = True
        else:
            self.tempAlert = False
        if self.isCelcius:
            return temp
        else:
            return self.convert_C2F(temp)
        
    def readSensorHumidity( self ):
        """
            read humidity from sensor
            set humidity alert flag if needed
        """        
        hum = round(self.read_humidity(),1)
        if hum >= self.humAlertThreshold:
            self.humAlert = True
        else:
            self.humAlert = False
        return hum    

    def getTemperature( self ):
        """
            get temperature called from button
            first validate sensor is connected
        """
        if self.isCollecting():
            return self.readSensorTemperature()
        else:
            return ''

    def getHumidity( self ):
        """
            get humidity called from button
            first validate sensor is connected
        """        
        if self.isCollecting():
            return self.readSensorHumidity()
        else:
            return ''

    def getReadings( self ):
        """
            get temperature and humidity readings from sensor
            initiated indirectly by `connect` button so we know the sensor is connected
        """
        self.temperature = self.readSensorTemperature()
        self.humidity = self.readSensorHumidity()
        
    def collectData( self ):
        """
            initiated indirectly by `connect` button
            determine is collecting should continue
            get sensor readings and time
            write csv file data: temperature, humidity and time
        """
        if self.switchCollecting:
            threading.Timer(1.0, self.collectData).start()
        self.getReadings()
        time_now = str(dt.datetime.now())
        try:
            self.write_csv_data(self.csv_filename, self.temperature, self.humidity, time_now)
        except:
            showinfo("Message","We have a threading problem!")
            exit()
            
    def haveGoodConnection( self ):
        """
            validate connection to sensor
        """
        try:
            self.getReadings()
        except:
            temp = "Sensor is not working !\n\n"
            temp += " "*10 + "Try\n\n"
            temp += "`sudo ./read_TH.sh`"
            showinfo("Message", temp)
            exit()
        return True

    def startCollecting( self ):
        """
            starts the process of collecting temperature, humidity and time readings
            validate collecting process is only started once
            calls for validation of a good connection before creating the file
        """
        #start collecting only once
        if self.collecting:
            messagebox.showinfo("Message","Already collecting",icon='warning')
            return
        self.switchCollecting = True
        if self.haveGoodConnection():
            self.collecting = True
            try:
                self.write_csv_header(self.csv_filename, self.header1, self.header2, self.header3)
            except:
                messagebox.showinfo("Message","We have a file creation problem!",icon='error')
                exit()
            self.collectData()

    def stopCollecting( self ):
        """
            direct result of pressing the `disconnect` button
            stops the process of collecting data
            first validates if sensor is connected (collecting)
            if connected then a flag is set to false to indicate collecting should stop
            we sleep for 2 seconds as it takes 1 second for the collecting process to stop
        """
        if not self.collecting:
            messagebox.showinfo("Message", "Not connected",detail='No need to Disconnect')
        else:
            self.switchCollecting = False
            time.sleep(2)
            messagebox.showinfo("Message","Collecting stopped",detail='Disconnected by user')
            self.collecting = False
            
            

    def get_Temp_CSV(self,temp):
        '''
        Method to read the csv file and get the temperature values in function of time stamp 
        Input : threshold temperature value
        output :  a graph that show the variation of temperature in function of time stamp 
        '''
    
        try:
            if temp is not None:
                CSV_Columns = defaultdict(list)
                with open(self.csv_filename) as CSV_File:
                    reader_File = csv.DictReader(CSV_File)
                    for entry in reader_File:
                        for (key,value) in entry.items():
                                CSV_Columns[key].append(value)
                list_time_temperature = list(zip(CSV_Columns['time'],CSV_Columns['temperature']))  
                list_time_temperature = [x for x in list_time_temperature if float(x[1])>float(temp)] 
                list_time = [x[0] for x in list_time_temperature ]
                list_temperature = [float(x[1]) for x in list_time_temperature ]
                plt.plot(list_time,list_temperature)
                plt.xlabel('Time') 
                plt.xticks(rotation=45,ha='right')
                plt.subplots_adjust(bottom=0.30)
                plt.ylabel('Temperature') 
                plt.title('Changed temperature got by sensor ') 
                plt.show()
        except FileNotFoundError:
            print("File does not exist !!!")

  
    def get_Hum_CSV(self,hum):
        '''
	Method to read the csv file and get the humidity values in function of time stamp 
	Input : threshold humidity value 
	output :  a graph that show the variation of humidity in function of time stamp
	'''
	
        try:
            if hum is not None:
                CSV_Columns = defaultdict(list)
                with open(self.csv_filename) as CSV_File:
                    reader_File = csv.DictReader(CSV_File)
                    for row in reader_File:
                        for (key,value) in row.items():
                                CSV_Columns[key].append(value)
                list_time_humidity = list(zip(CSV_Columns['time'],CSV_Columns['humidity']))  
                list_time_humidity = [x for x in list_time_humidity if float(x[1])>float(hum)] 
                list_time = [x[0] for x in list_time_humidity ]
                list_humidity = [float(x[1]) for x in list_time_humidity ]
                plt.plot(list_time,list_humidity)
                plt.xlabel('Time') 
                plt.xticks(rotation=45,ha='right')
                plt.subplots_adjust(bottom=0.30)
                plt.ylabel('Humidity') 
                plt.title('Changed humidity got by sensor ') 
                plt.show()
        except FileNotFoundError:
            print("File does not exist !!!")

    
    def get_Temp_animated(self,i,graph_X,list_X,list_Y):
        '''
	Method to monitor the output of the temperature sensor in real time
	
	Input : i: frame number it will be automatically incremented by 1
			graph_X : figure to draw
			list_X : list of time stamp
			list_Y : list of temperature values
	
	output :  a graph that show the variation of temperature in real time
	 
	'''
	
        temp_now = self.temperature
        time_now = str(dt.datetime.now())
        list_X.append(time_now)
        list_Y.append(temp_now)
        list_X=list_X[-20:]
        list_Y=list_Y[-20:]
        graph_X.clear()
        graph_X.plot(list_X,list_Y)
        plt.xticks(rotation=45,ha='right')
        plt.subplots_adjust(bottom=0.30)
        plt.title('Real Time temperature get from sensor')
        plt.ylabel('Temperature')
        
    
    def get_Hum_animated(self,i,graph_X,list_X,list_Y):
        '''
	Method to monitor the output of the humidity sensor in real time
	
	Input : i: frame number it will be automatically incremented by 1
			graph_X : figure to draw
			list_X : list for time stamp
			list_Y : list for humidity  values
	
	output :  a graph that show the variation of humidity in real time
	 
	'''
        hum_now = self.humidity
        time_now = str(dt.datetime.now())
        list_X.append(time_now)
        list_Y.append(hum_now)
        list_X=list_X[-20:]
        list_Y=list_Y[-20:]
        graph_X.clear()
        graph_X.plot(list_X,list_Y)
        plt.xticks(rotation=45,ha='right')
        plt.subplots_adjust(bottom=0.30)
        plt.title('Real Time humidity get from sensor')
        plt.ylabel('Humidity')


class SensorAlert:
    def __init__(self):
        """ initialize the SensorAlert object """
        self.LED_Temp = 20                      # GPIO pin 20 of raspberry pi is used as a temperature alert when True/HIGH
        self.LED_Hum = 21                       # GPIO pin 21 of raspberry pi is used as a humidity alert when True/HIGH 
        GPIO.setmode(GPIO.BCM)                  # set GPIO mode
        GPIO.setup(self.LED_Temp, GPIO.OUT)     # set temperature pin 20 as output
        GPIO.setup(self.LED_Hum, GPIO.OUT)      # set humidity pin 21 as output
##        self.set_TempAlertOn()
##        self.set_HumAlertOn()
##        time.sleep(5)
##        self.set_TempAlertOff()
##        self.set_HumAlertOff()
####        time.sleep(10)

    def set_TempAlertOn(self):
        """ turn on alert pin 20 goes high """
        GPIO.output(self.LED_Temp, True)

    def set_TempAlertOff(self):
        """ turn off alert pin 20 goes low """        
        GPIO.output(self.LED_Temp, False)
        
    def set_HumAlertOn(self):
        """ turn on alert pin 21 goes high """        
        GPIO.output(self.LED_Hum, True)

    def set_HumAlertOff(self):
        """ turn off alert pin 21 goes low """          
        GPIO.output(self.LED_Hum, False)

    def cleanup(self):
        """ cleanup GPIO - sets all GPIO pins as input to prevent accidental damage """
        GPIO.cleanup()      

##ledAlert = SensorAlert()
##ledAlert.set_TempAlertOn()
##time.sleep(5)
##ledAlert.set_TempAlertOff()
##ledAlert.set_HumAlertOn()
##time.sleep(5)
##ledAlert.set_HumAlertOff()
##GPIO.cleanup()




###################################################
        
#####################################################
### MAIN
####################################################
##csv_filename1 = 'temp-humid.csv'
##csv_filename2 = 'temp.csv'
##header1 = 'temperature'
##header2 = 'humidity'
##header3 = 'time'
###register SHTC3 sensor to the system, must run in su mode
###os.system("echo shtc1 0x70 > /sys/bus/i2c/devices/i2c-1/new_device")
##
##sensor1 = SHTC3Sensor()
##sensor2 = TMP117Sensor()
##sensor2.init_i2c_smbus()
### prepare header for csv file
##if not(os.path.isfile(csv_filename1)):
##    sensor1.write_csv_header(csv_filename1, header1, header2, header3)
##if not(os.path.isfile(csv_filename2)):
##    sensor2.write_csv_header(csv_filename2,header1, header3)
##
##while True:
##    temperature2 = round(sensor2.read_temp(),1)
##    print("Temperature from TMP117 : ", temperature2, "C")
##    
##    temperature1 = round(sensor1.read_temperature(),1)
##    print("Temperature from SHTC3  : ", temperature1, "C")
##    
##    humidity = round(sensor1.read_humidity(),1)
##    print("Humidity from SHTC3     : ", humidity, "%")
##    
##    time_now = str(dt.datetime.now())
##    
##    sensor1.write_csv_data(csv_filename1, temperature1, humidity, time_now)
##    sensor2.write_csv_data(csv_filename2, temperature2, time_now)
##    
####    sensor1.sendMQTT(temperature1, humidity, time_now)
####    if sensor1.check_cross_max_temp():
####        print ("Temperature now %s cross max value %s!" % (round(temperature1,1), SHTC3Sensor.shtc3_temp_max_value))
####        sensor1.sendMQTT_alarm(temperature1)
####    else:
####        print("Temperature is still under max value!")
##    
##    time.sleep(1)
