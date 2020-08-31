try:
    import urequests as requests
except:
    import requests
try:
    import ujson as json
except:
    import json
try:
    import uasyncio as asyncio
except:
    import asyncio
try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct
try:
   import utime as time
except:
   import time
import camera
import esp
import machine
import WIFI.STA

# author:ITJoker
# Blog:blog.itjoker.cn
# Date:2020.08.31
esp.osdebug(False)
#esp.osdebug(True)


with open('config.json','r+') as f:
   config = json.loads(f.read())
   f.close()

index_body = '''
<html>
<head>
<title>Live</title>
</head>
<body>
  <center>
    <h1>Live Video</h1>
    <p>Version:'''+config['version']+'''</p>
    <img src="/stream/'''+config['apikey']+'''" width=720 height=540 />
  </center>
</body>
</html>
'''
headers_ = 'HTTP/1.1 200 OK\r\n'
stream_Content_Type = 'Content-Type:multipart/x-mixed-replace; boundary=frame\r\nConnection:kerror_p-alive\r\n\r\n'
html_Content_Type = 'Content-Type:text/html; charset=utf-8\r\n\r\n'
jpeg_Content_Type = 'Content-Type:image/jpeg\r\n\r\n'
jpeg_stream_Content_Type = '--frame\r\n'+jpeg_Content_Type
jpeg_snapshot_Content_Type = 'Content-disposition:inline; filename=snapshot.jpg\r\n'+jpeg_Content_Type
response = {}
response['stream'] = ''+headers_+stream_Content_Type
response['live'] = ''+headers_+html_Content_Type+index_body
response['snapshot'] = ''+headers_+jpeg_snapshot_Content_Type
response['frame'] = ''+jpeg_stream_Content_Type
response['404'] = ''+headers_+html_Content_Type+'<h1>404 Not Found</h1>'
response['errors'] = ''+headers_+html_Content_Type
response['favicon'] = ''+headers_+jpeg_Content_Type+' '

def delSocket(ClientSocket):
   ClientSocket.close()  # flash buffer and close socket
   del ClientSocket

def frame_gen():
   while True:
      yield camera.capture()
async def getTime():
   # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
   NTP_DELTA = 3155644800

   # The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
   host = 'ntp1.aliyun.com'
   NTP_QUERY = bytearray(48)
   NTP_QUERY[0] = 0x1B
   addr = socket.getaddrinfo(host, 123)[0][-1]
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   try:
      s.settimeout(1)
      res = s.sendto(NTP_QUERY, addr)
      msg = s.recv(48)
   finally:
      s.close()
   val = struct.unpack("!I", msg[40:44])[0]
   return val - NTP_DELTA

async def updateService():
   updateUrlConfig = config['updateUrl']+'/config.json'
   updateUrl = config['updateUrl']+'/main.py'
   while True:
      if config['updateUrl'] == '':
         print('Update Service Disenable!')
         break
      else:
         print('Update Service Running!')
      try:
         response = requests.get(updateUrlConfig.replace('//','/')).json()
         print('Get Config Data Success!\nCurrent Version:%s Latest Version:%s' %(config['version'],response['version']))
         if config['versionNum'] < response['versionNum'] or config['updateTime'] < response['updateTime']:
            print('Getting main.py Data ...')
            data = requests.get(updateUrl.replace('//','/')).text
            config['version'] = response['version']
            config['versionNum'] = response['versionNum']
            config['updateTime'] = response['updateTime']
            config['updateUrl'] = response['updateUrl']
            print('Get Update Data Success! Updateing main.py...')
            with open('main_new.py','w+') as f:
               f.write(data)
               f.close()
            print('Write main.py Success! Updateing config.json...')
            with open('config_new.json','w+') as f:
               f.write(json.dumps(config))
               f.close()
            print('Write config.json Success! Resetting...')
            machine.reset()
         else:
            pass
      except Exception as e:
         print(e)
      await asyncio.sleep_ms(1000*60*10)

