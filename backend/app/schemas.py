from pydantic import BaseModel, EmailStr
from datetime import date

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str 

class RoomCreate(BaseModel):
    room_number: str
    room_type: str
    price: float
    image_url: str
    description: str | None = None
    bed_type: str | None = None
    max_guests: int | None = None
    room_size: str | None = None
    facilities: str | None = None


class BookingCreate(BaseModel):
    room_id: int
    check_in_date: date
    check_out_date: date

class BookingResponse(BaseModel):
    booking_id: int
    room_id: int

    class Config:
        from_attributes = True

class RoomUpdate(BaseModel):
    room_type: str
    price: float
    available: str
    image_url: str
    description: str | None = None
    bed_type: str | None = None
    max_guests: int | None = None
    room_size: str | None = None
    facilities: str | None = None

class ReviewCreate(BaseModel):
    room_id: int
    rating: int
    comment: str        