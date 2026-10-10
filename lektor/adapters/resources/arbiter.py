"""GPU VRAM arbiter adapter managing model lifecycle and preemption."""

from __future__ import annotations

import gc
import subprocess
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Sequence
from collections.abc import Generator

import httpx
import torch

from ...application.ports.audio_ports import TTSEngineProtocol
from ...application.ports.resource_ports import (
    AIModelArbiterProtocol,
    AIModelHandleProtocol,
)
from ...domain.resource_models import (
    ModelResourceId,
    ModelSlotId,
    VramSnapshot,
)


class ProcessModelHandle(AIModelHandleProtocol):
    """Handle controlling lifecycle of a model running as an external server process."""

    def __init__(
        self,
        slot_id: ModelSlotId,
        resource_id: ModelResourceId,
        executable_path: Path,
        args: Sequence[str],
        health_check_url: str = "http://127.0.0.1:1234/v1/models",
        process_name_for_kill: str = "llama-server.exe",
        startup_timeout_sec: float = 45.0,
    ) -> None:
        self._slot_id = slot_id
        self._resource_id = resource_id
        self._executable_path = executable_path
        self._args = list(args)
        self._health_check_url = health_check_url
        self._process_name = process_name_for_kill
        self._startup_timeout_sec = startup_timeout_sec
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._lock = threading.Lock()

    @property
    def slot_id(self) -> ModelSlotId:
        return self._slot_id

    @property
    def resource_id(self) -> ModelResourceId:
        return self._resource_id

    def is_loaded(self) -> bool:
        """Weryfikuje, czy serwer modelu odpowiada na zapytania HTTP."""
        try:
            with httpx.Client(timeout=0.8) as client:
                res = client.get(self._health_check_url)
                return res.status_code == 200
        except Exception:
            return False

    def load(self) -> None:
        """Loads weights and initializes model."""
        with self._lock:
            if self.is_loaded():
                print(f"[ProcessHandle/{self._slot_id}] Model {self._resource_id} jest juĹĽ aktywny w pamiÄ™ci GPU.")
                return

            if not self._executable_path.exists():
                print(f"[ProcessHandle/{self._slot_id}] Plik wykonywalny serwera nie istnieje: {self._executable_path}")
                return

            cmd: list[str] = [str(self._executable_path)] + self._args
            print(f"[ProcessHandle/{self._slot_id}] Uruchamianie serwera modelu AI: {self._resource_id}...")

            # Implementation note: see the surrounding code for the behavior described here.
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )

            # Implementation note: see the surrounding code for the behavior described here.
            deadline = time.time() + self._startup_timeout_sec
            while time.time() < deadline:
                if self.is_loaded():
                    print(f"[ProcessHandle/{self._slot_id}] Model {self._resource_id} zaĹ‚adowany pomyĹ›lnie na GPU!")
                    return
                time.sleep(0.5)

            print(f"[ProcessHandle/{self._slot_id}] OstrzeĹĽenie: Timeout podczas oczekiwania na model {self._resource_id}.")

    def unload(self) -> None:
        """Unloads model instance and clears VRAM memory."""
        with self._lock:
            print(f"[ProcessHandle/{self._slot_id}] Zamykanie serwera {self._resource_id} i zwalnianie VRAM...")
            if self._process is not None:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=4.0)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
                self._process = None

            # Implementation note: see the surrounding code for the behavior described here.
            if self._process_name:
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/IM", self._process_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                except Exception:
                    pass

            time.sleep(0.5)
            print(f"[ProcessHandle/{self._slot_id}] PamiÄ™Ä‡ VRAM zwolniona po procesie {self._resource_id}.")


