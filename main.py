import sys
import socket
import _thread
import threading
import numpy as np
from enum import Enum
from collections import Counter


MAX_PID = 1
LOCALHOST = '127.0.0.1'
ZERO_PORT = 20000
PORTS = []


class State(Enum):
    NF = 0,
    F = 1


class Role(Enum):
    PRIMARY = 0,
    SECONDARY = 1


class Process:

    def __init__(self, pid: int, role: Role):
        self.pid = pid
        self.state = State.NF
        self.role = role
        self.terminated = threading.Event()
        self.port = ZERO_PORT + pid
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((LOCALHOST, self.port))
        self.socket.listen()

    def receive_order(self, order: str):
        if self.role == Role.PRIMARY:
            self.broadcast(order)

    def broadcast(self, order: str):
        message = self.generate_order(order)
        for port in PORTS[1:]:
            if port != self.port:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((LOCALHOST, port))
                sock.send(message)

    def generate_order(self, order: str):
        if self.state == State.F:
            order = np.random.choice(['attack', 'retreat'])
        return f'{"P" if self.role == Role.PRIMARY else "S"} {order}'.encode()

    def start(self):
        received_orders = []
        while not self.terminated.is_set():
            if self.role == Role.SECONDARY:
                conn, _ = self.socket.accept()
                from_, order = conn.recv(1024).decode().split(' ')
                if from_ == 'P':
                    received_orders.append(order)
                    self.broadcast(order)
                else:
                    received_orders.append(order)
                    if len(received_orders) == len(PORTS) - 1:
                        order = Counter(received_orders).most_common(1)[0][0]
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.connect((LOCALHOST, ZERO_PORT))
                        sock.send(f'{self.pid} {order}'.encode())
                        received_orders = []
        self.socket.close()

    def stop(self):
        self.terminated.set()


def init_processes(n: int):
    return [Process(i + 1, Role.PRIMARY if i == 0 else Role.SECONDARY) for i in range(n)]


def get_process(processes: list, pid: int):
    for p in processes:
        if p.pid == pid:
            return p


def manage_states(command: list, processes: list):
    if len(command) > 1:
        pid = int(command[1])
        state = State.NF if command[2] == 'non-faulty' else State.F
        p = get_process(processes, pid)
        p.state = state
    else:
        p_list = [f'G{p.pid}, {p.role.name.lower()}, state={p.state.name}' for p in processes]
        print(*p_list, sep='\n')


def kill_process(command: list, processes: list):
    pid = int(command[1])
    for i, p in enumerate(processes):
        if p.pid == pid:
            processes.pop(i)
            PORTS.pop(i)
            if p.role == Role.PRIMARY:
                processes[0].role = Role.PRIMARY


def add_processes(command: list, processes: list):
    global MAX_PID
    n = int(command[1])
    for i in range(n):
        processes.append(Process(MAX_PID, Role.SECONDARY))
        _thread.start_new_thread(processes[-1].start, ())
        PORTS.append(ZERO_PORT + MAX_PID)
        MAX_PID += 1


if __name__ == '__main__':
    N = int(sys.argv[1])
    if N <= 0:
        print('Number of processes should be positive integer.')
        exit(1)
    processes = init_processes(N)
    MAX_PID = N + 1
    PORTS = [ZERO_PORT + i + 1 for i in range(N)]
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.bind((LOCALHOST, ZERO_PORT))
    client_socket.listen()
    for p in processes:
        _thread.start_new_thread(p.start, ())
    while True:
        command = input('$ ').split(' ')
        if command[0] == 'actual-order':
            p_num = len(processes)
            f_num = len([p for p in processes if p.state == State.F])
            if f_num * 3 + 1 > p_num:
                print('Execute order: cannot be determined – not enough generals ' +
                      f'in the system! {f_num} faulty node{"s" if f_num > 1 else ""} in the ' +
                      f'system - {p_num - f_num} out of {p_num} quorum not consistent')
            else:
                order = command[1]
                processes[0].receive_order(order)
                results = {processes[0].pid: order}
                while len(results) < len(processes):
                    conn, _ = client_socket.accept()
                    pid, result = conn.recv(1024).decode().split(' ')
                    results[int(pid)] = result
                for p in processes:
                    print(f'G{p.pid}, {p.role.name.lower()}, majority={results[p.pid]}, state={p.state.name}')
                valid_results = [v for k, v in results.items() if k != processes[0].pid and
                                 get_process(processes, k).state != State.F]
                consensus, n_agree = Counter(valid_results).most_common(1)[0]
                print(f'Execute order: {consensus}! {f_num if f_num else "No"} faulty nodes in the system – ' +
                      f'{n_agree} out of {len(processes)} quorum suggest {consensus}')
        elif command[0] == 'g-state':
            manage_states(command, processes)
        elif command[0] == 'g-kill':
            kill_process(command, processes)
        elif command[0] == 'g-add':
            add_processes(command, processes)
        elif command[0] in ['exit', 'quit']:
            break
        else:
            print('Unknown command')
    client_socket.close()
    for p in processes:
        p.stop()
