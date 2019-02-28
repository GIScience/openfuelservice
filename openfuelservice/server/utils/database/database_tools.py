from pathlib import Path

from sqlalchemy import text, create_engine

from openfuelservice.server import super_admin, super_admin_pw, pg_settings, admin, admin_pw, database, \
    create_app, db
# Set up the standard database uri
from openfuelservice.server.db_import.models import HashModel
from openfuelservice.server.utils.data_update.hash_functions import file_hash

uri_old = 'postgresql://{}:{}@{}:{}/{}'.format(super_admin,
                                               super_admin_pw,
                                               pg_settings['host'], pg_settings['port'],
                                               pg_settings['db_postgres_name'])
# Set up the ofs database uri
uri_new = 'postgresql://{}:{}@{}:{}/{}'.format(super_admin,
                                               super_admin_pw,
                                               pg_settings['host'], pg_settings['port'],
                                               pg_settings['db_name'])


def compare_with_hashtable(file: Path) -> bool:
    """Takes a file and calculates the sha1 of the file.
    Afterward it is compared against the sha1 hashes stored in the database under the same filename.
    :param file: Insert any file as string
    :return: True (Hash matches the Hash in the db, False (Hashes don't match) or
                None (Object not in Hash database)
    """
    app = create_app()
    app.app_context().push()
    file_basename = file.name
    hashmap_object = db.session.query(HashModel.object_name, HashModel.object_hash).filter_by(
        object_name=file_basename).first()
    # If object not found return None
    if hashmap_object is None:
        return False

    # Else compare file and hashobject
    hash_from_file = file_hash(file)
    hash_from_hashdb = hashmap_object.object_hash

    # Return the equivalent response for the comparison
    if hash_from_file == hash_from_hashdb:
        return True
    else:
        return False


def create_db(db_name, user, uri):
    default_engine = create_engine(uri)
    try:
        conn = default_engine.connect()
        conn.execute("COMMIT")
        query_create = text(
            "CREATE DATABASE {} WITH ENCODING='UTF8' OWNER={};".format(db_name, user))
        conn.execute(query_create)
        conn.close()
    except Exception:
        print("Couldn't create the database {}".format(db_name))


def drop_db(db_name, uri):
    default_engine = create_engine(uri)
    try:
        # Delete the old ofs database and create a fresh one
        conn = default_engine.connect()
        conn.execute("COMMIT")
        terminate_connections = "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{}';".format(
            db_name)
        conn.execute(terminate_connections)
        conn.close()
        conn = default_engine.connect()
        conn.execute("COMMIT")
        query_drop = text("DROP DATABASE {}".format(db_name))
        conn.execute(query_drop)
        conn.close()
    except Exception:
        print("Couldn't delete database {}".format(db_name))


def create_user(user_name, user_pw, uri):
    default_engine = create_engine(uri)
    try:
        conn = default_engine.connect()
        conn.execute("COMMIT")
        create_admin = text(
            "CREATE ROLE {} LOGIN NOSUPERUSER INHERIT CREATEDB NOCREATEROLE NOREPLICATION PASSWORD '{}';".format(
                user_name,
                user_pw))
        conn.execute(create_admin)
        conn.close()
    except Exception:
        print("Couldn't create user {}".format(admin))


def drop_user(user_name, uri):
    default_engine = create_engine(uri)
    try:
        conn = default_engine.connect()
        conn.execute("COMMIT")
        drop_user = text('DROP ROLE {};'.format(user_name))
        conn.execute(drop_user)
        conn.close()
    except Exception:
        print("Couldn't drop user {}".format(user_name))


def reassign_objects(from_user, to_user, uri):
    try:
        advanced_engine = create_engine(uri)
        conn = advanced_engine.connect()
        conn.execute("COMMIT")
        reassign_priv = text('REASSIGN OWNED BY {} TO {};'.format(from_user, to_user))
        conn.execute(reassign_priv)
        conn.close()
    except ConnectionError:
        print("Couldn't establish connection or reassign objects")


def create_schema(uri):
    advanced_engine = create_engine(uri)
    try:
        conn = advanced_engine.connect()
        conn.execute("COMMIT")
        schema_topology = text('CREATE SCHEMA topology AUTHORIZATION postgres;')
        conn.execute(schema_topology)
        ext_postgis = text('CREATE EXTENSION postgis SCHEMA public;')
        conn.execute(ext_postgis)
        ext_postgistopo = text('CREATE EXTENSION postgis_topology SCHEMA topology;')
        conn.execute(ext_postgistopo)
        conn.close()
    except Exception:
        print("Couldn't create schemas")


def clear_table(db, session, table_name):
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        if table == table_name:
            print('Clear table {}'.format(table))
            session.execute(table.delete())
    session.commit()


def clear_tables(db, session):
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print('Clear table {}'.format(table))
        session.execute(table.delete())
    session.commit()


# This function creates a fresh database and the admin user as set in the config file
class DBSetup:

    def create(self):
        # Create User and Database
        try:
            # Try to connect to a given ofs database and remove it together with the user
            advanced_engine = create_engine(uri_new)
            conn = advanced_engine.connect()
            conn.close()
            reassign_objects(admin, super_admin, uri_new)
            self.drop()
            # When an old ofs database is found and deleted continue in else:
        except Exception:
            # When no old ofs database is found, create a new one here
            drop_user(admin, uri_old)
            create_user(admin, admin_pw, uri_old)
            create_db(database, admin, uri_old)
            create_schema(uri_new)
        else:
            # Create the fresh database
            create_user(admin, admin_pw, uri_old)
            create_db(database, admin, uri_old)
            create_schema(uri_new)

    def drop(self):
        drop_db(database, uri_old)
        drop_user(admin, uri_old)
