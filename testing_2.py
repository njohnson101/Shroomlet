class uno(object):
    def __init__(self,one):
        self.one = one
    
    def __setattr__(self, key, value):
        print("set '"+str(key)+"' to '"+str(value)+"' in uno")
        self.__dict__[key] = value
        
class dos(uno):
    def __init__(self, one, two):
        super().__init__(one)
        self.two = two
    
    """ def __setattr__(self, key, value):
        print("set '"+str(key)+"' to '"+str(value)+"' in dos")
        super().__setattr__(key,value) """

    def __getattr__(self, key):
        print("get attribute '"+key+"' in dos")

tofu = dos(1,2)
print(tofu)
print(tofu.__dict__)
print(tofu.tres)