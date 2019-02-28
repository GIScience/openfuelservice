# openpoiservice/server/config.py

from openfuelservice.server import ofs_settings

pg_settings = ofs_settings['provider_parameters']


class BaseConfig(object):
    """Base configuration."""

    # SECRET_KEY = 'my_precious'
    WTF_CSRF_ENABLED = True
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class ProductionConfig(BaseConfig):
    """Production configuration."""

    # SECRET_KEY = 'my_precious'
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(pg_settings['admin_user'], pg_settings['admin_password'],
                                                                   pg_settings['host'], pg_settings['port'],
                                                                   pg_settings['db_name'])
    DEBUG_TB_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(pg_settings['admin_user'], pg_settings['admin_password'],
                                                                   pg_settings['host'], pg_settings['port'],
                                                                   pg_settings['db_name'])

    DEBUG_TB_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class TestingConfig(BaseConfig):
    """Testing configuration."""

    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(pg_settings['admin_user'], pg_settings['admin_password'],
                                                                   pg_settings['host'], pg_settings['port'],
                                                                   pg_settings['db_name'])
    DEBUG_TB_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
