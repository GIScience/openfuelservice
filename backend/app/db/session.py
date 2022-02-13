from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# import sys
#
# global_session = sys.modules[__name__]
# global_session.engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
# global_session.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=global_session.engine)
# global_session.TempSession = sessionmaker(autocommit=False, autoflush=False, bind=global_session.engine)
