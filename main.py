# program init
from time import sleep
from time import time
import requests
import pprint
import json
global regattaID
global clubID
global r
pp = pprint.PrettyPrinter()
regattaID = '5656'# '6033'
clubID = '1072'
APIurl = 'https://api.regattacentral.com'

class OAuth:
  def __init__(self):
    # client credentials
    self.client_id = '2cda3093-3efd-4ffd-933d-f95a4fd02ec6'
    self.client_secret = 'r0WWayWest'
    self.username = 'dcai169'
    self.password = '77PxNIfR6rvekj76'
    # token data
    self.access_token = ''
    self.expiry_time = 0
    self.refresh_token = ''
  
  def gettoken(self):
    print('token requested')
    # get a token
    try:
      t = json.loads(requests.post(APIurl+'/oauth2/api/token', data = {'client_id':self.client_id,'client_secret':self.client_secret,'username':self.username,'password':self.password,'grant_type':'password'}).text)
    # Catch the error
    except json.decoder.JSONDecodeError:
      print(requests.post(APIurl+'/oauth2/api/token', data = {'client_id':self.client_id,'client_secret':self.client_secret,'username':self.username,'password':self.password,'grant_type':'password'}).text)
    # write token to variables
    print('token received')
    self.access_token = t['access_token']
    self.expiry_time = t['expires_in'] + time()
    self.refresh_token = t['refresh_token']
    # return token
    return t['access_token']

  def refreshtoken(self):
    print('refresh token')
    # refresh token after an hour
    try:
      t = json.loads(requests.post(APIurl+'/oauth2/api/token', data = {'client_id':self.client_id,'client_secret':self.client_secret, 'refresh_token':self.refresh_token, 'grant_type':'refresh_token'}).text)
    except json.decoder.JSONDecodeError:
      print(requests.post(APIurl+'/oauth2/api/token', data = {'client_id':self.client_id,'client_secret':self.client_secret,'refresh_token':self.refresh_token,'grant_type':'refresh_token'}).text)
    else:
      self.expiry_time = t['expires_in'] + time()
      self.access_token = t['access_token']

  def validatetoken(self):
    t = json.loads(requests.post(APIurl+'/oauth2/api/validate', data = {'token':self.access_token}).text)
    if 'error' in t:
      return False
    else:
      return True

class Reader:
    def __init__(self):
        # authorization stuff
        self.oauth = OAuth()
        self.access_token = self.oauth.gettoken()
        self.headers = {'Authorization':self.access_token}
        self.reauthed = False

    def getdata(self, path):
        d = requests.get(APIurl+path,headers=self.headers)
        print('data received')
        if d.status_code == 401 and self.reauthed == False:
            self.oauth.refreshtoken()
            self.reauthed = True
            self.getData(path)
        if d.status_code != 200:
            print(d.status_code)
            print(d.url)
        return json.loads(d.text)

r = Reader()

class Regatta:
    def __init__(self):
        print('started fetching data')
        # metadata
        data = r.getdata('/v4.0/regattas/' + regattaID)['data']
        self.name = data['name']
        self.dates = data['regattaDates']
        self.venue = data['venue']
        # events
        self.events = []

    def findrelevantentries(self,data):
        print('sorting entries')
        relevant_entry_ids = []
        for j in range(data['count']):
            if str(data['data'][j]['organizationId']) == clubID:
              relevant_entry_ids.append(data['data'][j]['entryId'])
        return relevant_entry_ids

    def getevents(self):
      event_ids = []
      data = r.getdata('/v4.0/regattas/'+regattaID+'/events/')
      for i in range(len(data['data'])):
            event_ids.append(data['data'][i]['eventId'])
      return event_ids

    def findrelevantevents(self):
        print('sorting events')
        temp = r.getdata('/v4.0/regattas/'+regattaID+'/organizations/'+clubID+'/events')
        events = temp['data']
        relevant_event_ids = []
        for i in range(len(events)):
            relevant_event_ids.append(events[i]['eventId'])
        return relevant_event_ids

    def buildevents(self):
        allevents = r.getdata('/v4.0/regattas/'+regattaID+'/events')['data']
        eventlist = self.getevents()
        eventstobuild = self.findrelevantevents()
        for i in range(len(eventstobuild)):
            events = []
            title = ''
            sequence = 0
            finalracetime = 0
            coxed = False
            for j in range(len(allevents)):
                if allevents[j]['eventId'] == eventstobuild[i]:
                    title = allevents[j]['title']
                    sequence = allevents[j]['sequence']
                    finalracetime = allevents[j]['finalRaceTime']
                    coxed = allevents[j]['coxed']
                e = Event(eventstobuild[i],title,sequence,finalracetime,coxed)
                events.append(e)
        self.events = events
        return events


class Event:
    def __init__(self, eventid, title, sequence, final_race_time, coxed):
        self.eventid = str(eventid)
        self.title = title
        self.sequence = sequence
        self.final_race_time = final_race_time
        self.coxed = coxed
        self.entries = self.buildentries() # list of Entry objs
        self.relevant_entries = self.findrelevantentries() # list of relevant entryIds

    def buildentries(self):
        data = r.getdata('/v4.0/regattas/'+regattaID+'/events/'+self.eventid+'/entries')['data']
        entries = []
        for i in range(len(data)):
            e = Entry(self.eventid,data[i]['entryId'],data[i]['entryLabel'])
            entries.append(e)
        return entries

    def getentrylist(self):
        data = r.getdata('/v4.0/regattas/'+regattaID+'/events/'+self.eventid+'/entries')['data']
        entries = []
        for i in range(len(data)):
            entries.append(data[i]['entryId'])
        return entries

    def findrelevantentries(self):
        data = r.getdata('/v4.0/regattas/'+regattaID+'/events/'+self.eventid+'/entries')
        relevant_entry_ids = []
        for j in range(data['count']):
            if str(data['data'][j]['organizationId']) == clubID:
                relevant_entry_ids.append(data['data'][j]['entryId'])
        return relevant_entry_ids


class Entry:
    def __init__(self, eventid, entryid, label):
        self.eventid = eventid
        self.entryid = entryid
        self.organizationid = clubID
        self.lane = self.getlane(self.entryid)
        self.lineup = self.getlineup(self.entryid)
        self.label = label
        self.position = 0
        self.timeelapsed = 0.0

    def getresults(self,position,timeelapsed):
        self.position = position
        self.timeelapsed = timeelapsed

    def getlane(self,entryid):
        try:
            lanedata = r.getdata('/v4.0/regattas/'+regattaID+'/events/'+entryid+'/lanes')['data'][0]['races'][0]['lanes']
            for i in range(len(lanedata)):
                if lanedata[i]['entryId'] == entryid:
                    return lanedata[i]['lane']
        except TypeError:
            return None

    def getlineup(self, entryid):
        try:
            lineup = []
            for i in range(len(r.getdata('/v4.0/regattas/'+regattaID+'/entries/'+entryid)['data']['entryParticipants'])):
                lineup.append(r.getdata('/v4.0/regattas/'+regattaID+'/entries/'+entryid)['data']['entryParticipants'][i]['name'])
            return lineup
        except TypeError:
            return None

m = Regatta()

print('\n'+'='*25+'\n')
print(m.getevents())
print('\n'+'='*25+'\n')
print(r.oauth.validatetoken())
print('\n'+'='*25+'\n')
pp.pprint(r.getdata('/v4.0/regattas/'+regattaID+'/events/3/results')['data'][0]['lanes'][0]) # replace the last zero with an iterative variable

