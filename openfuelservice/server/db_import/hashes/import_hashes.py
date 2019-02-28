from openfuelservice.server import db
from openfuelservice.server.db_import.models import HashModel


def store_hash(hash_object):
    h_model = HashModel(
        uuid=hash_object.uuid,
        object_name=hash_object.object_name,
        object_hash=hash_object.object_hash,
        hash_date=hash_object.hash_date
    )
    if db.session.query(db.exists().where(HashModel.object_hash == h_model.object_hash)).scalar():
        pass
    else:
        db.session.add(h_model)
        db.session.commit()


def import_hashes(hash_object):
    store_hash(hash_object)
