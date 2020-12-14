import asyncio

import attr


@attr.s
class MonitoredSubprocess:
    name: str = attr.ib()
    proc: asyncio.subprocess.Process = attr.ib()
    _stopped: bool = attr.ib(init=False, default=False)
    _early_exited: bool = attr.ib(init=False, default=False)

    # _monitor() blocks until proc exits.
    #
    # An exception raised in _monitor_task won't automatically break
    # the loop -- it must be awaited to receive that exception (=
    # promise rejection).
    #
    # We provide check() as a non-blocking way to check that the
    # process is still running.
    #
    # We can await the task in wait() (also blocking), and then
    # check().

    def __attrs_post_init__(self):
        self._monitor_task = asyncio.get_event_loop().create_task(self._monitor())

    async def _monitor(self):
        await self.proc.wait()
        if not self._stopped:
            self._early_exited = True

    async def stop(self):
        self._stopped = True
        self.proc.terminate()
        await self.wait()

    async def wait(self):
        await self._monitor_task
        await self.check()

    async def check(self):
        if self._early_exited:
            raise RuntimeError(
                f"Process {self.name} {self.proc.pid} exited before expected: {self.proc.returncode}"
            )
