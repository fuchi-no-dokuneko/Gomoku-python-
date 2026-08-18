try:
    import random
    import numpy as np
except:
    pass
r =random
class test:
    def __init__(self):
        self.resulty=0
        self.resultx=0
    def InputData__Available(self,data):
        self.EmptySpaceList =[]
        for y in range(len(data)):
            for x in range(len(data[y])):
                if data[y,x] == True:
                    self.EmptySpaceList.append([y,x])

        self.makedecision()
    def makedecision(self):
        temp = r.randrange(len(self.EmptySpaceList))

        self.resulty = self.EmptySpaceList[temp][0]
        self.resultx =self.EmptySpaceList[temp][1]
        print(type(self).__name__+"   make decision")

