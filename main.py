import sys
import _thread
import threading
from enum import Enum


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
    for p in processes:
        _thread.start_new_thread(p.start, ())
    while True:
        command = input('$ ').split(' ')
        if command[0] == 'g-state':
            if len(command) == 1:
                p_list = [f'G{p.pid}, {p.role.name.lower()}, state={p.state.name}' for p in processes]
                print(*p_list, sep='\n')
            else:
                pid = int(command[1])
                state = State.NF if command[1] == 'non-faulty' else State.F
        elif command[0] in ['exit', 'quit']:
            break
        else:
            print('Unknown command')
    for p in processes:
        p.stop()
