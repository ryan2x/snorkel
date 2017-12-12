import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Sets connection string
def build_snorkel_connection_string():
    snorkel_conn_string = os.environ['SNORKELDB'] if 'SNORKELDB' in os.environ and os.environ['SNORKELDB'] != '' \
        else 'sqlite:///' + os.getcwd() + os.sep + 'snorkel.db'
    return snorkel_conn_string


# Sets global variable indicating whether we are using Postgres
def check_snorkel_postgres():
    return build_snorkel_connection_string().startswith('postgres')


# Automatically turns on foreign key enforcement for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if build_snorkel_connection_string().startswith('sqlite'):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Defines procedure for setting up a sessionmaker
def new_sessionmaker():
    
    # Turning on autocommit for Postgres, see http://oddbird.net/2014/06/14/sqlalchemy-postgres-autocommit/
    # Otherwise any e.g. query starts a transaction, locking tables... very bad for e.g. multiple notebooks
    # open, multiple processes, etc.
    snorkel_conn_string = build_snorkel_connection_string()
    if check_snorkel_postgres():
        snorkel_engine = create_engine(snorkel_conn_string, isolation_level="AUTOCOMMIT")
    else:
        snorkel_engine = create_engine(snorkel_conn_string)

    # New sessionmaker
    SnorkelSession = sessionmaker(bind=snorkel_engine)
    return SnorkelSession


# We initialize the engine within the models module because models' schema can depend on
# which data types are supported by the engine
SnorkelSession = new_sessionmaker()
snorkel_engine = SnorkelSession.kw['bind']

SnorkelBase = declarative_base(name='SnorkelBase', cls=object)


def build_snorkel_session():
    global SnorkelSession
    global snorkel_engine
    global SnorkelBase
    SnorkelSession = new_sessionmaker()
    snorkel_engine = SnorkelSession.kw['bind']
    SnorkelBase = declarative_base(name='SnorkelBase', cls=object)
    #
    SnorkelBase.metadata.create_all(snorkel_engine)
