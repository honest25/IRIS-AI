"""
IRIS AI — Desktop Agent: System Tray
Provides a system tray icon for quick access to IRIS functions.
"""
import threading
import sys
from typing import Callable, Optional


def create_tray_icon(
    on_connect: Callable,
    on_disconnect: Callable,
    on_quit: Callable,
    get_status: Callable[[], str],
):
    """
    Create and run the system tray icon.
    This blocks, so run in a separate thread.
    
    Requires: pip install pystray Pillow
    """
    try:
        import pystray
        from PIL import Image, ImageDraw

        def _make_icon(connected: bool) -> Image.Image:
            """Generate a simple circular icon."""
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            color = (74, 224, 255, 255) if connected else (100, 100, 100, 255)
            draw.ellipse([8, 8, 56, 56], fill=color)
            # Inner circle
            draw.ellipse([20, 20, 44, 44], fill=(5, 10, 18, 255))
            # Center dot
            dot_color = (57, 255, 154, 255) if connected else (255, 74, 110, 255)
            draw.ellipse([28, 28, 36, 36], fill=dot_color)
            return img

        icon_img = _make_icon(False)

        def _on_connect_action(icon, item):
            on_connect()
            icon.icon = _make_icon(True)

        def _on_disconnect_action(icon, item):
            on_disconnect()
            icon.icon = _make_icon(False)

        def _on_quit_action(icon, item):
            icon.stop()
            on_quit()

        menu = pystray.Menu(
            pystray.MenuItem("IRIS AI", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Connect", _on_connect_action),
            pystray.MenuItem("Disconnect", _on_disconnect_action),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", _on_quit_action),
        )

        icon = pystray.Icon(
            "IRIS AI",
            icon=icon_img,
            title="IRIS AI Desktop Agent",
            menu=menu,
        )
        icon.run()

    except ImportError:
        print("[IRIS Tray] pystray or Pillow not installed. Tray icon disabled.")
        print("[IRIS Tray] Install: pip install pystray Pillow")
