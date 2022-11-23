from tkinter import *
from tkinter import ttk

#Tkinter Testing
    
def drawNodes():

    def addNode(event):
    
        x0 = event.x -50
        y0 = event.y -50
        x1 = event.x +50
        y1 = event.y +50

        doSet = True

        for i in range(1, len(nodes)):
            a = x0 - nodes[i]['x0']
            b = y0 - nodes[i]['y0']
            c = ((a**2) + (b**2))**0.5
            
            if c<141.4:
                doSet=False
                break

        if (doSet):
            id = canvas.create_oval(x0,y0,x1,y1, fill='red', outline='black')
            print(id)
            nodes[id] = {'x0':x0, 'y0':y0, 'x1':x1, 'y1':y1}


    nodes = {}
    root = Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    canvas = Canvas(root)

    canvas.grid(column=0, row=0, sticky=(N, W, E, S))
    canvas.bind("<Button-1>", addNode)


    root.mainloop()