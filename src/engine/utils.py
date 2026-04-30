from typing import List
from src.engine.models import TraceStep

class Tracer:
    """
    计算追踪器：用于收集排盘过程中的所有推导路径。
    使用 thread-local 或在排盘生命周期内传递。
    """
    def __init__(self):
        self._steps: List[TraceStep] = []

    def record(self, module: str, desc: str, value: float = None):
        step = TraceStep(module=module, desc=desc, value=value)
        self._steps.append(step)

    def get_steps(self) -> List[TraceStep]:
        return self._steps

    def clear(self):
        self._steps = []
