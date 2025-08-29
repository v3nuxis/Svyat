import os
import subprocess

class UberClient:
    def __init__(self, order_id: int):
        self.order_id = order_id
        self.simulator_process = None

    def start_delivery(self):
        simulator_path = os.path.join(
            os.path.dirname(__file__),
            "../../tests/providers/uber.py"
        )
        self.simulator_process = subprocess.Popen(
            ["python", simulator_path, str(self.order_id)]
        )

    def stop_delivery(self):
        if self.simulator_process:
            self.simulator_process.terminate()
