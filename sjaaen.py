
import time
def string_to_dict(arg):
    dict = {}
    if arg == "":
        return dict
    pairs = arg.split(DICT_DELIM)
    for i in pairs:
        key, val = i.split(KEYVAL_DELIM)
        dict[key] = val
    return dict

def string_to_dict(args):
    for i in range(len(args)):
        dict = {}
        if args[i] == "":
            args[i] = dict
        else:
            pairs = args[i].split(DICT_DELIM)
            for p in pairs:
                key, val = p.split(KEYVAL_DELIM)
                dict[key] = val
            args[i] = dict
    return args


d= {"en": 1, "to": 2}

while True:
    try:
        i = d.popitem()
    except:
        print("go to bucket")
        break
    print(i)




#