async def sendFrame(ClientSocket):
   while True:
      error_ = ''
      try:
         ClientSocket.send(b'%s%s%s' % (response['frame'],next(pic), '\r\n\r\n'))
      except Exception as e:
        error_ = str(e)
      if error_ == '':
        await asyncio.sleep_ms(1)  # try as fast as we can
      else:
        break
   delSocket(ClientSocket)
   return


async def port_80(ClientSocket, requests):
   request = requests[1].split('/')
   try:
      if request[1] == 'webcam':  # Must have /apikey/<REQ>
         if len(request) > 2:
            if request[2] == config['apikey']:
               ClientSocket.send(b'%s' % response['live'])
               delSocket(ClientSocket)
               return

      elif request[1] == 'stream':  # start streaming
         if len(request) > 2:
            if request[2] == config['apikey']:
               ClientSocket.send(b'%s' % response['stream'])
               await sendFrame(ClientSocket)
               return

      elif request[1] == 'snapshot':  # start snapshot
         if len(request) > 2:
            if request[2] == config['apikey']:
               ClientSocket.send(b'%s%s' % (response['snapshot'],next(pic)))
               return

      ClientSocket.send(b'%s' % response['404'])
      delSocket(ClientSocket)

   except Exception as e:
      error_ = str(e)
   if error_ == '':
      await asyncio.sleep_ms(1)  # try as fast as we can
   else:
      ClientSocket.send(b'%s%s' % (response['errors'],'<h1>'+error_+'</h1>'))
      delSocket(ClientSocket)


async def socketRecv(portID):
  serverAccept = socks[portID]  # scheduled server
  while True:
     ok = True
     error_ = ''
     yield
     try:
        serverAccept.settimeout(0.05)  # in sec NB! default browser timeout (5-15 min)
        ClientSocket, ca = serverAccept.accept()
        ClientSocket.settimeout(0.05)  # in sec
     except Exception as e:
        error_ = str(e)
     if error_ != '':
        pass
        ok = False
     yield
     if ok: 
        error_ = ''
        try:
           # client accepted
           recv_ = ClientSocket.recv(1024)
        except Exception as e:
           error_ = str(e)
        if error_ != '':
           print(error_)
           ok = False
        else:
           ms = recv_.decode('utf-8')
           if ms.find('favicon.ico') < 0:
              requests = ms.split(' ')
              try:
                 print(requests[0], requests[1], ca)
              except:
                 ok = False
           else:
              # handle favicon request early
              ClientSocket.send(b'%s' % response['favicon'])
              delSocket(ClientSocket)
              ok = False
     yield
     if ok:
        await ports[portID](ClientSocket, requests)

cameraInit = 0
while True:
   cr = camera.init() 
   print("Camera ready?: ", cr)
   if cameraInit:
       print('Camera init fail!')
       break
   if cr:
      break
   cameraInit += 1
   time.sleep(2)

if not cr:
  print("Camera not ready. Can't continue!")
else:
   # reconfigure camera
   #camera.speffect(2) # black and white
   camera.quality(10)  # increase quality from 12 (default) to 10
   # setup networking
   wifi = WIFI.STA.Sta(config['WIFI_SSID'], config['WIFI_PASSWORD'])
   wifi.connect()
   wifi.wait()
   wifiConnectCount = 0
   while not wifi.wlan.isconnected():
      print("WIFI not ready. Wait...")
      time.sleep(2)
      wifiConnectCount += 1
      if wifiConnectCount >= 5:
         print("WIFI not ready. Can't continue!")
         break

   pic = frame_gen()
   socks = []
   socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   socket_.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   address_ = ('0.0.0.0', 80)
   socket_.bind(address_)
   socket_.listen(20)
   socks.append(socket_)
   ports = [port_80]  # 80
   loop = asyncio.get_event_loop()
   for i in range(len(socks)):
      if i == 0:
         loop.create_task(socketRecv(i))  # schedule 2 servers for portID 80
         loop.create_task(socketRecv(i))  # streaming hold socket until client
      else:
         loop.create_task(socketRecv(i))  # only one for 81 and 82
   print('create Task Success!')
   print('IP-Camera Current Version:%s' %(config['version']))
   loop.create_task(updateService()) 
   loop.run_forever()