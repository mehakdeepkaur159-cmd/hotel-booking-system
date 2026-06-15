from sqlalchemy import Column, Integer, String
from .database import Base
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Date
from sqlalchemy import Text

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    role = Column(String, default="user")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True)
    room_type = Column(String)
    price = Column(Float)
    available = Column(String, default="Yes")
    image_url = Column(String, nullable=True)
    description = Column(Text)
    bed_type = Column(String)
    max_guests = Column(Integer)
    room_size = Column(String)
    facilities = Column(Text)
    image1 = Column(String)
    image2 = Column(String)
    image3 = Column(String)
    image4 = Column(String)

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))

    check_in_date = Column(Date)
    check_out_date = Column(Date)

    status = Column(String, default="confirmed")
    payment_status = Column(String, default="pending")


    user = relationship("User")
    room = relationship("Room")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))

    rating = Column(Integer)
    comment = Column(String)

    user = relationship("User")
    room = relationship("Room")