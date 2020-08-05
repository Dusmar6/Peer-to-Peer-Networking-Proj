class File:
    def __init__(self, name, mod, path='Master'):
        self.name = name
        self.path = path
        self.mod = mod
        
        
    def __str__(self):
        ret = ''
        ret = ret+ "Name: "+ str(self.name) + "\nPath: "+ str(self.path) + "\nMod: "+ str(self.mod)
        print(ret)
        return ret
        



# list = []
#
# list.append(File("test", 543543.234534, "testpath"))
#
# list.append(File("test", 543543.234534, "testpath"))
#
# list.append(File("test", 543543.234534, "testpath"))
#
#
# j = {"masterlist":[]}
# for file in list:
#     j["masterlist"].append({"name": file.name, "mod": file.mod,  "path": file.path})
#
#
# print(j)
    