from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import os
from supabase import create_client, Client
import json
from datetime import datetime
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('WEB_SECRET_KEY', secrets.token_hex(32))
# Socket.IO avec configuration stricte pour Render.com
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',  # Force threading mode
    logger=False,
    engineio_logger=False,
    allow_upgrades=False,  # Désactive complètement les websockets
    transports=['polling'],  # Force uniquement le polling
    ping_timeout=60,
    ping_interval=25
)

# Rate limiting simple avec dictionnaire en mémoire
from collections import defaultdict
import time

# Stockage des requêtes par IP
request_counts = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX_REQUESTS = 100  # 100 requêtes par minute par IP

def check_rate_limit():
    """Vérifie le rate limiting pour l'IP actuelle"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if not client_ip:
        client_ip = '127.0.0.1'
    
    now = time.time()
    
    # Nettoyer les anciennes requêtes
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Vérifier la limite
    if len(request_counts[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    # Ajouter la requête actuelle
    request_counts[client_ip].append(now)
    return True

def rate_limit(f):
    """Décorateur pour le rate limiting"""
    def decorated_function(*args, **kwargs):
        if not check_rate_limit():
            return jsonify({'error': 'Rate limit exceeded. Please slow down.'}), 429
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Décorateurs pour éliminer la duplication de code
def require_admin(f):
    """Décorateur pour vérifier les permissions admin"""
    def decorated_function(*args, **kwargs):
        if not is_user_admin():
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_database(f):
    """Décorateur pour vérifier la disponibilité de la base de données"""
    def decorated_function(*args, **kwargs):
        if supabase is None:
            print(f"ERREUR: Supabase non configuré pour {f.__name__}")
            return jsonify({'error': 'Database not configured'}), 500
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def handle_api_errors(f):
    """Décorateur pour la gestion d'erreurs API"""
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            log_error(f.__name__, e)
            return jsonify({'error': f'Server error: {str(e)}'}), 500
    decorated_function.__name__ = f.__name__
    return decorated_function

# Fonction utilitaire pour la gestion d'erreurs
def log_error(endpoint: str, error: Exception, context: str = ""):
    """Log détaillé des erreurs avec contexte"""
    error_type = type(error).__name__
    error_msg = str(error)
    context_info = f" - {context}" if context else ""
    print(f"ERREUR {endpoint}: {error_type}: {error_msg}{context_info}")

def validate_request_data(data: dict, required_fields: list) -> tuple[bool, str]:
    """Valide les données de requête"""
    if not data:
        return False, "Aucune donnée fournie"
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Champs manquants: {', '.join(missing_fields)}"
    
    return True, ""

# Configuration avec validation
discord_client_id = os.getenv('DISCORD_CLIENT_ID')
discord_client_secret = os.getenv('DISCORD_CLIENT_SECRET')
BASE_URL = os.getenv('RENDER_EXTERNAL_URL') or os.getenv('WEB_PANEL_URL') or os.getenv('HOST_IP', 'http://localhost:5000')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', BASE_URL + '/callback')
ADMIN_ROLE_IDS = [int(x) for x in os.getenv('ADMIN_ROLE_IDS', '').split(',') if x.strip()]

