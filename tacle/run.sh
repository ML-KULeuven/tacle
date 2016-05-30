#flask run --host=0.0.0.0 -- > to make it visible to the outside world
export FLASK_DEBUG=1 #set to false once release to the world
export FLASK_APP=main.py
flask run
