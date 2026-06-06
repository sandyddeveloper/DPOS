"""
App entry point — boots everything.
"""
import sys
from app import App

def main():
    """Main application entry point."""
    if "--scan" in sys.argv:
        print("Running DPOS background filesystem scan...")
        from core.database import init_db, SessionLocal
        from app import scan_and_update_projects
        init_db()
        session = SessionLocal()
        try:
            scan_and_update_projects(session)
            print("Background scan complete.")
        except Exception as e:
            print(f"Error during background scan: {e}")
            sys.exit(1)
        finally:
            session.close()
        sys.exit(0)

    app = App()
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
