import multiprocessing
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import TracebackType

from tblib import pickling_support

pickling_support.install()

#
# This file taken from https://github.com/cdzombak/driveway-monitor
#


@dataclass
class ChildExit:
    exc_info: (
        tuple[type[BaseException], BaseException, TracebackType]
        | tuple[None, None, None]
    )
    pid: int
    class_name: str
    error: str

    def is_exc(self) -> bool:
        return self.exc_info[0] is not None


class ChildProcess(ABC):
    @abstractmethod
    def _run(self):
        raise NotImplementedError

    def run(self, ex_queue: multiprocessing.Queue):
        ex_record: ChildExit | None = None

        try:
            self._run()
        except Exception as e:  # noqa: BLE001 - forward any child failure to the parent
            ex_record = ChildExit(
                exc_info=sys.exc_info(),
                pid=multiprocessing.current_process().pid,
                class_name=self.__class__.__name__,
                error=str(e),
            )

        if not ex_record:
            ex_record = ChildExit(
                exc_info=(None, None, None),
                pid=multiprocessing.current_process().pid,
                class_name=self.__class__.__name__,
                error="exited normally.",
            )

        try:
            ex_queue.put(ex_record)
        except Exception as e:  # noqa: BLE001 - last resort before process exit
            print("PANIC:ex_queue.put exception:", e)
            sys.exit(1)
