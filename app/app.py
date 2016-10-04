from flask import Flask
from flask import request
from flask import render_template
import psycopg2
app = Flask(__name__)

conn = psycopg2.connect("host='db' dbname='postgres' user='postgres'")
cur = conn.cursor()

@app.route('/')
def hello(name=None):

    # set up table if needs be
    query = "CREATE TABLE IF NOT EXISTS cats(name text, coat text, donut text);"
    cur.execute(query)
    conn.commit()

    return render_template('index.html')

@app.route('/write-db', methods=['POST'])
def writedb():

    query = "insert into cats (name, coat, donut) values(%s, %s, %s)"
    cur.execute(query, (request.form['name'], request.form['coat'], request.form['donut']))
    conn.commit()

    n = request.form['name']
    
    return render_template('thanks.html', name=n)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)