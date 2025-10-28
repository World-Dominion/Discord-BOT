import logging
import os
from datetime import datetime

class GameLogger:
    def __init__(self):
        # Créer le dossier logs s'il n'existe pas
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Configuration du logger
        self.logger = logging.getLogger('WorldDominion')
        self.logger.setLevel(logging.INFO)
        
        # Formateur
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler pour fichier
        file_handler = logging.FileHandler(
            f'logs/world_dominion_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setFormatter(formatter)
        
        # Handler pour console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Ajouter les handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log d'information"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log d'avertissement"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log d'erreur"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log de debug"""
        self.logger.debug(message)
    
    def log_command(self, user_id: str, username: str, command: str, success: bool = True):
        """Logger l'utilisation d'une commande"""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"COMMAND {status} - User: {username} ({user_id}) - Command: {command}")
    
    def log_database_operation(self, operation: str, table: str, success: bool = True):
        """Logger une opération de base de données"""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"DB {status} - Operation: {operation} - Table: {table}")
    
    def log_game_event(self, event_type: str, description: str, country_id: str = None):
        """Logger un événement de jeu"""
        country_info = f" - Country: {country_id}" if country_id else ""
        self.info(f"GAME_EVENT - Type: {event_type} - {description}{country_info}")

# Instance globale
logger = GameLogger()
