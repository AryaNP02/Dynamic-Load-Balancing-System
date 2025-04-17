import grpc
import time
import threading
from concurrent import futures
import consul

import server_pb2
import server_pb2_grpc
import loadbalancer_pb2
import loadbalancer_pb2_grpc



class BackendService(server_pb2_grpc.BackendServiceServicer):
    def __init__(self):
        self.client_count = 0  
        self.lock = threading.Lock() 

    def ProcessRequest(self, request, context):
        """Handles client request and updates client count."""
        with self.lock:
            self.client_count += 1 

        print(self.client_count)
        result = f"Processed: {request.data}"
        print(f"[INFO] Request processed: {request.data}")

        
        return server_pb2.Response(result=result)


def register_with_lb(lb_address, server_address):
    
    with grpc.insecure_channel(lb_address) as channel:
        stub = loadbalancer_pb2_grpc.LoadBalancerStub(channel)
        response = stub.RegisterServer(loadbalancer_pb2.ServerInfo(address=server_address))
        if response.success:
            print(f"[INFO] Successfully registered with LB at {lb_address}")
        else:
            print(f"[ERROR] Failed to register with LB at {lb_address}")


def report_load(lb_address, server):
   
    while True:
        with server.lock:
            print( server.client_count)
            load = server.client_count  #

        with grpc.insecure_channel(lb_address) as channel:
            stub = loadbalancer_pb2_grpc.LoadBalancerStub(channel)  
            response = stub.ReportLoad(loadbalancer_pb2.LoadReport(address=server.server_address, load=load))
            if response.success:
                print(f"[INFO] Reported load {load} to LB at {lb_address}")
            else:
                print(f"[ERROR] Failed to report load to LB")

        time.sleep(3)


def register_with_consul(service_name, address, port, consul_host="localhost", consul_port=8500):
    c = consul.Consul(host=consul_host, port=consul_port)
    c.agent.service.register(
        name=service_name,
        service_id=f"{service_name}-{address}-{port}",
        address=address,
        port=int(port),
        check=consul.Check.tcp(address, int(port), "10s")
    )
    print(f"[INFO] Registered with Consul as {service_name} at {address}:{port}")


def serve(server_address, lb_address):
 
    server = BackendService()
    server.server_address = server_address


    host, port = server_address.split(":")
    register_with_consul("backendserver", host, port)

    register_with_lb(lb_address, server_address)

 
    threading.Thread(target=report_load, args=(lb_address, server), daemon=True).start()

    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    server_pb2_grpc.add_BackendServiceServicer_to_server(server, grpc_server)
    grpc_server.add_insecure_port(server_address)
    print(f"[INFO] Backend Server started at {server_address}")

    grpc_server.start()
    grpc_server.wait_for_termination()


if __name__ == "__main__":
   
    port = input("Enter server port (e.g., 50052): ").strip()
    SERVER_ADDRESS = f"localhost:{port}"
    LB_ADDRESS = "localhost:50051"

    serve(SERVER_ADDRESS, LB_ADDRESS)
