"""
lektor.__main__
~~~~~~~~~~~~~~~
Main application entry point (Composition Root).
Initializes the infrastructure container and delegates execution to the appropriate adapter (CLI or GUI).
"""

import sys

from .infrastructure.config import settings
from .infrastructure.container import default_container


def run() -> None:
    args = sys.argv[1:]

    # Implementation note: see the surrounding code for the behavior described here.
    if args and args[0] in ("gui", "serve", "web"):
        import uvicorn
        from .infrastructure.gui_app import app
        uvicorn.run(
            app,
            host=settings.gui_host,
            port=settings.gui_port,
        )
        return

    # Implementation note: see the surrounding code for the behavior described here.
    from .adapters.cli.main import main as cli_main

    exit_code = cli_main(
        args_list=args,
        container=default_container,
        default_audio_dir=str(settings.data_paths.audio_dir),
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
