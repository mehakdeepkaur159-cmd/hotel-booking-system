const API_URL = "http://127.0.0.1:8000";

async function registerUser() {
    alert("Register button clicked");

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const response = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            email: email,
            password: password
        })
    });

    const data = await response.json();

    document.getElementById("message").innerText =
        data.message || data.detail;
}

async function loginUser() {

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: formData
    });

    const data = await response.json();

    if (data.access_token) {

        localStorage.setItem(
            "token",
            data.access_token
        );
        localStorage.setItem("role", data.role);

        document.getElementById("message").innerText =
            "Login Successful";

    } else {

        document.getElementById("message").innerText =
            data.detail;

    }
}

async function loadRooms() {
    const response = await fetch(`${API_URL}/rooms`);
    const rooms = await response.json();

    const container = document.getElementById("rooms-container");
    container.innerHTML = "";

    rooms.forEach(room => {
       container.innerHTML += `
<div class="room-card">
    <img src="${room.image_url || 'https://via.placeholder.com/300x180'}">

    <h3>Room ${room.room_number}</h3>

    <p><strong>Type:</strong> ${room.room_type}</p>

    <p><strong>Price:</strong> Rs. ${room.price}</p>

    <p><strong>Availability:</strong> ${room.available}</p>

    <button onclick="bookRoom(${room.id})">
        Book Now
    </button>
</div>
`;
    });
}

