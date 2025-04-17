# Dynamic Load Balancing System

## Overview

This project simulates a distributed load balancing system using gRPC and Consul for dynamic service discovery. The system efficiently distributes computational requests among multiple backend servers, preventing overload on any single server and maximizing resource utilization.

The architecture consists of clients, a load balancer server, backend servers, and Consul for service discovery. The load balancer maintains the state of all backend servers and implements the selected load balancing policy, providing clients with the optimal backend server for each request.

---

## System Components

- **Backend Servers**:  
  - Register themselves with the LB server and Consul.
  - Periodically report their current load.
  - Handle computational requests from clients.

- **Load Balancer (LB) Server**:  
  - Maintains a dynamic list of available backend servers and their load status.
  - Implements three load balancing policies:
    - **Pick First**: Always selects the first available server.
    - **Round Robin**: Cycles through servers in order.
    - **Least Load**: Selects the server with the lowest reported load.
  - Responds to client queries with the best server according to the selected policy.
  - Discovers backend servers dynamically using Consul.

- **Clients**:  
  - Discover the LB server using Consul.
  - Query the LB server for the best backend server.
  - Send computational requests to the selected backend server.

- **Consul**:  
  - Provides service discovery for both the LB server and backend servers.
  - Ensures clients and the LB server always have up-to-date information about available services.

---

## Features

- **Dynamic Service Discovery**: Both clients and the LB server use Consul to discover available services at runtime.
- **Multiple Load Balancing Policies**: Easily switch between Pick First, Round Robin, and Least Load strategies.
- **Automatic Backend Registration**: Backend servers register and deregister themselves with Consul and the LB server.
- **Health Checks**: Consul performs TCP health checks to ensure only healthy services are used.
- **Scalability**: Add or remove backend servers at any time; the system adapts automatically.
- **gRPC-based Communication**: All inter-component communication uses efficient, strongly-typed gRPC APIs.


---


## Directory Structure

```
protofiles/
  ├── loadbalancer.proto
  ├── server.proto
server/
  ├── load_balancer.py
  ├── backend_server.py
client/
  ├── client.py
```

---

## Dependencies

- Python 3.7+
- [grpcio](https://pypi.org/project/grpcio/)
- [grpcio-tools](https://pypi.org/project/grpcio-tools/)
- [python-consul](https://pypi.org/project/python-consul/)
- [Consul](https://www.consul.io/) (standalone binary)

Install Python dependencies:
```sh
pip install grpcio grpcio-tools python-consul
```


Ensure that the generated files are placed in the appropriate `server/` directory for proper functionality.

Make sure the generated files are placed in the correct `server/` and `client/` directories.

---

## How to Run

### 1. Start Consul Agent

```sh
consul agent -dev
```
This starts Consul in development mode on `localhost:8500`.

---

### 2. Start the Load Balancer

```sh
python3 server/load_balancer.py
```
- Enter the load balancing policy when prompted (`PickFirst`, `RoundRobin`, or `LeastLoad`).

---

### 3. Start One or More Backend Servers

For each backend server, open a new terminal and run:
```sh
python3 server/backend_server.py
```
- Enter a unique port for each server (e.g., `50052`, `50053`, etc.).

---

### 4. Start the Client

```sh
python3 client/client.py
```
- Enter tasks as prompted. Type `exit` to quit.

---



## Notes

- Consul must be running before starting any servers or clients.
- You can start/stop backend servers at any time; the load balancer will automatically update its list.
- All gRPC and Consul communication is on `localhost` by default.
- Proto files define the gRPC service interfaces and messages.

---

