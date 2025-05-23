import json
import random
import ipaddress
from collections import defaultdict, namedtuple

Route = namedtuple("Route", ["destination", "next_hop", "metric"])

MAX_METRIC = 16

class Router:
    def __init__(self, ip):
        self.ip = ip
        self.neighbors = set()
        self.routing_table = {}

    def add_neighbor(self, neighbor_ip):
        self.neighbors.add(neighbor_ip)

    def initialize_routing_table(self):
        self.routing_table[self.ip] = Route(destination=self.ip, next_hop=self.ip, metric=0)
        for neighbor in self.neighbors:
            self.routing_table[neighbor] = Route(destination=neighbor, next_hop=neighbor, metric=1)

    def update_routing_table(self, neighbor_ip, neighbor_table):
        updated = False
        for dest, route in neighbor_table.items():
            if dest == self.ip:
                continue

            new_metric = min(route.metric + 1, MAX_METRIC)
            if dest not in self.routing_table:
                self.routing_table[dest] = Route(dest, neighbor_ip, new_metric)
                updated = True
            else:
                current_route = self.routing_table[dest]
                if new_metric < current_route.metric:
                    self.routing_table[dest] = Route(dest, neighbor_ip, new_metric)
                    updated = True
        return updated

    def print_table(self):
        print(f"\nFinal state of router {self.ip} table:")
        print(f"{'Source IP':<18}{'Destination IP':<20}{'Next Hop':<20}{'Metric':<10}")
        for dest, route in sorted(self.routing_table.items()):
            print(f"{self.ip:<18}{dest:<20}{route.next_hop:<20}{route.metric:<10}")

class Network:
    def __init__(self):
        self.routers = {}

    def load_from_json(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            for ip, neighbors in data["routers"].items():
                self.routers[ip] = Router(ip)
            for ip, neighbors in data["routers"].items():
                for neighbor in neighbors:
                    self.routers[ip].add_neighbor(neighbor)

    def generate_random(self, num_routers=5, max_neighbors=3):
        ips = [str(ipaddress.IPv4Address(random.randint(0x0B000001, 0xDF000000))) for _ in range(num_routers)]
        for ip in ips:
            self.routers[ip] = Router(ip)
        for ip in ips:
            neighbors = random.sample([x for x in ips if x != ip], random.randint(1, min(max_neighbors, len(ips)-1)))
            for neighbor in neighbors:
                self.routers[ip].add_neighbor(neighbor)
                self.routers[neighbor].add_neighbor(ip)

    def simulate_rip(self, max_iterations=10):
        for router in self.routers.values():
            router.initialize_routing_table()

        for iteration in range(max_iterations):
            print(f"\n--- RIP Iteration {iteration+1} ---")
            updated = False
            for router in self.routers.values():
                for neighbor_ip in router.neighbors:
                    neighbor_router = self.routers[neighbor_ip]
                    if router.update_routing_table(neighbor_ip, neighbor_router.routing_table):
                        updated = True
            if not updated:
                print("No updates in this iteration. RIP converged.")
                break

    def print_all_tables(self):
        for router in self.routers.values():
            router.print_table()

def main():
    net = Network()
    choice = input("Load topology from JSON (1) or generate randomly (2)? ")

    if choice == "1":
        filename = "routers.json"
        net.load_from_json(filename)
    else:
        num_routers = int(input("Enter number of routers: "))
        net.generate_random(num_routers)

    net.simulate_rip()
    net.print_all_tables()

if __name__ == "__main__":
    main()
