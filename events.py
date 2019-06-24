from __future__ import print_function


import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from flask import Flask
from flask import render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import jsonify


SCOPES = ['https://www.googleapis.com/auth/calendar.events']

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

class Event(db.Model):
	id_=db.Column(db.Integer, primary_key=True)
	event_name=db.Column(db.Text, unique=True, nullable=False)
	event_description=db.Column(db.Text, nullable=False)
	date_time=db.Column(db.DateTime, nullable=False)
	mails=db.relationship('Mail',backref='author',lazy=True)
	
	def __repr__(self):
		return f"User('{self.id},{self.event_name},{self.date_time}')"

class Mail(db.Model):
	id_=db.Column(db.Integer, primary_key=True)
	mail_id=db.Column(db.Text, unique=True)
	user_id=db.Column(db.Integer, db.ForeignKey('event.id_'))

	def __repr__(self):
		return f"User('{self.user_id},{self.mail_id}')"

db.drop_all()
db.create_all()


@app.route('/', methods=["GET","POST"])
def home():
	db.drop_all()
	db.create_all()
	if request.form:
		print(request.form)
		date_string=request.form.get("datetime")
		date_object = datetime.strptime(date_string, "%m/%d/%Y %H:%M %p")
		td=Event(event_name=request.form.get('event'), date_time=date_object, event_description=request.form.get('event_description'))
		db.session.add(td)
		db.session.commit()

	events=Event.query.all()
	return render_template('homepage.html',events=events)

@app.route('/gmail', methods=["GET","POST"])
def gmail():
	if request.form:
		print(request.form)
		# user=Event.query#.first()
		# return user
		gd=Mail(mail_id=request.form.get('email_id'))
		db.session.add(gd)
		db.session.commit()
	emails=Mail.query.all()
	events=Event.query.all()
	return render_template('gmail.html',emails=emails,events=events)

@app.route('/gmail/done', methods=["GET","POST"])
def add_gmail():
	import datetime
	creds= None
	if os.path.exists('token.pickle'):
		with open('token.pickle', 'rb') as token:
			creds=pickle.load(token)
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow= InstalledAppFlow.from_client_secrets_file(
				'credentials.json', SCOPES)
			creds= flow.run_local_server()
		with open('token.pickle', 'wb') as token:
			pickle.dump(creds, token)

	service= build('calendar', 'v3', credentials=creds)
	event = db.session.query(Event).all()
	event = [op.event_name for op in event]
	mail=db.session.query(Mail).all()
	mail=[op.mail_id for op in mail]
	dates = db.session.query(Event).all()
	dates = [op.date_time for op in dates]

	now= dates[0].isoformat() + 'Z'

	attend=[]
	mydict={}
	for i in range(len(mail)):
		mydict['email']=mail[i]
		attend.append(mydict.copy())
	print(attend)


	print("Getting the upcomming events")
	event ={ 'summary' :event[0],
            'start': {
    'dateTime': now,
    
  },
  'end': {
    'dateTime': now,
    
  },
  'attendees': attend,
  		
    	
   
  }

	event= service.events().insert(calendarId='primary', body=event).execute()
	events_result= service.events().list(calendarId='primary', timeMin=now,
		maxResults=10, singleEvents=True, orderBy='startTime').execute()

	events= events_result.get('items',[])

	if not events:
		print("No upcomming events")
	for event in events:
		start= event['start'].get('dateTime', event['start'].get('date'))
		print(start, event['summary'])



	events=Event.query.all()
	emails=Mail.query.all()
	return render_template('done.html',events=events, emails=emails)
	


if __name__=="__main__":
        debug=True




