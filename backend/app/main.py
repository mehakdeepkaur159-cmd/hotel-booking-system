from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from datetime import date
from sqlalchemy import and_

from .database import engine
from . import models, schemas
from .dependencies import get_db
from .auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Register User
# -----------------------------
@app.post("/register")
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(models.User)
        .filter(models.User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user.password)

    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully"
    }


# -----------------------------
# Login User
# -----------------------------
@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        form_data.password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    access_token = create_access_token(
        data={"sub": user.email}
    )

    return {
       "access_token": access_token,
       "token_type": "bearer",
       "role": user.role
}

# -----------------------------
# Protected Profile Route
# -----------------------------
@app.get("/profile")
def profile(
    current_user: str = Depends(get_current_user)
):
    return {
        "email": current_user,
        "message": "Welcome to your profile"
    }

@app.post("/add-room")
def add_room(
    room: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can add rooms"
        )

    new_room = models.Room(
        room_number=room.room_number,
        room_type=room.room_type,
        price=room.price,
        image_url=room.image_url
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return {
        "message": "Room added successfully",
        "room_id": new_room.id
    }
@app.get("/test-room")
def test_room():
    return {
        "attributes": dir(models.Room)
    }

@app.post("/room-debug")
def room_debug(
    room: schemas.RoomCreate,
    db: Session = Depends(get_db)
):
    return {
        "model_room_number": str(models.Room.room_number),
        "input_room_number": room.room_number
    }
@app.get("/rooms")
def get_rooms(
    room_type: str = None,
    max_price: float = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(models.Room)

    if room_type:
        query = query.filter(
            models.Room.room_type == room_type
        )

    if max_price:
        query = query.filter(
            models.Room.price <= max_price
        )

    rooms = query.offset(
        (page - 1) * limit
    ).limit(limit).all()

    return rooms

@app.post("/book-room")
def book_room(
    booking: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    room = db.query(models.Room).filter(
        models.Room.id == booking.room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    # Date validation
    if booking.check_in_date < date.today():
        raise HTTPException(
        status_code=400,
        detail="Cannot book past dates"
    )
    if booking.check_in_date >= booking.check_out_date:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date"
        )

    # Overlap validation
    existing_booking = db.query(models.Booking).filter(
        models.Booking.room_id == booking.room_id,
        models.Booking.check_in_date < booking.check_out_date,
        models.Booking.check_out_date > booking.check_in_date
    ).first()

    if existing_booking:
        raise HTTPException(
            status_code=400,
            detail="Room is already booked for these dates"
        )

    new_booking = models.Booking(
        user_id=user.id,
        room_id=room.id,
        check_in_date=booking.check_in_date,
        check_out_date=booking.check_out_date,
         status="confirmed",
         payment_status="pending"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return {
        "message": "Room booked successfully",
        "booking_id": new_booking.id
    }


@app.get("/my-bookings")
def my_bookings(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    bookings = db.query(models.Booking).filter(
        models.Booking.user_id == user.id
    ).all()

    result = []

    for booking in bookings:
        result.append({
            "booking_id": booking.id,
            "room_number": booking.room.room_number,
            "room_type": booking.room.room_type,
            "price": booking.room.price,
            "check_in_date": booking.check_in_date,
            "check_out_date": booking.check_out_date,
            "status": booking.status,
            "payment_status": booking.payment_status
        })

    return result

@app.delete("/cancel-booking/{booking_id}")
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.user_id == user.id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    room = db.query(models.Room).filter(
        models.Room.id == booking.room_id
    ).first()

    room.available = "Yes"

    booking.status = "cancelled"
    db.commit()

    return {
        "message": "Booking cancelled successfully"
    }
@app.get("/all-bookings")
def all_bookings(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    bookings = db.query(models.Booking).all()

    result = []

    for booking in bookings:
        result.append({
            "booking_id": booking.id,
            "user_email": booking.user.email,
            "room_number": booking.room.room_number,
            "room_type": booking.room.room_type,
            "price": booking.room.price,
            "check_in_date": booking.check_in_date,
            "check_out_date": booking.check_out_date,
            "status": booking.status,
            "payment_status": booking.payment_status
        })

    return result

@app.put("/rooms/{room_id}")
def update_room(
    room_id: int,
    room_data: schemas.RoomUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    room = db.query(models.Room).filter(
        models.Room.id == room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    room.room_type = room_data.room_type
    room.price = room_data.price
    room.available = room_data.available
    room.image_url = room_data.image_url

    db.commit()
    db.refresh(room)

    return {
        "message": "Room updated successfully",
        "room_id": room.id
    }

@app.delete("/rooms/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    room = db.query(models.Room).filter(
        models.Room.id == room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    booking_exists = db.query(models.Booking).filter(
        models.Booking.room_id == room_id
    ).first()

    if booking_exists:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a room that has bookings"
        )

    db.delete(room)
    db.commit()

    return {
        "message": "Room deleted successfully"
    }

@app.get("/search-rooms")
def search_rooms(
    check_in_date: date,
    check_out_date: date,
    db: Session = Depends(get_db)
):
    if check_in_date >= check_out_date:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date"
        )

    booked_rooms = db.query(models.Booking.room_id).filter(
        models.Booking.check_in_date < check_out_date,
        models.Booking.check_out_date > check_in_date
    )

    available_rooms = db.query(models.Room).filter(
        ~models.Room.id.in_(booked_rooms)
    ).all()

    result = []

    for room in available_rooms:
        result.append({
            "room_id": room.id,
            "room_number": room.room_number,
            "room_type": room.room_type,
            "price": room.price
        })

    return result

@app.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    total_users = db.query(models.User).count()

    total_rooms = db.query(models.Room).count()

    total_bookings = db.query(models.Booking).count()

    total_revenue = 0

    bookings = db.query(models.Booking).all()

    for booking in bookings:
        days = (
        booking.check_out_date -
        booking.check_in_date
    ).days

    total_revenue += days * booking.room.price

    available_rooms = db.query(models.Room).filter(
        models.Room.available == "Yes"
    ).count()

    occupied_rooms = db.query(models.Room).filter(
        models.Room.available == "No"
    ).count()

    return {
        "total_users": total_users,
        "total_rooms": total_rooms,
        "total_bookings": total_bookings,
        "available_rooms": available_rooms,
        "occupied_rooms": occupied_rooms,
        "total_revenue": total_revenue
    }
@app.get("/booking/{booking_id}")
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Get booking
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    # Get logged-in user
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    # Admin can view any booking
    # Normal user can only view their own booking
    if user.role != "admin" and booking.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this booking"
        )

    return {
        "booking_id": booking.id,
        "user_email": booking.user.email,
        "room_number": booking.room.room_number,
        "room_type": booking.room.room_type,
        "price": booking.room.price,
        "check_in_date": booking.check_in_date,
        "check_out_date": booking.check_out_date
    }

@app.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Get logged-in user
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    # Admin check
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    users = db.query(models.User).all()

    result = []

    for u in users:
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role
        })

    return result
@app.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    new_role: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Get logged-in user
    admin = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    # Admin check
    if admin.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    # Validate role
    if new_role not in ["admin", "user"]:
        raise HTTPException(
            status_code=400,
            detail="Role must be admin or user"
        )

    # Find target user
    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.role = new_role

    db.commit()
    db.refresh(user)

    return {
        "message": "Role updated successfully",
        "user_id": user.id,
        "new_role": user.role
    }

@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Get logged-in user
    admin = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    # Admin check
    if admin.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    # Prevent admin from deleting themselves
    if admin.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account"
        )

    # Find target user
    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check if user has bookings
    booking_exists = db.query(models.Booking).filter(
        models.Booking.user_id == user_id
    ).first()

    if booking_exists:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a user with existing bookings"
        )

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully"
    }
@app.post("/reviews")
def add_review(
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    room = db.query(models.Room).filter(
        models.Room.id == review.room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    if review.rating < 1 or review.rating > 5:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 5"
        )

    new_review = models.Review(
        user_id=user.id,
        room_id=review.room_id,
        rating=review.rating,
        comment=review.comment
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return {
        "message": "Review added successfully"
    }
@app.get("/rooms/{room_id}/reviews")
def get_room_reviews(
    room_id: int,
    db: Session = Depends(get_db)
):
    room = db.query(models.Room).filter(
        models.Room.id == room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    reviews = db.query(models.Review).filter(
        models.Review.room_id == room_id
    ).all()

    if not reviews:
        return {
            "room_id": room_id,
            "average_rating": 0,
            "reviews": []
        }

    total_rating = 0
    result = []

    for review in reviews:
        total_rating += review.rating

        result.append({
            "user": review.user.email,
            "rating": review.rating,
            "comment": review.comment
        })

    average_rating = total_rating / len(reviews)

    return {
        "room_id": room_id,
        "average_rating": round(average_rating, 2),
        "reviews": result
    }
@app.put("/booking/{booking_id}/pay")
def pay_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if user.role != "admin" and booking.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to pay for this booking"
        )

    if booking.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cannot pay for cancelled booking"
        )

    if booking.payment_status == "paid":
        raise HTTPException(
            status_code=400,
            detail="Booking already paid"
        )

    booking.payment_status = "paid"

    db.commit()
    db.refresh(booking)

    return {
        "message": "Payment successful",
        "booking_id": booking.id,
        "payment_status": booking.payment_status
    }
@app.put("/booking/{booking_id}/complete")
def complete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.User).filter(
        models.User.email == current_user
    ).first()

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if booking.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cancelled booking cannot be completed"
        )
    if booking.payment_status != "paid":
      raise HTTPException(
        status_code=400,
        detail="Booking must be paid before completion"
    )

    booking.status = "completed"

    db.commit()
    db.refresh(booking)

    return {
        "message": "Booking marked as completed",
        "booking_id": booking.id,
        "status": booking.status
    }
# -----------------------------
# Home Route
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "Hotel Booking Backend Running"
    }