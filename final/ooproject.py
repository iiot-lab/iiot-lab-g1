"""
Project
See White board drawing
"""

from tkinter import *
from tkinter.messagebox import *
from temphum import SHTC3Sensor, ConnectTH, SensorAlert
import datetime as dt
import time
import threading

import numpy as np
import matplotlib.pyplot as plt
import csv
from collections import defaultdict
from tkinter import simpledialog
import matplotlib.animation as animation
  
class TempHumForm( Frame ):
    """Demonstrate tkInter"""
        
    def __init__( self ):
        """Create our form"""
        Frame.__init__( self )  # initializes Frame object
        self.pack( expand = YES, fill = BOTH )
        self.master.title( "Oop Sensor Project" )
        #self.master.geometry( "220x100" )  # width x length

        #---------------CONNECT---------------
        
        self.frame11 = Frame( self )
        self.frame11.pack( pady = 5)

        self.btnConnect = Button( self.frame11, text = "CONNECT", command = self.startCollecting )
        self.btnConnect.pack( side = LEFT, padx = 5)

        self.btnDisconnect = Button( self.frame11, text = "DISCONNECT", command = self.stopCollecting )
        self.btnDisconnect.pack( )        


        #-----------SENSOR TEMPERATURE / HUMIDITY --------
        #---------------TEMPERATURE---------------
        
        self.frame12 = Frame( self )
        self.frame12.pack( pady = 5 )
        
        self.btnTemperature = Button( self.frame12, text = "TEMP:", command = self.displayTemperature, width = 5 )
        self.btnTemperature.pack( side = LEFT, padx = 5 )
        
        self.txtTemperature = Entry( self.frame12, width = 6 )
        self.txtTemperature.pack( side = LEFT, padx = 5)

        #---------------TEMPERATURE C/F--------------
    
        scaleSelections = [ "C", "F" ]   

        self.chosenScale = StringVar()
  
        # initial selection
        self.chosenScale.set( scaleSelections[ 0 ] ) 
  
        # create group of Radiobutton components with same variable
        for style in scaleSelections:
            aButton = Radiobutton( self.frame12, text = style,
            variable = self.chosenScale, value = style,
            command = self.changeScale )
            aButton.pack( side = LEFT, padx = 5)

        #---------------TEMPERATURE ALERT--------------

        self.lblTemperatureAlert = Label( self.frame12, text = "",bg="#d9d9d9", width = 5 )
        self.lblTemperatureAlert.pack( side = LEFT, padx = 5)            


        #---------------HUMIDITY---------------
        
        self.frame13 = Frame( self )
        self.frame13.pack( pady = 5 )
        
        self.btnHumidity = Button( self.frame13, text = "HUM:", command = self.displayHumidity, width = 5 )
        self.btnHumidity.pack( side = LEFT, padx = 5 )
        
        self.txtHumidity = Entry( self.frame13, width = 6 )
        self.txtHumidity.pack( side = LEFT, padx = 5)

        self.lblSpacer1 = Label( self.frame13, text = "", anchor="e", width = 11 )
        self.lblSpacer1.pack( side = LEFT, padx = 5)

        self.lblHumidityAlert = Label( self.frame13, text = "", bg="#d9d9d9", width = 5 )
        self.lblHumidityAlert.pack( side = LEFT, padx = 5)

        #---------------STATUS STATS-T/STATS-H----------

        self.frame14 = Frame( self )
        self.frame14.pack( pady = 5 )        

        #---------------STATUS STATS-T------------------

        self.btnStatsTemp = Button( self.frame14, text = "STATS-T", command = self.displayStatsTemp, width = 10 )
        self.btnStatsTemp.pack( side = LEFT, padx = 5 )

        #---------------STATUS STATS-H------------------

        self.btnStatsHum = Button( self.frame14, text = "STATS-H", command = self.displayStatsHum, width = 10 )
        self.btnStatsHum.pack( side = LEFT, padx = 5 )
        
        
         #---------------STATUS RT-T/RT-H----------

        self.frame15 = Frame( self )
        self.frame15.pack( pady = 5 )   
        
        
         #---------------STATUS RT-T------------------

        self.btnRTTemp = Button( self.frame15, text = "RT-T", command = self.displayRTTemp, width = 10 )
        self.btnRTTemp.pack( side = LEFT, padx = 5 )

        #---------------STATUS RT-H------------------

        self.btnRTHum = Button( self.frame15, text = "RT-H", command = self.displayRTHum, width = 10 )
        self.btnRTHum.pack( side = LEFT, padx = 5 )
        
        
        # Set this true if you have the `sensor alert hardware` installed
        self.usingSensorAlertHardware = False 
        if self.usingSensorAlertHardware:
            self.ourSensorAlert = SensorAlert() ## to control led alert signals
        self.ourSensor = ConnectTH( "temperature-humidity.csv", "temperature", "humidity", "time" )
        self.ourSensor.set_tempAlertThreshold(30) # same as default
        self.ourSensor.set_humAlertThreshold(30) # same as default       
    def startCollecting( self ):
        """ start the process of collecting """
        self.ourSensor.startCollecting()
        
    def stopCollecting( self ):
        """ stop the process of collecting """
        self.ourSensor.stopCollecting()
        if self.usingSensorAlertHardware:        
            self.ourSensorAlert.cleanup()

    def displayTemperature( self ):
        """ display temperature - button pressed """
        self.txtTemperature.delete(0,'end')
        self.txtTemperature.insert( INSERT , self.ourSensor.getTemperature() )
        if self.ourSensor.tempAlert:
            self.lblTemperatureAlert.configure(bg = 'RED')
            if self.usingSensorAlertHardware:
                self.ourSensorAlert.set_TempAlertOn()            
        else:
            self.lblTemperatureAlert.configure(bg = '#d9d9d9')
            if self.usingSensorAlertHardware:            
                self.ourSensorAlert.set_TempAlertOff()             
        #humidity = round(sensor1.read_humidity(),1)
        #showinfo("Message", "You pressed the TEMP: button")

    def displayHumidity( self ):
        """ display humidity - button pressed """
        self.txtHumidity.delete(0,'end')
        self.txtHumidity.insert( INSERT , str(self.ourSensor.getHumidity()) )
        if self.ourSensor.humAlert:
            self.lblHumidityAlert.configure(bg = 'RED')
            if self.usingSensorAlertHardware:            
                self.ourSensorAlert.set_HumAlertOn()
        else:
            self.lblHumidityAlert.configure(bg = '#d9d9d9')
            if self.usingSensorAlertHardware:            
                self.ourSensorAlert.set_HumAlertOff()            
        #humidity = round(sensor1.read_humidity(),1)        
        #showinfo("Message", "You pressed the HUM: button")

    def displayStatsTemp( self ):
        '''
        method that used tkinter simpledialog module to get the float value of the temperature threshold from user with options: initialvalue = 0.0,minvalue=-200.0,maxvalue=200.
        call of the method get_Temp_CSV on ConnectTH object
        '''
        float_value = simpledialog.askfloat('temperature threshold','what is temperature threshold',initialvalue = 0.0,minvalue=-200.0,maxvalue=200.0)
        self.ourSensor.get_Temp_CSV(float_value)
        
        #showinfo("Message", "You pressed the STATS-T button")

    def displayStatsHum( self ):
        '''
        method that used tkinter simpledialog module to get the float value of the humidity threshold from user with options: initialvalue = 0.0,minvalue=-200.0,maxvalue=200.
        call of the method get_Hum_CSV on ConnectTH object
        '''
        float_value = simpledialog.askfloat('humidity threshold','what is humidity threshold',initialvalue = 0.0,minvalue=0.0,maxvalue=200.0)
        self.ourSensor.get_Hum_CSV(float_value)        
        #showinfo("Message", "You pressed the STATS-H button")
        
    def displayRTTemp( self ):
        '''
        Method that used FuncAnimation function in animation module to automate updating the graph
        options to pass to FuncAnimation:graph that we want to draw
                                         name of the function that should be called at regular interval
                                         arguments to pass to our get_Temp_animated: graph_X : select the subplot for the current plot
                                                                                     list_X: list for x values (time stamp)
                                                                                     list_Y: list for y values (temperature)
                                                                                     interval of time to call the animation function
                                                                          
        
        '''
        if self.ourSensor.isCollecting():
            graph = plt.figure()
            list_X = []
            list_Y = []
            graph_X = graph.add_subplot(1,1,1)
            temperature_animation = animation.FuncAnimation(graph,self.ourSensor.get_Temp_animated, fargs = (graph_X,list_X,list_Y),interval = 100)
            plt.show()
        
        
    def displayRTHum( self ):
        '''
        Method that used FuncAnimation function in animation module to automate updating the graph
        options to pass to FuncAnimation:graph that we want to draw
                                         name of the function that should be called at regular interval
                                         arguments to pass to our get_Temp_animated: graph_X : select the subplot for the current plot
                                                                                     list_X: list for x values (time stamp)
                                                                                     list_Y: list for y values (humidity)
                                                                                     interval of time to call the animation function
                                                                          
        
        '''
        if self.ourSensor.isCollecting():
            graph = plt.figure()
            list_X = []
            list_Y = []
            graph_X = graph.add_subplot(1,1,1)
            humidity_animation = animation.FuncAnimation(graph,self.ourSensor.get_Hum_animated, fargs = (graph_X,list_X,list_Y),interval = 100)
            plt.show()
        

    def changeScale( self ):
        """ change scale to and from celsius-farenheit """
        self.ourSensor.flipScale()
        self.txtTemperature.delete(0,'end')
        self.txtTemperature.insert( INSERT , self.ourSensor.getTemperature() )

        
        #showinfo( "Message", "You changed the temperature scale")


def main():
    TempHumForm().mainloop()  # starts event loop
if __name__ == "__main__":
        main()
