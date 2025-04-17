import grpc
import loadbalancer_pb2
import loadbalancer_pb2_grpc
import server_pb2
import server_pb2_grpc
import consul

def discover_loadbalancer(consul_host="localhost", consul_port=8500):
    c = consul.Consul(host=consul_host, port=consul_port)
    services = c.health.service("loadbalancer", passing=True)[1]
    if not services:
        return None
    # Pick the first healthy loadbalancer
    service = services[0]['Service']
    address = service['Address'] or services[0]['Node']['Address']
    port = service['Port']
    return f"{address}:{port}"

def get_best_server(lb_address):
    with grpc.insecure_channel(lb_address) as channel:
        stub = loadbalancer_pb2_grpc.LoadBalancerStub(channel)
        request = loadbalancer_pb2.ClientRequest()
        response = stub.GetServer(request)
        return response.address

def send_request(stub, data):
    request = server_pb2.Request(data=data)
    response = stub.ProcessRequest(request)
    return response.result

if __name__ == "__main__":
    LB_ADDRESS = discover_loadbalancer()
    if not LB_ADDRESS:
        print("[ERROR] No available load balancers found in Consul. Try again later.")
    else:
        print(f"[INFO] Load balancer selected: {LB_ADDRESS}")
        best_server = get_best_server(LB_ADDRESS)
        if not best_server:
            print("[ERROR] No available servers. Try again later.")
        else:
            print(f"[INFO] Best server selected: {best_server}")
            with grpc.insecure_channel(best_server) as channel:
                stub = server_pb2_grpc.BackendServiceStub(channel)
                while True:
                    user_input = input("Enter a task (or type 'exit' to quit): ").strip()
                    if user_input.lower() == "exit":
                        break
                    response = send_request(stub, user_input)
                    print(f"[INFO] Response from {best_server}: {response}")