import sys
import _thread
import threading
from enum import Enum


MAX_PID = 1


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

    def start(self):
        while not self.terminated.is_set():
            pass

    def stop(self):
        self.terminated.set()


def init_processes(n):
    return [Process(i + 1, Role.PRIMARY if i == 0 else Role.SECONDARY) for i in range(n)]


if __name__ == '__main__':
    N = int(sys.argv[1])
    if N <= 0:
        print('Number of processes should be positive integer.')
        exit(1)
    processes = init_processes(N)
    MAX_PID = N + 1
    for p in processes:
        _thread.start_new_thread(p.start, ())
    while True:
        command = input('$ ').split(' ')
        if command[0] == 'actual-order':
            order = command[1]
        elif command[0] == 'g-state':
            if len(command) > 1:
                pid = int(command[1])
                state = State.NF if command[1] == 'non-faulty' else State.F
                for p in processes:
                    if p.pid == pid:
                        p.state = state
            else:
                p_list = [f'G{p.pid}, {p.role.name.lower()}, state={p.state.name}' for p in processes]
                print(*p_list, sep='\n')
        elif command[0] == 'g-kill':
            pid = int(command[1])
            for i, p in enumerate(processes):
                if p.pid == pid:
                    processes.pop(i)
                    if p.role == Role.PRIMARY:
                        processes[0].role = Role.PRIMARY
        elif command[0] == 'g-add':
            n = int(command[1])
            for i in range(n):
                processes.append(Process(MAX_PID, Role.SECONDARY))
                _thread.start_new_thread(processes[-1].start, ())
                MAX_PID += 1
        elif command[0] in ['exit', 'quit']:
            break
        else:
            print('Unknown command')
    for p in processes:
        p.stop()
