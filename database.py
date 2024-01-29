from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# SQLite Database
# SQLARCHEMY_DATABASE_URL = "sqlite:///./todosapp.db"
# engine = create_engine(SQLARCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

# Postgres Database
SQLARCHEMY_DATABASE_URL = "postgresql://sswhxtwz:sJ8IhSqIJzP8DmCpKYEiQXoU8mgyZaFW@babar.db.elephantsql.com/sswhxtwz"
engine = create_engine(SQLARCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
