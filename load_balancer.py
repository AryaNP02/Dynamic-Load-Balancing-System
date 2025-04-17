import grpc
import threading
from concurrent import futures
import loadbalancer_pb2
import loadbalancer_pb2_grpc
import consul
import time

class LoadBalancer(loadbalancer_pb2_grpc.LoadBalancerServicer):
    def __init__(self, policy, consul_host="localhost", consul_port=8500):
        self.servers = {}
        self.server_list = []
        self.round_robin_index = 0
        self.lock = threading.Lock()
        self.policy = policy
        self.consul = consul.Consul(host=consul_host, port=consul_port)
        threading.Thread(target=self.update_servers_from_consul, daemon=True).start()

    def update_servers_from_consul(self):
        while True:
            services = self.consul.health.service("backendserver", passing=True)[1]
            with self.lock:
                new_server_list = []
                for s in services:
                    service = s['Service']
                    address = service['Address'] or s['Node']['Address']
                    port = service['Port']
                    addr = f"{address}:{port}"
                    new_server_list.append(addr)
                    if addr not in self.servers:
                        self.servers[addr] = 0  # Default load
                # Remove servers that are no longer registered
                self.server_list = new_server_list
                self.servers = {k: self.servers.get(k, 0) for k in self.server_list}
            time.sleep(3)

    def RegisterServer(self, request, context):
        with self.lock:
            if request.address not in self.servers:
                self.servers[request.address] = 0  # Default load = 0
                self.server_list.append(request.address)
                print(f"[INFO] Registered server: {request.address}")
        return loadbalancer_pb2.RegistrationResponse(success=True)

    def ReportLoad(self, request, context):
        with self.lock:
            if request.address in self.servers:
                self.servers[request.address] = request.load
                print(f"[INFO] Updated load for {request.address}: {request.load}")
                return loadbalancer_pb2.LoadReportResponse(success=True)
        print(f"[ERROR] Server {request.address} not found!")
        return loadbalancer_pb2.LoadReportResponse(success=False)

    def GetServer(self, request, context):
        print(len(self.server_list))
        for i in self.server_list:
            print(i)
        with self.lock:
            if not self.servers:
                print("[WARNING] No servers available!")
                return loadbalancer_pb2.ServerAddress(address="")

            if self.policy == "PickFirst":
                address = self.server_list[0]
            elif self.policy == "RoundRobin":
                address = self.server_list[self.round_robin_index]
                self.round_robin_index = (self.round_robin_index + 1) % len(self.server_list)
            elif self.policy == "LeastLoad":
                address = min(self.servers, key=self.servers.get)
            else:
                print(f"[ERROR] Invalid policy: {self.policy}")
                return loadbalancer_pb2.ServerAddress(address="")
            print(f"[INFO] Assigned server {address} using {self.policy} policy")
            return loadbalancer_pb2.ServerAddress(address=address)

def register_with_consul(service_name, address, port, consul_host="localhost", consul_port=8500):
    c = consul.Consul(host=consul_host, port=consul_port)
    c.agent.service.register(
        name=service_name,
        service_id=f"{service_name}-{address}-{port}",
        address=address,
        port=int(port),
        check=consul.Check.tcp(address, int(port), "10s")
    )
    print(f"[INFO] Registered Load Balancer with Consul as {service_name} at {address}:{port}")

def serve(policy):

    host = "localhost"
    port = 50051
    register_with_consul("loadbalancer", host, port)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    loadbalancer_pb2_grpc.add_LoadBalancerServicer_to_server(LoadBalancer(policy), server)
    server.add_insecure_port(f"{host}:{port}")
    print(f"[INFO] Load Balancer started on port {port} with {policy} policy")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    policy = input("Enter load balancing policy (PickFirst, RoundRobin, LeastLoad): ").strip()
    if policy not in ["PickFirst", "RoundRobin", "LeastLoad"]:
        print("[ERROR] Invalid policy. Please choose from PickFirst, RoundRobin, or LeastLoad.")
    else:
        serve(policy)
