# from app.db.base_class import Base
#
#
# class HashModel(Base):
#     __tablename__ = hash_table
#     uuid = db.Column(
#         db.Binary(length=16), nullable=False, primary_key=True, unique=True
#     )
#     object_name = db.Column(db.String, nullable=False, primary_key=True)
#     object_hash = db.Column(db.String, nullable=False, primary_key=True, unique=True)
#     hash_date = db.Column(db.Date, nullable=False, primary_key=False, unique=False)
#
#     def __repr__(self):
#         return "<Hash Table object {}>".format(self.object_name)
#
#     def __hash__(self):
#         return hash(self.object_name)
