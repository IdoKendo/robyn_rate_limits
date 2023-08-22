import contextlib
import os
import pathlib
import platform
import signal
import socket
import subprocess
import time
from dataclasses import dataclass
from typing import List

import pytest
from robyn import Request


def spawn_process(command: List[str]) -> subprocess.Popen:
    if platform.system() == "Windows":
        command[0] = "python"
        process = subprocess.Popen(
            command,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # type: ignore
        )
        return process
    process = subprocess.Popen(command, preexec_fn=os.setsid)
    return process


def kill_process(process: subprocess.Popen) -> None:
    if platform.system() == "Windows":
        process.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore
        process.kill()
        return

    with contextlib.suppress(ProcessLookupError):
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)


def start_server(domain: str, port: int) -> subprocess.Popen:
    """
    Call this method to wait for the server to start
    """
    # Start the server
    current_file_path = pathlib.Path(__file__).parent.resolve()
    base_routes = os.path.join(current_file_path, "./base_routes.py")
    command = ["python3", base_routes]
    process = spawn_process(command)

    # Wait for the server to be reachable
    timeout = 5  # The maximum time we will wait for an answer
    start_time = time.time()
    while True:
        current_time = time.time()
        if current_time - start_time > timeout:
            # Robyn didn't start correctly before timeout
            kill_process(process)
            raise ConnectionError("Could not reach Robyn server")
        try:
            sock = socket.create_connection((domain, port), timeout=5)
            sock.close()
            break  # We were able to reach the server, exit the loop
        except Exception:
            pass
    return process


@pytest.fixture()
def _session():
    domain = "127.0.0.1"
    port = 8080
    os.environ["ROBYN_URL"] = domain
    process = start_server(domain, port)
    yield
    kill_process(process)


@pytest.fixture()
def mock_request():
    @dataclass
    class Url:
        scheme: str
        host: str
        path: str

    request = Request
    request.queries = {}
    request.headers = {}
    request.path_params = {}
    request.body = ""
    request.method = "GET"
    request.url = Url(  # type: ignore
        scheme="https",
        host="127.0.0.1",
        path="/test",
    )
    request.ip_addr = "127.0.0.1"
    return request
