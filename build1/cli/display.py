import tkinter as tk
import psycopg2 as pg
import datetime as dt

SQL_SRV='192.168.89.6'
SQL_USR='pistats'
SQL_PWD='pistats'
SQL_DB='pistats'

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack()
        master.title("PiTool Client")
        self.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.data_temp = tk.StringVar()  
        self.data_humidity = tk.StringVar()  
        self.data_light = tk.StringVar()  
        self.data_motion = tk.StringVar()  
        self.data_time = tk.StringVar() 
        self.sqlcon = None
        self.sqlcur = None
        self.createWidgets()

    def createWidgets(self):
        self.lbl_temp = tk.Label(self, textvariable=self.data_temp, width=20).grid(row=0, column=0, sticky=(tk.W, tk.N))
        self.lbl_humidity = tk.Label(self, textvariable=self.data_humidity, width=20).grid(row=0, column=1, sticky=(tk.E, tk.N))
        self.lbl_light = tk.Label(self, textvariable=self.data_light, width=20).grid(row=1, column=0, sticky=(tk.W, tk.N))
        self.lbl_motion = tk.Label(self, textvariable=self.data_motion, width=20).grid(row=1, column=1, sticky=(tk.E, tk.N))
        self.lbl_motion = tk.Label(self, textvariable=self.data_time, width=20).grid(row=2, column=3, sticky=(tk.E, tk.S))
        self.btn_update = tk.Button(self, text="Update Now", command=self.do_update).grid(column=0, row=2, sticky=(tk.W, tk.S))
     
    def updateLabels(self):
        self.data_time.set("" + str(dt.datetime.now()))
        
        if self.sqlcur is not None:
            self.sqlcur.execute("""select id, sensor_type, data_read, time_read from v_sensordata_current""")
            while True:
                data = self.sqlcur.fetchone()

                if data and str(data[1]) == 'motion':
                    self.data_motion.set("Motion: " + str(data[2]))
                elif data and str(data[1]) == 'light':
                    self.data_light.set("Light: " + str(data[2]))
                elif data and str(data[1]) == 'temperature':
                    self.data_temp.set("Temp: " + str(data[2]) + ' C')
                elif data and str(data[1]) == 'humidity':
                    self.data_humidity.set("Humidity: " + str(data[2]) + ' %')

                if not data:
                    break

        self.after(2000,  self.updateLabels)  

        #self.QUIT = tk.Button(self, text="QUIT", fg="red",command=master.destroy)
        #self.QUIT.pack(side="bottom")

    def do_update(self):
        print("hi there, everyone!")
        self.updateLabels()


def main():
    try:
        root = tk.Tk()
        app = Application(master=root)
        app.sqlcon = pg.connect(host=SQL_SRV,user=SQL_USR,password=SQL_PWD,database=SQL_DB)
        app.sqlcur = app.sqlcon.cursor()


        app.updateLabels()
        app.mainloop()
        
        app.sqlcur.close()
        app.sqlcon.close()
        print('Exit')
        

    except pg.Error as e:
        print("Sql error: " + str(e))

    except Exception as e:
        print("Unknow error: " + str(e))


if __name__ == '__main__':
    main()