function bookRoom(roomId) {
    const token = localStorage.getItem("token");

    if (!token) {
        alert("Please login first");
        window.location.href = "login.html";
        return;
    }

    document.getElementById("selectedRoomId").value = roomId;
    document.getElementById("bookingModal").style.display = "block";
}
async function loadMyBookings() {
    const token = localStorage.getItem("token");

    if (!token) {
        alert("Please login first");
        window.location.href = "login.html";
        return;
    }

    const response = await fetch(`${API_URL}/my-bookings`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const bookings = await response.json();
    const activeBookings = bookings.filter(
    booking => booking.status !== "cancelled"
);

    const container = document.getElementById("bookings-container");
    container.innerHTML = "";

    if (activeBookings.length === 0) {
        container.innerHTML = "<p>No bookings found.</p>";
        return;
    }

    activeBookings.forEach(booking => {
        container.innerHTML += `
            <div class="room-card">
                <h3>Room ${booking.room_number}</h3>
                <p>Type: ${booking.room_type}</p>
                <p>Price: Rs. ${booking.price}</p>
                <p>Check-in: ${booking.check_in_date}</p>
                <p>Check-out: ${booking.check_out_date}</p>
                <p>Status: ${booking.status}</p>
                <p>Payment: ${booking.payment_status}</p>

                <button onclick="payBooking(${booking.booking_id})">Pay Now</button>
                <button onclick="cancelBooking(${booking.booking_id})">Cancel Booking</button>
            </div>
        `;
    });
}

async function cancelBooking(bookingId) {

    const token = localStorage.getItem("token");

    const response = await fetch(
        `${API_URL}/cancel-booking/${bookingId}`,
        {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );

    const data = await response.json();

    alert(data.message);

    loadMyBookings();
}

function logoutUser() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");

    alert("Logged out successfully");

    window.location.href = "login.html";
}
async function payBooking(bookingId) {
    const token = localStorage.getItem("token");

    const response = await fetch(`${API_URL}/booking/${bookingId}/pay`, {
        method: "PUT",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const data = await response.json();

    if (response.ok) {
        alert("Payment successful");
        loadMyBookings();
    } else {
        alert(data.detail);
    }
}
async function loadDashboard() {

    const token = localStorage.getItem("token");

    const response = await fetch(
        `${API_URL}/dashboard`,
        {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );

    const data = await response.json();

    document.getElementById("users").innerText = data.total_users;
    document.getElementById("rooms").innerText = data.total_rooms;
    document.getElementById("bookings").innerText = data.total_bookings;
    document.getElementById("revenue").innerText = "Rs. " + data.total_revenue;
}
function closeBookingModal() {
    document.getElementById("bookingModal").style.display = "none";
}

async function submitBooking() {
    const token = localStorage.getItem("token");

    const roomId = document.getElementById("selectedRoomId").value;
    const checkInDate = document.getElementById("checkInDate").value;
    const checkOutDate = document.getElementById("checkOutDate").value;

    if (!checkInDate || !checkOutDate) {
        alert("Please select both dates");
        return;
    }

    const response = await fetch(`${API_URL}/book-room`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            room_id: Number(roomId),
            check_in_date: checkInDate,
            check_out_date: checkOutDate
        })
    });

    const data = await response.json();

    if (response.ok) {
       showSuccess("Room booked successfully!");
        closeBookingModal();
        window.location.href = "my-bookings.html";
    } else {
        alert(data.detail);
    }
}
function showSuccess(message) {

    const popup =
        document.getElementById("successPopup");

    popup.innerText = message;
    popup.style.display = "block";

    setTimeout(() => {
        popup.style.display = "none";
    }, 3000);
}
function logoutUser() {
    localStorage.removeItem("token");
    alert("Logged out successfully");
    window.location.href = "login.html";
}
async function searchRooms() {

    const roomType =
        document.getElementById("roomType").value;

    const maxPrice =
        document.getElementById("maxPrice").value;

    let url =
        `${API_URL}/rooms?page=1&limit=50`;

    if (roomType) {
        url += `&room_type=${roomType}`;
    }

    if (maxPrice) {
        url += `&max_price=${maxPrice}`;
    }

    const response = await fetch(url);

    const rooms = await response.json();

    const container =
        document.getElementById("rooms-container");

    container.innerHTML = "";

    rooms.forEach(room => {

        container.innerHTML += `
        <div class="room-card">
            <img src="${room.image_url || 'https://via.placeholder.com/300x180'}">

            <h3>Room ${room.room_number}</h3>

            <p><strong>Type:</strong> ${room.room_type}</p>

            <p><strong>Price:</strong> Rs. ${room.price}</p>

            <p><strong>Availability:</strong> ${room.available}</p>

            <button onclick="bookRoom(${room.id})">
                Book Now
            </button>
        </div>
        `;
    });
}
function resetRooms() {

    document.getElementById("roomType").value = "";
    document.getElementById("maxPrice").value = "";

    loadRooms();
}
async function loadAdminRooms() {
    const response = await fetch(`${API_URL}/rooms?page=1&limit=100`);
    const rooms = await response.json();

    const container = document.getElementById("admin-rooms-container");
    container.innerHTML = "";

   rooms.forEach(room => {
    container.innerHTML += `
        <div class="room-card">
            <img src="${room.image_url || 'https://via.placeholder.com/300x180'}">

            <h3>Room ${room.room_number}</h3>

            <p><strong>Type:</strong> ${room.room_type}</p>

            <p><strong>Price:</strong> Rs. ${room.price}</p>

            <p><strong>Available:</strong> ${room.available}</p>

            <button onclick="editRoom(${room.id})">
                Update Room
            </button>

            <button onclick="deleteAdminRoom(${room.id})">
                Delete Room
            </button>
        </div>
    `;
});
}

async function addAdminRoom() {
    const token = localStorage.getItem("token");

    const roomNumber = document.getElementById("adminRoomNumber").value;
    const roomType = document.getElementById("adminRoomType").value;
    const price = document.getElementById("adminRoomPrice").value;
    const imageUrl = document.getElementById("adminRoomImage").value;

    const response = await fetch(`${API_URL}/add-room`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            room_number: roomNumber,
            room_type: roomType,
            price: Number(price),
            image_url: imageUrl
        })
    });

    const data = await response.json();

    document.getElementById("adminRoomMessage").innerText =
        data.message || data.detail;

    loadAdminRooms();
}

