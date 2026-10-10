"""
Audiobook playback CLI utility.
Plays generated wav files sequentially or by page.
"""
import sys
import time
from pathlib import Path

# Implementation note: see the surrounding code for the behavior described here.
if sys.platform == "win32":
    try:
        reconfig = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfig):
            reconfig(encoding="utf-8")
        reconfig_err = getattr(sys.stderr, "reconfigure", None)
        if callable(reconfig_err):
            reconfig_err(encoding="utf-8")
    except Exception:
        pass

import winsound
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lektor.infrastructure.config import settings

def format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def play_audiobook(
    audio_dir: str | Path | None = None,
    start_index: int = 0,
    poll_interval: float = 1.0
) -> None:
    folder = Path(audio_dir) if audio_dir is not None else settings.data_paths.audio_dir
    print("\n" + "â•" * 70, flush=True)
    print("  đźŽ§ LIVE AUDIOBOOK PLAYER â€” AUTOMATYCZNE ODTWARZANIE STRON", flush=True)
    print(f"  â€˘ Katalog nagraĹ„: {folder.resolve()}", flush=True)
    print("  â€˘ Tryb: natychmiastowe odtwarzanie po ukoĹ„czeniu syntezy", flush=True)
    print("â•" * 70 + "\n", flush=True)

    current_idx = start_index
    waiting_logged = False

    try:
        while True:
            expected_filename = f"page_{current_idx:03d}.wav"
            file_path = folder / expected_filename

            # Implementation note: see the surrounding code for the behavior described here.
            if file_path.exists() and file_path.stat().st_size > 1000:
                # Implementation note: see the surrounding code for the behavior described here.
                time.sleep(0.2)
                
                try:
                    info = sf.info(str(file_path))
                    duration_str = format_duration(info.duration)
                except Exception:
                    duration_str = "??:??"

                # Implementation note: see the surrounding code for the behavior described here.
                txt_preview = ""
                txt_path = folder / f"page_{current_idx:03d}_normalized.txt"
                if txt_path.exists():
                    try:
                        lines = txt_path.read_text(encoding="utf-8").splitlines()
                        for line in lines:
                            if "]" in line:
                                content = line.split("]", 2)[-1].strip()
                                if content:
                                    txt_preview = content[:60] + "..." if len(content) > 60 else content
                                    break
                    except Exception:
                        pass

                print("â”Ś" + "â”€" * 68 + "â”", flush=True)
                print(f"â”‚  â–¶ď¸Ź  ODTWARZANIE: {expected_filename} (Czas: {duration_str})", flush=True)
                if txt_preview:
                    print(f"â”‚      Tekst: {txt_preview}", flush=True)
                print("â””" + "â”€" * 68 + "â”", flush=True)

                # Implementation note: see the surrounding code for the behavior described here.
                winsound.PlaySound(str(file_path.resolve()), winsound.SND_FILENAME)
                
                current_idx += 1
                waiting_logged = False
            else:
                # Implementation note: see the surrounding code for the behavior described here.
                if not waiting_logged:
                    print(f"âŹł Czekam na wygenerowanie: {expected_filename} przez lektora...", flush=True)
                    waiting_logged = True
                time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n\n[Player] Odtwarzanie zatrzymane przez uĹĽytkownika.", flush=True)
    except Exception as e:
        print(f"\n[Player] BĹ‚Ä…d odtwarzania: {e}", flush=True)

if __name__ == "__main__":
    dir_arg = sys.argv[1] if len(sys.argv) > 1 else None
    start_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    play_audiobook(audio_dir=dir_arg, start_index=start_arg)
