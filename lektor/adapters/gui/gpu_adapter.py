"""
lektor.adapters.gui.gpu_adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~
GPU telemetry adapter querying NVIDIA driver parameters via nvidia-smi.
"""

import shutil
import subprocess

from ...application.ports.telemetry_ports import GpuTelemetryProtocol


class NvidiaSmiGpuTelemetryAdapter(GpuTelemetryProtocol):
    """Queries NVIDIA driver for VRAM memory and GPU core utilization."""

    def get_gpu_stats(self) -> tuple[float, float, float]:
        """Returns tuple: (used_vram_mb, total_vram_mb, gpu_utilization_pct)."""
        nvidia_smi = shutil.which("nvidia-smi")
        if not nvidia_smi:
            return 0.0, 0.0, 0.0

        try:
            cmd = [
                nvidia_smi,
                "--query-gpu=memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=2.0)
            parts = [p.strip() for p in res.stdout.strip().split(",")]
            if len(parts) >= 3:
                used_mb = float(parts[0])
                total_mb = float(parts[1])
                util_pct = float(parts[2])
                return used_mb, total_mb, util_pct
        except Exception:
            pass

        return 0.0, 0.0, 0.0
