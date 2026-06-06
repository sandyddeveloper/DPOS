"""
pyperclip poll loop (background thread).
"""
import time
import threading
import pyperclip

from core.models import ClipEntry
from modules.search.providers import clip_provider

_monitor_thread = None
_running = False

def start_clipboard_monitor(session_factory):
    """Start the background clipboard polling thread."""
    global _monitor_thread, _running
    if _running:
        return

    _running = True

    def poll_loop():
        last_val = ""
        try:
            last_val = pyperclip.paste()
        except Exception:
            pass

        while _running:
            try:
                curr_val = pyperclip.paste()
                # If clipboard content is non-empty and has changed
                if curr_val and curr_val != last_val:
                    last_val = curr_val

                    # Save to SQLite database
                    session = session_factory()
                    try:
                        clip = ClipEntry(content=curr_val)
                        session.add(clip)
                        session.commit()
                        session.refresh(clip)

                        # Write to Whoosh index
                        clip_provider.index_entry(clip)
                    except Exception as e:
                        session.rollback()
                        print(f"Clipboard monitor database write failed: {e}")
                    finally:
                        session.close()
            except Exception as e:
                # Handle temporary OS clipboard locking errors gracefully
                pass

            time.sleep(1.0)

    _monitor_thread = threading.Thread(
        target=poll_loop, 
        name="DPOS-Clipboard-Monitor", 
        daemon=True
    )
    _monitor_thread.start()
    print("Clipboard Monitor active.")

def stop_clipboard_monitor():
    """Stop the background clipboard polling thread."""
    global _running
    _running = False
