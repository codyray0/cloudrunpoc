import os

from flask import Flask, render_template, request, Response
import sqlalchemy

app = Flask(__name__)

def init_unix_connection_engine():
    db_config = {
        "pool_size": 5,
        "max_overflow": 2,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    }

    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]
    db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
    cloud_sql_connection_name = os.environ["CLOUD_SQL_CONNECTION_NAME"]

    pool = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=db_user,
            password=db_pass,
            database=db_name,
            query={"unix_sock": f"{db_socket_dir}/{cloud_sql_connection_name}/.s.PGSQL"}
        ),
        **db_config
    )

    pool.dialect.description_encoding = None
    return pool

db = init_unix_connection_engine()

@app.before_first_request
def create_tables():
    with db.connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sampleTable "
            "( id SERIAL NOT NULL, name TEXT, PRIMARY KEY (id) )"
        )

@app.route('/', methods=['GET'])
def index():
    with db.connect() as conn:
        all = conn.execute(
            "SELECT * FROM sampleTable"
        ).fetchall()

        data = []
        for row in all:
            data.append({'id': row[0], 'name': row[0]})
        
    return render_template(data)

@app.route('/add', methods=['POST'])
def add_row():
    n = request.form['name']
    
    if len(n) == 0:
        return Response(status=400)
    
    try:
        with db.connect() as conn:
            conn.execute(sqlalchemy.text("INSERT INTO sampleTable (name) VALUES (:name)"), name=n)
    except:
        return Response(status=500)
    
    return Response(status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
