# group-message-socket
flask and socketio chat application, login functionality added

Site is deployed on heroku: http://ompals-py-chat.herokuapp.com/ 

# Setup

Add config.py to the root folder and add the following variables: 
DB_CONNECTION = 'postgres database connection'
APP_SECRET_KEY = 'your secret key'
MONGO_DB_CONNECTION = 'your mongodb connection uri'

install requirements:
`pip install -r requirements.txt`

run the application:
Set an environment variable for FLASK_APP to app.py
and then run: `flask run` 
The application runs on port 5000
