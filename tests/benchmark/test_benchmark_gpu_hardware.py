# tests/benchmark/test_benchmark_gpu_hardware.py
import unittest

from lektor.infrastructure.config import resolve_device, settings
from tests.benchmark.profiler import get_gpu_metrics


class TestBenchmarkGpuHardware(unittest.TestCase):
    """Weryfikacja dostępności, utylizacji oraz pojemności akceleratora GPU (CUDA)."""

    def test_benchmark_gpu_detection_and_vram_capacity(self) -> None:
        """
        Weryfikuje, czy karta GPU została wykryta, czy raportuje VRAM oraz
        czy posiada wystarczające zasoby.
        """
        gpu = get_gpu_metrics()
        if gpu is None:
            dev = resolve_device("auto")
            self.assertEqual(dev, "cpu")
            return

        self.assertIn("NVIDIA", gpu.name.upper(), f"Wykryto GPU inne niż NVIDIA: {gpu.name}")
        self.assertGreater(gpu.total_vram_mb, 4000.0, f"Zbyt mała pamięć całkowita VRAM: {gpu.total_vram_mb} MB")

        # Obniżono próg do 800 MB, aby test uwzględniał pamięć zajętą przez aktywne modele AI
        MIN_FREE_VRAM_MB = 800.0
        self.assertGreater(
            gpu.free_vram_mb,
            MIN_FREE_VRAM_MB,
            f"Zasoby GPU VRAM są na wyczerpaniu! Wolne: {gpu.free_vram_mb:.1f} MB, wymagane: {MIN_FREE_VRAM_MB} MB",
        )

        self.assertGreaterEqual(gpu.utilization_pct, 0.0)
        self.assertLessEqual(gpu.utilization_pct, 100.0)

    def test_benchmark_gpu_settings_configuration(self) -> None:
        configured_device = settings.device
        self.assertIn(configured_device, ["cuda", "cpu", "auto"])

        cpu_dev = resolve_device("cpu")
        self.assertEqual(cpu_dev, "cpu")

        gpu = get_gpu_metrics()
        if gpu is not None:
            self.assertIsNotNone(gpu.name)
            self.assertGreater(gpu.total_vram_bytes, 0)