async function deleteAdminRoom(roomId) {
    const token = localStorage.getItem("token");

    const response = await fetch(`${API_URL}/rooms/${roomId}`, {
        method: "DELETE",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const data = await response.json();

    alert(data.message || data.detail);

    loadAdminRooms();
}
async function loadAdminBookings() {
    const token = localStorage.getItem("token");

    const response = await fetch(`${API_URL}/all-bookings`, {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const bookings = await response.json();

    const container = document.getElementById("admin-bookings-container");
    container.innerHTML = "";

    bookings.forEach(booking => {
        container.innerHTML += `
            <div class="room-card">
                <h3>Booking #${booking.booking_id}</h3>

                <p><strong>User:</strong> ${booking.user_email}</p>
                <p><strong>Room:</strong> ${booking.room_number}</p>
                <p><strong>Type:</strong> ${booking.room_type}</p>
                <p><strong>Price:</strong> Rs. ${booking.price}</p>
                <p><strong>Check-in:</strong> ${booking.check_in_date}</p>
                <p><strong>Check-out:</strong> ${booking.check_out_date}</p>
                <p><strong>Status:</strong> ${booking.status}</p>
                <p><strong>Payment:</strong> ${booking.payment_status}</p>

               ${
    booking.payment_status === "paid" &&
    booking.status === "confirmed"
        ? `<button onclick="completeBooking(${booking.booking_id})">
                Mark Completed
           </button>`
        : ""
}
            </div>
        `;
    });
}

async function completeBooking(bookingId) {
    const token = localStorage.getItem("token");

    const response = await fetch(`${API_URL}/booking/${bookingId}/complete`, {
        method: "PUT",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const data = await response.json();

    alert(data.message || data.detail);

    loadAdminBookings();
}
async function loadAdminUsers() {
    const token = localStorage.getItem("token");

    const response = await fetch(`${API_URL}/users`, {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const users = await response.json();

    const container = document.getElementById("admin-users-container");
    container.innerHTML = "";

    users.forEach(user => {
        container.innerHTML += `
            <div class="room-card">
                <h3>${user.name}</h3>

                <p><strong>Email:</strong> ${user.email}</p>
                <p><strong>Role:</strong> 
                    <span class="${user.role === 'admin' ? 'admin-badge' : 'user-badge'}">
                        ${user.role}
                    </span>
                </p>
            </div>
        `;
    });
}
async function editRoom(roomId) {
    const roomType = prompt("Enter new room type");
    const price = prompt("Enter new price");
    let available = prompt("Available? Type Yes or No");
    const imageUrl = prompt("Enter image URL");

    if (!roomType || !price || !available || !imageUrl) {
        alert("All fields are required");
        return;
    }

    available = available.toLowerCase() === "no" ? "No" : "Yes";

    const token = localStorage.getItem("token");

    const response = await fetch(`${API_URL}/rooms/${roomId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            room_type: roomType,
            price: Number(price),
            available: available,
            image_url: imageUrl
        })
    });

    const data = await response.json();

    if (response.ok) {
        alert("Room updated successfully");
        loadAdminRooms();
    } else {
        alert(data.detail || "Room update failed");
    }
}
async function addReview() {
    const token = localStorage.getItem("token");

    const roomId = document.getElementById("roomId").value;
    const rating = document.getElementById("rating").value;
    const comment = document.getElementById("comment").value;

    const response = await fetch(`${API_URL}/add-review`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            room_id: Number(roomId),
            rating: Number(rating),
            comment: comment
        })
    });

    const data = await response.json();

    alert(data.message || data.detail);

    loadReviews();
}

async function addReview() {
    const token = localStorage.getItem("token");

    const roomId = document.getElementById("roomId").value;
    const rating = document.getElementById("rating").value;
    const comment = document.getElementById("comment").value;

    const response = await fetch(`${API_URL}/reviews`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            room_id: Number(roomId),
            rating: Number(rating),
            comment: comment
        })
    });

    const data = await response.json();
    alert(data.message || data.detail);
}

async function loadReviews() {
    const roomId = prompt("Enter room ID to view reviews");

    if (!roomId) return;

    const response = await fetch(`${API_URL}/rooms/${roomId}/reviews`);
    const data = await response.json();

    const container = document.getElementById("reviews-container");
    container.innerHTML = "";

    container.innerHTML += `
        <div class="room-card">
            <h3>Room ID: ${data.room_id}</h3>
            <p><strong>Average Rating:</strong> ${data.average_rating}</p>
        </div>
    `;

    data.reviews.forEach(review => {
        container.innerHTML += `
            <div class="room-card">
                <h3>${review.user}</h3>
                <p><strong>Rating:</strong> ${review.rating}/5</p>
                <p><strong>Comment:</strong> ${review.comment}</p>
            </div>
        `;
    });
}

function checkAdminLink() {
    const role = localStorage.getItem("role");
    const adminLink = document.getElementById("adminLink");

    if (adminLink && role === "admin") {
        adminLink.style.display = "inline";
    } else if (adminLink) {
        adminLink.style.display = "none";
    }
}