# Supabase avec vérification d'initialisation complète
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Validation des variables d'environnement critiques
def validate_environment():
    """Valide les variables d'environnement critiques"""
    errors = []
    warnings = []
    
    # Variables critiques pour Discord OAuth
    if not discord_client_id:
        errors.append("DISCORD_CLIENT_ID manquant")
    elif not discord_client_id.isdigit():
        warnings.append("DISCORD_CLIENT_ID ne semble pas être un ID Discord valide")
    
    if not discord_client_secret:
        errors.append("DISCORD_CLIENT_SECRET manquant")
    elif len(discord_client_secret) < 32:
        warnings.append("DISCORD_CLIENT_SECRET semble trop court")
    
    if not ADMIN_ROLE_IDS:
        warnings.append("ADMIN_ROLE_IDS vide - aucun utilisateur ne pourra accéder au panel")
    
    # Variables Supabase
    if not SUPABASE_URL:
        errors.append("SUPABASE_URL manquant")
    elif not SUPABASE_URL.startswith('https://'):
        warnings.append("SUPABASE_URL ne semble pas être une URL HTTPS valide")
    
    if not SUPABASE_KEY:
        errors.append("SUPABASE_KEY manquant")
    elif len(SUPABASE_KEY) < 100:
        warnings.append("SUPABASE_KEY semble trop court")
    
    # Log des problèmes
    if errors:
        print("ERREURS CRITIQUES de configuration:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("AVERTISSEMENTS de configuration:")
        for warning in warnings:
            print(f"  - {warning}")
    
    return len(errors) == 0

# Validation au démarrage
if not validate_environment():
    print("ATTENTION: Configuration incomplète détectée. Certaines fonctionnalités peuvent ne pas fonctionner.")

LOG_CHANNEL_ID = 1432369899635871894


supabase: Client = None

def initialize_database():
    """Initialise et vérifie la connexion à la base de données"""
    global supabase
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERREUR: SUPABASE_URL/SUPABASE_KEY manquants - les endpoints DB seront indisponibles")
        return False
    
    try:
        print("INFO: Initialisation de la connexion Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Test de connexion avec une requête simple
        print("INFO: Test de connexion à la base de données...")
        test_result = supabase.table('countries').select('id').limit(1).execute()
        print("SUCCESS: Connexion à la base de données établie")
        
        # Vérification des tables critiques
        required_tables = ['countries', 'players', 'wars', 'events']
        missing_tables = []
        
        for table in required_tables:
            try:
                supabase.table(table).select('id').limit(1).execute()
                print(f"SUCCESS: Table '{table}' accessible")
            except Exception as e:
                missing_tables.append(table)
                print(f"WARNING: Table '{table}' inaccessible: {str(e)}")
        
        if missing_tables:
            print(f"ATTENTION: Tables manquantes: {', '.join(missing_tables)}")
            print("Certaines fonctionnalités peuvent ne pas fonctionner correctement")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: Échec de l'initialisation Supabase: {type(e).__name__}: {str(e)}")
        supabase = None
        return False

# Initialisation de la base de données
if not initialize_database():
    print("ATTENTION: Base de données non initialisée. Le panel web sera limité.")

DISCORD_BOT_TOKEN = os.getenv('DISCORD_TOKEN')

class WebAdminManager:
    def __init__(self):
        self.bot = None
    def is_admin(self, user_data):
        if not user_data or 'guilds' not in user_data:
            print("ERREUR: Pas de données utilisateur ou guildes")
            return False
        guild_id = str(os.getenv('DISCORD_GUILD_ID'))
        print(f" Recherche dans la guilde: {guild_id}")
        print(f" Rôles admin configurés: {ADMIN_ROLE_IDS}")
        for guild in user_data['guilds']:
            print(f" Guilde trouvée: {guild['id']} - {guild.get('name', 'Inconnu')}")
            if guild['id'] == guild_id:
                user_roles = guild.get('roles', [])
                print(f" Rôles de l'utilisateur: {user_roles}")
                if not user_roles:
                    print("⚠️ Pas de rôles dans guild, tentative récupération via API")
                    try:
                        import requests
                        member_response = requests.get(
                            f'https://discord.com/api/guilds/{guild_id}/members/{user_data["id"]}',
                            headers={'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
                        )
                        if member_response.status_code == 200:
                            member_data = member_response.json()
                            user_roles = member_data.get('roles', [])
                            print(f"✅ Rôles récupérés via API: {len(user_roles)} rôles")
                        else:
                            print(f"ERREUR API: {member_response.status_code}")
                            if guild.get('permissions'):
                                permissions = int(guild.get('permissions', '0'))
                                if permissions & 0x8:
                                    print("✅ Utilisateur a les permissions admin dans la guilde")
                                    return True
                    except Exception as e:
                        print(f"ERREUR lors de la récupération des rôles: {e}")
                user_role_ids = []
                for role_id in user_roles:
                    try:
                        user_role_ids.append(int(role_id))
                    except (ValueError, TypeError):
                        pass
                print(f" Rôles convertis: {user_role_ids}")
                has_admin_role = any(role_id in ADMIN_ROLE_IDS for role_id in user_role_ids)
                print(f" A un rôle admin: {has_admin_role}")
                if has_admin_role:
                    return True
        print("ERREUR: Aucun rôle admin trouvé")
        return False
admin_manager = WebAdminManager()

def is_user_admin():
    if 'user' not in session:
        return False
    return session['user'].get('admin', False)

# Import des logs Discord améliorés
from web.discord_logs import (
    log_country_created, log_country_modified, log_country_deleted,
    log_player_modified, log_player_deleted, log_war_ended, log_war_deleted,
    log_event_triggered, log_tools_action, log_admin_give
)

def get_user_info():
    """Récupère les informations de l'utilisateur connecté"""
    return (
        session.get('user', {}).get('username', 'Inconnu'),
        session.get('user', {}).get('id', 'Inconnu')
    )

# Routes principales
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if not is_user_admin():
        return render_template('unauthorized.html')
    
    return render_template('dashboard.html')

@app.route('/api/rate-limit-status')
def rate_limit_status():
    """Retourne le statut du rate limiting pour l'IP actuelle"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if not client_ip:
        client_ip = '127.0.0.1'
    
    now = time.time()
    
    # Nettoyer les anciennes requêtes
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < RATE_LIMIT_WINDOW
    ]
    
    remaining = max(0, RATE_LIMIT_MAX_REQUESTS - len(request_counts[client_ip]))
    
    return jsonify({
        'ip': client_ip,
        'requests_used': len(request_counts[client_ip]),
        'requests_remaining': remaining,
        'window_seconds': RATE_LIMIT_WINDOW,
        'max_requests': RATE_LIMIT_MAX_REQUESTS
    })

# Health check (Render)
@app.route('/healthz')
def healthz():
    """Health check détaillé pour Render.com"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected' if supabase is not None else 'disconnected',
            'discord_oauth': 'configured' if discord_client_id and discord_client_secret else 'not_configured',
            'admin_roles': len(ADMIN_ROLE_IDS) if ADMIN_ROLE_IDS else 0
        }
        
        # Test de la base de données si disponible
        if supabase:
            try:
                supabase.table('countries').select('id').limit(1).execute()
                health_status['database_status'] = 'accessible'
            except Exception as e:
                health_status['database_status'] = 'error'
                health_status['database_error'] = str(e)
                health_status['status'] = 'degraded'
        
        # Déterminer le code de statut HTTP
        status_code = 200
        if health_status['status'] == 'degraded':
            status_code = 503
        elif not supabase or not discord_client_id:
            health_status['status'] = 'unhealthy'
            status_code = 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/login')
def login():
    if 'user' in session and is_user_admin():
        return redirect(url_for('index'))
    
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?client_id={discord_client_id}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return render_template('login.html', discord_url=discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        print("ERREUR: Pas de code OAuth fourni")
        return redirect(url_for('login'))
    
    data = {
        'client_id': discord_client_id,
        'client_secret': discord_client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    import requests
    response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
    
    print(f"� Réponse OAuth: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get('https://discord.com/api/users/@me', headers=headers)
        guilds_response = requests.get('https://discord.com/api/users/@me/guilds', headers=headers)
        
        print(f"� User response: {user_response.status_code}, Guilds response: {guilds_response.status_code}")
        
        if user_response.status_code == 200 and guilds_response.status_code == 200:
            user_data = user_response.json()
            guilds_data = guilds_response.json()
            
            print(f"� Utilisateur: {user_data.get('username')}")
            print(f"� Nombre de guildes: {len(guilds_data)}")
            
            for guild in guilds_data:
                if guild['id'] == str(os.getenv('DISCORD_GUILD_ID')):
                    print(f"✅ Guilde trouvée: {guild.get('name')}")
                    member_response = requests.get(f'https://discord.com/api/guilds/{guild["id"]}/members/{user_data["id"]}', 
                                                 headers={'Authorization': f'Bot {DISCORD_BOT_TOKEN}'})
                    print(f"� Status récupération membre: {member_response.status_code}")
                    
                    if member_response.status_code == 200:
                        member_data = member_response.json()
                        guild['roles'] = member_data.get('roles', [])
                        print(f"✅ Rôles récupérés: {len(guild['roles'])} rôles")
                    else:
                        print(f"ERREUR récupération rôles: {member_response.status_code}")
                        print(f"� Réponse: {member_response.text[:200]}")
                        guild['roles'] = []
            
            user_data['guilds'] = guilds_data
            
            print(f"� Utilisateur connecté: {user_data['username']}")
            print(f"� Guildes: {[g['name'] for g in guilds_data]}")
            print(f"� Rôles admin configurés: {ADMIN_ROLE_IDS}")
            
            is_admin = admin_manager.is_admin(user_data)
            print(f"� Est admin: {is_admin}")
            
            if is_admin:
                session['user'] = {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'avatar': user_data.get('avatar'),
                    'discriminator': user_data.get('discriminator'),
                    'admin': True
                }
                print("✅ Redirection vers le dashboard")
                return redirect(url_for('index'))
            else:
                print("ERREUR: Accès refusé - pas admin")
                return render_template('unauthorized.html')
        else:
            print(f"ERREUR récupération données: User {user_response.status_code}, Guilds {guilds_response.status_code}")
    
    print("ERREUR OAuth")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# API Routes - Countries
@app.route('/api/countries')
@rate_limit
@require_admin
@require_database
@handle_api_errors
def api_countries():
    """Récupérer tous les pays"""
    print("INFO: Récupération de tous les pays...")
    result = supabase.table('countries').select('*').execute()
    
    if result.data is None:
        print("WARNING: Aucun pays trouvé dans la base de données")
        return jsonify([])
    
    print(f"SUCCESS: {len(result.data)} pays récupérés")
    return jsonify(result.data)

@app.route('/api/countries', methods=['POST'])
@rate_limit
@require_admin
@require_database
@handle_api_errors
def api_create_country():
    """Créer un nouveau pays"""
    data = request.json
    if not data:
        print("ERREUR: Aucune donnée fournie pour la création de pays")
        return jsonify({'error': 'No data provided'}), 400
    
    print(f"INFO: Création d'un nouveau pays: {data.get('name', 'N/A')}")
    result = supabase.table('countries').insert(data).execute()
    
    if result.data:
        country = result.data[0]
        username, user_id = get_user_info()
        log_country_created(country, username, user_id)
        print(f"SUCCESS: Pays créé avec ID {country.get('id', 'N/A')}")
        return jsonify({'success': True, 'data': result.data})
    
    print("ERREUR: Échec de la création du pays - pas de données retournées")
    return jsonify({'error': 'Failed to create country'}), 500

@app.route('/api/countries/<country_id>', methods=['GET', 'PUT', 'DELETE'])
def api_country(country_id):
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        if request.method == 'GET':
            result = supabase.table('countries').select('*').eq('id', country_id).execute()
            if result.data:
                return jsonify(result.data[0])
            return jsonify({'error': 'Country not found'}), 404
        
        elif request.method == 'PUT':
            old_country = supabase.table('countries').select('*').eq('id', country_id).execute()
            
            data = request.json
            result = supabase.table('countries').update(data).eq('id', country_id).execute()
            
            if result.data:
                country = result.data[0]
                changes = []
                for key, value in data.items():
                    if key in old_country.data[0]:
                        changes.append(f"{key}: {old_country.data[0][key]} → {value}")
                
                username, user_id = get_user_info()
                log_country_modified(country, changes, username, user_id)
                
                return jsonify({'success': True, 'data': result.data})
            
            return jsonify({'error': 'Failed to update country'}), 500
        
        elif request.method == 'DELETE':
            old_country = supabase.table('countries').select('*').eq('id', country_id).execute()
            
            supabase.table('players').update({
                'country_id': None,
                'role': 'recruit'
            }).eq('country_id', country_id).execute()
            
            result = supabase.table('countries').delete().eq('id', country_id).execute()
            
            if old_country.data:
                username, user_id = get_user_info()
            log_country_deleted(old_country.data[0].get('name', 'Inconnu'), country_id, username, user_id)
            
            return jsonify({'success': True})
    
    except Exception as e:
        print(f"❌ Erreur API pays: {e}")
        return jsonify({'error': str(e)}), 500

# API Routes - Players
@app.route('/api/players')
def api_players():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        result = supabase.table('players').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<player_id>', methods=['PUT', 'DELETE'])
def api_player(player_id):
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        if request.method == 'PUT':
            old_player = supabase.table('players').select('*').eq('id', player_id).execute()
            
            data = request.json
            result = supabase.table('players').update(data).eq('id', player_id).execute()
            
            if result.data:
                player = result.data[0]
                changes = []
                for key, value in data.items():
                    if old_player.data and key in old_player.data[0]:
                        changes.append(f"{key}: {old_player.data[0][key]} → {value}")
                
                username, user_id = get_user_info()
                log_player_modified(player, changes, username, user_id)
                
                return jsonify({'success': True, 'data': result.data})
            
            return jsonify({'error': 'Failed to update player'}), 500
        
        elif request.method == 'DELETE':
            old_player = supabase.table('players').select('*').eq('id', player_id).execute()
            
            result = supabase.table('players').delete().eq('id', player_id).execute()
            
            if old_player.data:
                username, user_id = get_user_info()
            log_player_deleted(old_player.data[0].get('username', 'Inconnu'), player_id, username, user_id)
            
            return jsonify({'success': True})
    
    except Exception as e:
        print(f"❌ Erreur API joueur: {e}")
        return jsonify({'error': str(e)}), 500

# API Routes - Wars
@app.route('/api/wars')
def api_wars():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        result = supabase.table('wars').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wars/<war_id>', methods=['PUT', 'DELETE'])
def api_war(war_id):
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        if request.method == 'PUT':
            data = request.json
            result = supabase.table('wars').update(data).eq('id', war_id).execute()
            
            if result.data:
                username, user_id = get_user_info()
                log_war_ended(war_id, username, user_id)
                return jsonify({'success': True, 'data': result.data})
            
            return jsonify({'error': 'Failed to update war'}), 500
        
        elif request.method == 'DELETE':
            result = supabase.table('wars').delete().eq('id', war_id).execute()
            
            username, user_id = get_user_info()
            log_war_deleted(war_id, username, user_id)
            
            return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wars/end-all', methods=['POST'])
def api_end_all_wars():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        result = supabase.table('wars').update({
            'ended_at': datetime.now().isoformat()
        }).is_('ended_at', 'null').execute()
        
        username, user_id = get_user_info()
        log_tools_action(r"� Fin de toutes les guerres", r"{len(result.data) if result.data else 0} guerres terminées", username=username, user_id=user_id)
        
        return jsonify({'success': True, 'count': len(result.data) if result.data else 0})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes - Events
@app.route('/api/events')
def api_events():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        result = supabase.table('events').select('*').order('created_at', desc=True).limit(50).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/trigger', methods=['POST'])
def api_trigger_event():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        data = request.json
        
        # Créer un événement aléatoire si aucune donnée n'est fournie
        if not data:
            import random
            countries = supabase.table('countries').select('id').execute()
            if countries.data:
                random_country = random.choice(countries.data)
                
                event_types = [
                    {'type': 'disaster', 'description': 'Catastrophe naturelle', 'impact': {'stability': -10, 'economy': -5}},
                    {'type': 'boom', 'description': 'Boom économique', 'impact': {'economy': 10, 'stability': 5}},
                    {'type': 'rebellion', 'description': 'Rébellion populaire', 'impact': {'stability': -15, 'army_strength': -5}},
                    {'type': 'discovery', 'description': 'Découverte de ressources', 'impact': {'economy': 15}},
                ]
                
                event = random.choice(event_types)
                data = {
                    'type': event['type'],
                    'description': event['description'],
                    'target_country': random_country['id'],
                    'impact': event['impact'],
                    'created_at': datetime.now().isoformat()
                }
            else:
                return jsonify({'error': 'Aucun pays disponible pour générer un événement'}), 400
        
        # Validation minimale
        if not isinstance(data, dict) or 'type' not in data:
            print(f"ERREUR Validation échouée: data={data}")
            return jsonify({'error': 'Invalid payload'}), 400

        # Insérer
        print(f"📝 Insertion événement: {data}")
        result = supabase.table('events').insert(data).execute()
        
        if result.data:
            username, user_id = get_user_info()
            log_event_triggered(data, username, user_id)
            return jsonify({'success': True, 'data': result.data})
        
        print(f"ERREUR Insertion échouée: {result}")
        return jsonify({'error': 'Failed to trigger event'}), 500
    
    except Exception as e:
        # Log verbeux côté serveur
        print(f"Erreur /api/events/trigger: {e}")
        return jsonify({'error': 'Failed to trigger event', 'details': str(e)}), 500

# API Routes - Transactions (audit économique)
@app.route('/api/transactions')
def api_transactions():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        ttype = request.args.get('type')
        country_id = request.args.get('country_id')
        player_id = request.args.get('player_id')
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        limit = int(request.args.get('limit', '200'))

        q = supabase.table('transactions').select('*').order('created_at', desc=True).limit(limit)
        if ttype:
            q = q.eq('type', ttype)
        if country_id:
            q = q.eq('country_id', country_id)
        if player_id:
            q = q.eq('player_id', player_id)
        if date_from:
            q = q.gte('created_at', date_from)
        if date_to:
            q = q.lte('created_at', date_to)

        res = q.execute()
        return jsonify({'success': True, 'data': res.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes - Statistics
@app.route('/api/statistics')
def api_statistics():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        countries_count = supabase.table('countries').select('id', count='exact').execute()
        players_count = supabase.table('players').select('id', count='exact').execute()
        active_wars = supabase.table('wars').select('id', count='exact').is_('ended_at', 'null').execute()
        
        top_economy = supabase.table('countries').select('name, economy').order('economy', desc=True).limit(5).execute()
        top_military = supabase.table('countries').select('name, army_strength').order('army_strength', desc=True).limit(5).execute()
        
        return jsonify({
            'countries_count': countries_count.count,
            'players_count': players_count.count,
            'active_wars': active_wars.count,
            'top_economy': top_economy.data,
            'top_military': top_military.data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes - Tools
@app.route('/api/tools/reset-resources', methods=['POST'])
def api_reset_resources():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        default_resources = {
            'money': 5000,
            'food': 200,
            'metal': 50,
            'oil': 80,
            'energy': 100,
            'materials': 30
        }
        
        result = supabase.table('countries').update({
            'resources': default_resources
        }).neq('id', 0).execute()
        
        username, user_id = get_user_info()
        log_tools_action(r"� Réinitialisation des ressources", r"{len(result.data) if result.data else 0} pays réinitialisés", username=username, user_id=user_id)
        
        return jsonify({'success': True, 'count': len(result.data) if result.data else 0})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/reset-stats', methods=['POST'])
def api_reset_stats():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        result = supabase.table('countries').update({
            'economy': 50,
            'army_strength': 20,
            'stability': 80
        }).neq('id', 0).execute()
        
        username, user_id = get_user_info()
        log_tools_action(r"� Réinitialisation des statistiques", r"{len(result.data) if result.data else 0} pays réinitialisés", username=username, user_id=user_id)
        
        return jsonify({'success': True, 'count': len(result.data) if result.data else 0})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/backup', methods=['POST'])
def api_backup():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        # Récupérer toutes les données
        countries = supabase.table('countries').select('*').execute()
        players = supabase.table('players').select('*').execute()
        wars = supabase.table('wars').select('*').execute()
        events = supabase.table('events').select('*').execute()
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'countries': countries.data,
            'players': players.data,
            'wars': wars.data,
            'events': events.data
        }
        
        # Sauvegarder dans un fichier
        backup_file = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        username, user_id = get_user_info()
        log_tools_action(r"� Sauvegarde créée", r"Fichier: {backup_file}", username=username, user_id=user_id)
        
        return jsonify({'success': True, 'file': backup_file})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/give', methods=['POST'])
def api_give():
    """Donner une ressource/argent à un joueur/pays ou à tous (admin requis).
    Body JSON attendu:
    {
      "target_type": "player" | "country" | "all_players" | "all_countries",
      "target_id": "<id optionnel>",
      "resource": "money|food|metal|oil|energy|materials|balance",
      "amount": <int>
    }
    """
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        data = request.json or {}
        target_type = data.get('target_type')
        target_id = data.get('target_id')
        resource = data.get('resource')
        amount = int(data.get('amount', 0))

        if amount == 0 or not resource or not target_type:
            return jsonify({'error': 'Paramètres invalides'}), 400

        # Donner à un joueur: met à jour le solde personnel (balance)
        if target_type == 'player':
            if resource in ['balance', 'money']:
                result = supabase.table('players').update({
                    'balance': supabase.rpc('increment_field', {
                        'table_name': 'players',
                        'row_id': target_id,
                        'field_name': 'balance',
                        'delta': amount
                    })
                }).eq('id', target_id).execute()
                # fallback sans RPC
                if not result.data:
                    player = supabase.table('players').select('balance').eq('id', target_id).execute()
                    if player.data:
                        new_balance = (player.data[0].get('balance', 0) or 0) + amount
                        supabase.table('players').update({'balance': new_balance}).eq('id', target_id).execute()
            else:
                return jsonify({'error': 'Ressource invalide pour un joueur'}), 400

        # Donner à un pays: met à jour le champ resources JSON
        elif target_type == 'country':
            country = supabase.table('countries').select('resources').eq('id', target_id).execute()
            if not country.data:
                return jsonify({'error': 'Pays introuvable'}), 404
            resources = country.data[0].get('resources') or {}
            resources[resource] = (resources.get(resource, 0) or 0) + amount
            supabase.table('countries').update({'resources': resources}).eq('id', target_id).execute()

        elif target_type == 'all_players':
            if resource not in ['balance', 'money']:
                return jsonify({'error': 'Ressource invalide pour all_players'}), 400
            players = supabase.table('players').select('id,balance').execute()
            for p in (players.data or []):
                new_balance = (p.get('balance', 0) or 0) + amount
                supabase.table('players').update({'balance': new_balance}).eq('id', p['id']).execute()

        elif target_type == 'all_countries':
            countries = supabase.table('countries').select('id,resources').execute()
            for c in (countries.data or []):
                res = c.get('resources') or {}
                res[resource] = (res.get(resource, 0) or 0) + amount
                supabase.table('countries').update({'resources': res}).eq('id', c['id']).execute()
        else:
            return jsonify({'error': 'target_type invalide'}), 400

        username, user_id = get_user_info()
        log_tools_action(r"🎁 Don", r"Cible: {target_type} {target_id or ''} | Ressource: {resource} | Montant: {amount}", username=username, user_id=user_id)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/promote-citizens', methods=['POST'])
def api_promote_citizens():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        result = supabase.table('players').update({
            'role': 'citizen'
        }).eq('role', 'recruit').execute()
        
        username, user_id = get_user_info()
        log_tools_action(r"⬆️ Promotion de tous les recrues", r"{len(result.data) if result.data else 0} joueurs promus", username=username, user_id=user_id)
        
        return jsonify({'success': True, 'count': len(result.data) if result.data else 0})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/give-money', methods=['POST'])
def api_give_money():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        amount = request.json.get('amount', 1000)
        
        # Récupérer tous les joueurs
        players = supabase.table('players').select('*').execute()
        
        # Mettre à jour chaque joueur
        for player in players.data:
            new_balance = (player.get('balance', 0) or 0) + amount
            supabase.table('players').update({
                'balance': new_balance
            }).eq('id', player['id']).execute()
        
        username, user_id = get_user_info()
        log_tools_action(r"� Distribution d'argent", r"{amount}� donnés à {len(players.data)} joueurs", username=username, user_id=user_id)
        
        return jsonify({'success': True, 'count': len(players.data)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/reset-players', methods=['POST'])
def api_reset_players():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        result = supabase.table('players').update({
            'balance': 0,
            'role': 'recruit',
            'country_id': None
        }).neq('id', '0').execute()
        
        username, user_id = get_user_info()
        log_tools_action(r"� Réinitialisation des joueurs", r"{len(result.data) if result.data else 0} joueurs réinitialisés", username=username, user_id=user_id)
        
        return jsonify({'success': True, 'count': len(result.data) if result.data else 0})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/export')
def api_export_players():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if supabase is None:
            return jsonify({'error': 'Database not configured'}), 500
        players = supabase.table('players').select('*').execute()
        
        username, user_id = get_user_info()
        log_tools_action(r"� Export des joueurs", r"{len(players.data)} joueurs exportés", username=username, user_id=user_id)
        
        return jsonify({'success': True, 'data': players.data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket events (AMÉLIORÉS)
@socketio.on('connect')
def handle_connect():
    """Gestion de la connexion Socket.IO avec validation"""
    try:
        if not is_user_admin():
            emit('error', {'message': 'Unauthorized'})
            return False
        
        emit('connected', {'message': 'Connected to admin dashboard'})
        print(f"✅ Admin connecté via Socket.IO")
        return True
    except Exception as e:
        print(f"❌ Erreur connexion Socket.IO: {e}")
        emit('error', {'message': 'Connection error'})
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Gestion de la déconnexion Socket.IO"""
    print('📤 Admin déconnecté du Socket.IO')

@socketio.on('request_update')
def handle_update_request():
    """Mise à jour des données avec gestion d'erreurs améliorée"""
    if not is_user_admin():
        emit('error', {'message': 'Unauthorized'})
        return
    
    try:
        if supabase is None:
            emit('error', {'message': 'Database not configured'})
            return
        
        # Récupération des données avec gestion d'erreurs individuelle
        countries_data = []
        players_data = []
        wars_data = []
        events_data = []
        
        try:
            countries = supabase.table('countries').select('*').execute()
            countries_data = countries.data or []
        except Exception as e:
            print(f"❌ Erreur récupération pays: {e}")
            countries_data = []
        
        try:
            players = supabase.table('players').select('*').execute()
            players_data = players.data or []
        except Exception as e:
            print(f"❌ Erreur récupération joueurs: {e}")
            players_data = []
        
        try:
            wars = supabase.table('wars').select('*').execute()
            wars_data = wars.data or []
        except Exception as e:
            print(f"❌ Erreur récupération guerres: {e}")
            wars_data = []
        
        try:
            events = supabase.table('events').select('*').order('created_at', desc=True).limit(50).execute()
            events_data = events.data or []
        except Exception as e:
            print(f"❌ Erreur récupération événements: {e}")
            events_data = []
        
        emit('data_update', {
            'countries': countries_data,
            'players': players_data,
            'wars': wars_data,
            'events': events_data,
            'timestamp': datetime.now().isoformat()
        })
        print(f"✅ Données mises à jour via Socket.IO")
        
    except Exception as e:
        print(f"❌ Erreur générale Socket.IO: {e}")
        emit('error', {'message': f'Update error: {str(e)}'})

# ==================== TOOLS ENDPOINTS (CORRIGÉS) ====================

# Démarrage du serveur
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
