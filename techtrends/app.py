import sqlite3
import logging
import sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from flask import json
#import datetime

class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelname.__ne__(logging.WARNING)   



# create logger                                                                                                      
logger_stdout = logging.getLogger('logger_stdout')
logger_stdout.setLevel(logging.DEBUG) # Set to the lowest level    
logger_stderr = logging.getLogger('logger_stderr')
logger_stderr.setLevel(logging.DEBUG) # Set to the lowest level   
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
# Create a filter that only accepts INFO level messages
#filter = logging.Filter('INFO')
#filter.filter = lambda record: record.levelno == logging.INFO

# Add the filter to the stdout_handler
#stdout_handler.addFilter(filter)
#stdout_handler.addFilter(InfoFilter())
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)
formatter = logging.Formatter('%(message)s\n%(asctime)s %(levelname)s    %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
stderr_handler.setFormatter(formatter)
stdout_handler.setFormatter(formatter)
# Add handler to logger                                                                                            
logger_stdout.addHandler(stdout_handler)
logger_stderr.addHandler(stderr_handler)

#function that counts a method invocation
def counted(fn):
    def wrapper(*args, **kwargs):
        wrapper.called += 1
        return fn(*args, **kwargs)
    wrapper.called = 0
    wrapper.__name__ = fn.__name__
    return wrapper


# Function to get a database connection.
# This function connects to database with the name `database.db`
@counted
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    logger_stdout.info('The homepage has been retrieved.')
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      #app.logger.error(datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")+', Article with "'+str(post_id)+'" id does not exist!')
      logger_stderr.warning('Post Not Found!')
      return render_template('404.html'), 404
    else:
      #app.logger.info(datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")+', Article "'+post['title']+'" retrieved!')
      logger_stdout.info('The <<'+post['title']+'>> post has been retrieved.')
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logger_stdout.info('The about webpage has been retrieved.')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            #app.logger.info(datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")+', Article "'+title+'" created!')
            logger_stdout.info('The <<'+title+'>> post has been created successfully.')
            return redirect(url_for('index'))

    return render_template('create.html')

# Define the healthcheck endpoint
@app.route('/healthz')
def status():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )
    logger_stdout.info('The healthz webpage has been retrieved.')
    return response

# Define the metrics endpoint
@app.route('/metrics')
def metrics():
    numberOfPosts=totalAmountOfPosts()
    dbConnectionCounts=get_db_connection.called
    response = app.response_class(
            response=json.dumps({"status":"success","code":0,"data":{"db_connection_count": dbConnectionCounts, "post_count": numberOfPosts}}),
            status=200,
            mimetype='application/json'
    )
    logger_stdout.info('The Metrics webpage has been retrieved.')
    return response

# returns total ammount of posts available
def totalAmountOfPosts():
    connection = get_db_connection()
    row = [item[0] for item in connection.execute('SELECT count(*) FROM posts').fetchall()]
    totalNumberOfPosts=row[0]
    connection.close()
    return totalNumberOfPosts

# start the application on port 3111
if __name__ == "__main__":
   ## stream logs 
   #logging.root.handlers[:]
   #for handler in logging.root.handlers[:]:
   # logging.root.removeHandler(handler)
   #logging.basicConfig(level=logging.DEBUG)
   app.run(host='0.0.0.0', port='3111')