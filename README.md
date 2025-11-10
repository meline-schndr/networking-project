# Network Project - Pizzeria Management

A Python client-server application for validating and managing pizza orders, developed as part of the "Introduction to Networks" (PEI-A A2) university project.


## ✨ Features : The current system (Phase IV) is capable of:
- Connecting to a PostgreSQL database.
- Listening for customer orders broadcast over the network.
- Validating the feasibility of each order based on production time and delivery time.


## 🚀 Technologies Used and structure

- Language: Python 3
- Database: PostgreSQL 
- Python Libraries: psycopg2 (DB connection), socket (UDP/TCP networking)

```
networking-project/
├── pizzeria/
│   ├── __init__.py
│   ├── database.py             # Database handler
│   ├── network.py              # Order reciever
│   └── order_processor.py      # Ordering system and management
│
├── server/
│   ├── __init__.py
│   ├── init.sql                # DB initializer
│   ├── order_broadcaster.py    # Order generator
│   └── dock_restart.bash       # Docker reloader
│
├── web/
│   ├── tcp_html.py             # (Future) Admin dashboard
│
└── main.py
```

## 📋 Prerequisites
Before you begin, ensure you have the following installed:

- Python 3.x
- Docker (and the Docker service must be running).
- The psycopg2 library for Python. You can install it via pip:
    ```
    pip install psycopg2-binary
    ```

## ⚙️ Setup & Launch
1. Launch the database
    ```
    chmod +x docker_restart.bash
    # Run the script
    ./server/docker_restart.bash
    ```
    You should see logs from Docker and psql indicating the tables have been created.

2. Launch the Order Simulator
    ``` 
    python server/order_broadcaster.py
    # Use python3 if 'python' is not recognized
    ```

3. Launch the Pizzeria Client (in a second terminal)
    ```
    python main.py
    # Also use python3 if 'python' is not recognized
    ```


## 📈 Future Development Steps
- Add factory aspect and production system/limitations, we will have to optimize the ordering according to the factory's capacities.
- Add a human-machine-interface / admin dashboard.
- Implement advanced statistics (sales totals, ingredients used).
- Implement a waiting queue for orders if all posts are busy but the order could be made later.
- Optimize multi-pizza orders (ensure all 4 pizzas for a customer arrive hot at the same time).