import os
path_list = os.listdir()
if 'config_new.json' in path_list:
    os.remove('config.json')
    os.rename('config_new.json','config.json')
    print('Update config.json Success!')
if 'main_new.py' in path_list:
    os.remove('main.py')
    os.rename('main_new.py','main.py')
    print('Update main.py Success!')
execfile('main.py')
print('run main.py')