from flask import Flask
import os
import threading
import logging

logger = logging.getLogger("Modmail")

class KeepAliveServer:
    """Lightweight Flask server to prevent suspension"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.thread = None
        self.port = int(os.getenv("PORT", 8000))
        
        @self.app.route('/')
        def home():
            return '<div align="center">Bot is alive</div>'
            
        @self.app.route('/health')
        def health():
            return '', 200

    def start(self):
        """Start in background thread"""
        if not self.is_running():
            self.thread = threading.Thread(
                target=self.app.run,
                kwargs={'host': '0.0.0.0', 'port': self.port},
                daemon=True
            )
            self.thread.start()
            logger.info(f"Server started on port {self.port}")

    def is_running(self) -> bool:
        return self.thread and self.thread.is_alive()

    @property
    def url(self) -> str:
        return os.getenv("KOYEB_APP_URL", f"http://localhost:{self.port}")
