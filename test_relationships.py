from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# WE TEND TO CREATE A ONE TO MANY RELATIONSHIPs FROM OWNER TO PET
# A FOREIGN KEY is a field (or collection of fields) in one table, that refers to the PRIMARY KEY in another table.
# owner can have many pets
# The back_populates argument tells SqlAlchemy which column/field to link with when it joins the two tables
# db.relationship() bata baneka columns are not visible, but can be accessed in code

class Owner(db.Model):
    """tablename will be owner"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    address = db.Column(db.String(200))
    pets = db.relationship('Pet', back_populates="pet_owner")
    # relationship('Pet') so, pets will be objects formed by Pet class/table

    # backref="owmer" creates a column called owner in Pet table , it is created, we can tap into it here in code but
    # it is not displayed in the database

# duitaitira relationship() use garim so it is bidirectional,i.e. one to many from Owner to pets and
# many_to_one from Pet to Owner
# one to many from Owner to pet matra chaiyeko vaye , petmaa relationship() dinthenam hola

# |id|name|address|  db ma pets dekhaunna, but we can access it in here


class Pet(db.Model):
    """tablename will be pet"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    age = db.Column(db.Integer)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'))
    # owner means Owner tablename and .id means all ids , but pet_owner waala id linivao
    pet_owner = db.relationship('Owner', back_populates="pets")
    # relationship('Owner') so, pet_owner will be object from Owner class/table

db.create_all()

# |id|name|age|owmer_id| , db ma dekhaunna pet_owner, but we can tap it as colum in python
# hamle obj/record define garda id aafaile dinnam, foreignkey wala id ni aafule dinnam

# pet_object() banauda pet_owner= dinxam,
# id, owner_id ni hamle dina pardena
# pari = Owner(name="Pari", address="Belbas")
# hari = Owner(name="Hari", address="Butwal")
# pratik = Owner(name="pra", address="Birgunj")
# db.session.add_all([pari, hari, pratik])
# db.session.commit()

# pratik = db.session.query(Owner).filter_by(name="pra").first()
# max = Pet(name="Max", age=3, pet_owner=pratik)
# owner_id ni afai halxa coz hamle pet_owner specify garisakim, id haru hamle dina pardena
# db.session.add(max)
# db.session.commit()

# pari = db.session.query(Owner).filter_by(name="Pari").first()
# rock = Pet(name="Rock", age=4, pet_owner=pari)
# fiver = Pet(name="Fiver", age=5, pet_owner=pari)
# henry = Pet(name="Henry", age=8, pet_owner=pari)
# db.session.add_all([rock, fiver, henry])
# db.session.commit()

pari = db.session.query(Owner).filter_by(name="Pari").first()
pratik = db.session.query(Owner).filter_by(name="pra").first()
print(pari.pets)   # [<Pet 2>, <Pet 3>, <Pet 4>]
print(pratik.pets)  # [<Pet 1>]

for pet in pari.pets:
    print(f"{pet.name} is of age {pet.age}")

print(pari.pets[0])  # <Pet 2>
# Rock is of age 4
# Fiver is of age 5
# Henry is of age 8

# so owner ra pet duitai link vae esari
