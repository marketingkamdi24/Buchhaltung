"""
UI module for Buchhaltung.
"""

# Defer imports to avoid circular import issues
__all__ = ["create_app", "main"]

def create_app():
    """Create the Gradio application."""
    from .app import create_app as _create_app
    return _create_app()

def main():
    """Main entry point."""
    from .app import main as _main
    return _main()