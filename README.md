# MaDuka - Multi-Vendor E-Commerce Platform

**Live Demo:** [http://143.198.110.248](http://143.198.110.248)  
**Author:** Peter Kibuka  
**GitHub:** [github.com/pluto476526](https://github.com/pluto476526)

---

## 📌 Project Overview

MaDuka is a fully functional, multi-vendor e-commerce platform designed to enable users to open their own shops, manage inventory, and conduct real-time communication with buyers. Built with Django, WebSockets, PostgreSQL, and Redis, the platform emphasizes modular design, scalability, and real-time interactivity.

---

## 🚀 Features

### 🛍️ Shop System
- **Multi-vendor support**: Each user can register as a shop owner.
- **Role-Based Access Control (RBAC)**:
  - **Shop Owner**: Full control over shop settings, users, and inventory.
  - **Manager**: Manages products, processes orders, and updates delivery statuses.
  - **Staff**: Limited access to assigned tasks.

### 🛒 Product & Inventory Management
- Add/edit/delete product listings
- Track inventory in real time
- Upload images and manage product variants

### 📦 Orders & Fulfillment
- Buyers can place orders with multiple vendors
- Shop owners receive notifications
- Order statuses: Pending → Processed → Shipped → Delivered

### 💬 Real-Time Chat System
- WebSocket-based in-app messaging between buyers and sellers
- Built using Django Channels, Redis, and Daphne

### 📊 Dashboard & Analytics
- Visual overview of orders, revenue, and stock levels (planned/under development)

### 📱 Responsive Design
- Optimized for mobile and desktop
- Over 50 pages to support user flows

---

## 🧰 Tech Stack

### Back-End
- **Python**: Core programming language
- **Django**: Main framework
- **PostgreSQL**: Primary relational database
- **Redis**: Message broker for WebSocket communication
- **Daphne**: ASGI server for WebSocket support

### Front-End
- **HTML5**, **CSS3**, **JavaScript**
- Templates rendered server-side (Django templating engine)

### Deployment
- **Linux VPS** (Debian)
- **Nginx** as reverse proxy
- **Docker** (optional setup)

---

## 🏁 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL
- Redis
- virtualenv / pipenv (recommended)

### Installation

```bash
# Clone the repository
$ git clone https://github.com/pluto476526/maduka.git
$ cd maduka

# Set up virtual environment
$ python3 -m venv venv
$ source venv/bin/activate

# Install dependencies
$ pip install -r requirements.txt

# Run migrations and start server
$ python manage.py migrate
$ python manage.py runserver
```

### Redis & Daphne Setup (WebSocket Support)
Ensure Redis is running:
```bash
$ redis-server
```
Start Daphne server:
```bash
$ daphne -b 0.0.0.0 -p 8001 maduka.asgi:application
```

---

## 🧪 Testing
```bash
$ python manage.py test
```

---

## 📁 Project Structure
```
maduka/
├── dash/             # Shop management logic (RBAC, products, deliveries, sales, etc.)
├── shop/             # Shopping pages
├── web/              # Main landing page, signup, signin
├── konnekt/          # WebSocket chat system
├── main/             # Superadmin actions (add shop, shop categories, etc.)
├── static/           # Static files (CSS, JS, images)
├── maduka/           # Project settings and routing
```

---

## 🙌 Contributions
Contributions are welcome! Fork the repository and submit a pull request. For major changes, open an issue to discuss what you’d like to improve.

---

## 📜 License
This project is licensed under the MIT License.

---

## 📬 Contact
**Peter Kibuka**  
Email: peterkibuka58@gmail.com  
GitHub: [github.com/pluto476526](https://github.com/pluto476526)

---