class PyTorchModelHandle(AIModelHandleProtocol):
    """Handle controlling model loaded directly in Python process memory."""

    def __init__(
        self,
        slot_id: ModelSlotId,
        resource_id: ModelResourceId,
        engine: TTSEngineProtocol,
    ) -> None:
        self._slot_id = slot_id
        self._resource_id = resource_id
        self._engine = engine
        self._lock = threading.Lock()

    @property
    def slot_id(self) -> ModelSlotId:
        return self._slot_id

    @property
    def resource_id(self) -> ModelResourceId:
        return self._resource_id

    def is_loaded(self) -> bool:
        return self._engine.is_loaded()

    def load(self) -> None:
        with self._lock:
            if not self._engine.is_loaded():
                print(f"[PyTorchHandle/{self._slot_id}] Ĺadowanie wag modelu {self._resource_id} do pamiÄ™ci GPU...")
                self._engine.load_model()

    def unload(self) -> None:
        with self._lock:
            print(f"[PyTorchHandle/{self._slot_id}] WyĹ‚adowywanie modelu {self._resource_id} z pamiÄ™ci GPU...")
            self._engine.unload_model()
            if torch is not None and torch.cuda.is_available():
                gc.collect()
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
            print(f"[PyTorchHandle/{self._slot_id}] PamiÄ™Ä‡ VRAM wyczyszczona (PyTorch CUDA Cache cleared).")


class DynamicVramModelArbiter(AIModelArbiterProtocol):
    """Central VRAM Arbiter managing mutual exclusion of GPU models."""

    def __init__(
        self,
        handles: Sequence[AIModelHandleProtocol],
    ) -> None:
        self._handles: dict[ModelSlotId, AIModelHandleProtocol] = {
            h.slot_id: h for h in handles
        }
        self._active_slot: Optional[ModelSlotId] = None
        self._lock = threading.RLock()

    def register_handle(self, handle: AIModelHandleProtocol) -> None:
        with self._lock:
            self._handles[handle.slot_id] = handle

    def acquire(self, slot_id: ModelSlotId) -> None:
        """Leases accelerator resource for specified slot, preempting any active model."""
        with self._lock:
            handle = self._handles.get(slot_id)
            if handle is None:
                raise ValueError(f"Nieznany slot modelu: {slot_id}")

            if self._active_slot == slot_id and handle.is_loaded():
                return

            if self._active_slot is not None and self._active_slot != slot_id:
                prev_handle = self._handles.get(self._active_slot)
                if prev_handle is not None:
                    print(
                        f"[VRAM Arbiter] WYWĹASZCZANIE: WyĹ‚adowujÄ™ model ze slotu {self._active_slot} "
                        f"na rzecz slotu {slot_id}..."
                    )
                    prev_handle.unload()
                self._active_slot = None

            print(f"[VRAM Arbiter] Przydzielam GPU dla slotu: {slot_id}...")
            handle.load()
            self._active_slot = slot_id

    def release(self, slot_id: ModelSlotId) -> None:
        """Releases GPU compute lease and frees VRAM."""
        with self._lock:
            handle = self._handles.get(slot_id)
            if handle is not None:
                handle.unload()
            if self._active_slot == slot_id:
                self._active_slot = None

    def release_all(self) -> None:
        """Releases all active models and restores clean GPU state."""
        with self._lock:
            print("[VRAM Arbiter] Zwalnianie wszystkich modeli AI z pamiÄ™ci GPU...")
            for handle in self._handles.values():
                try:
                    handle.unload()
                except Exception as e:
                    print(f"[VRAM Arbiter] BĹ‚Ä…d podczas zwalniania {handle.slot_id}: {e}")
            self._active_slot = None

    def get_active_slot(self) -> Optional[ModelSlotId]:
        with self._lock:
            return self._active_slot

    def get_vram_snapshot(self) -> VramSnapshot:
        """Retrieves current VRAM telemetry snapshot."""
        if torch is not None and torch.cuda.is_available():
            free_b, total_b = torch.cuda.mem_get_info()
            used_b = total_b - free_b
            return VramSnapshot(
                used_mb=used_b / (1024 * 1024),
                total_mb=total_b / (1024 * 1024),
                free_mb=free_b / (1024 * 1024),
            )
        return VramSnapshot(used_mb=0.0, total_mb=0.0, free_mb=0.0)

    @contextmanager
    def acquire_context(self, slot_id: ModelSlotId) -> Generator[None, None, None]:
        """Context manager guaranteeing exclusive model access within a with block."""
        self.acquire(slot_id)
        try:
            yield
        finally:
            self.release(slot_id)


__all__ = [
    "ProcessModelHandle",
    "PyTorchModelHandle",
    "DynamicVramModelArbiter",
]
