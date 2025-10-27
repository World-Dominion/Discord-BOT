from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import os
# imports supprimés - non utilisés
from supabase import create_client, Client
import json
from datetime import datetime
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('WEB_SECRET_KEY', secrets.token_hex(32))
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
# URL du service - Render.com fournit RENDER_EXTERNAL_URL automatiquement
BASE_URL = os.getenv('RENDER_EXTERNAL_URL') or os.getenv('WEB_PANEL_URL') or os.getenv('HOST_IP', 'http://localhost:5000')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', BASE_URL + '/callback')
ADMIN_ROLE_IDS = [int(x) for x in os.getenv('ADMIN_ROLE_IDS', '').split(',') if x.strip()]

# Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Discord Bot Token (pour les API calls)
DISCORD_BOT_TOKEN = os.getenv('DISCORD_TOKEN')

class WebAdminManager:
    def __init__(self):
        self.bot = None
    
    def is_admin(self, user_data):
        """Vérifier si l'utilisateur est admin"""
        if not user_data or 'guilds' not in user_data:
            print("❌ Pas de données utilisateur ou guildes")
            return False
        
        guild_id = str(os.getenv('DISCORD_GUILD_ID'))
        print(f"🔍 Recherche dans la guilde: {guild_id}")
        print(f"🔍 Rôles admin configurés: {ADMIN_ROLE_IDS}")
        
        for guild in user_data['guilds']:
            print(f"🔍 Guilde trouvée: {guild['id']} - {guild.get('name', 'Inconnu')}")
            if guild['id'] == guild_id:
                user_roles = guild.get('roles', [])
                print(f"🔍 Rôles de l'utilisateur: {user_roles}")
                
                # Convertir les rôles en entiers pour la comparaison
                user_role_ids = [int(role_id) for role_id in user_roles if role_id.isdigit()]
                print(f"🔍 Rôles convertis: {user_role_ids}")
                
                # Vérifier si l'utilisateur a un des rôles admin
                has_admin_role = any(role_id in ADMIN_ROLE_IDS for role_id in user_role_ids)
                print(f"🔍 A un rôle admin: {has_admin_role}")
                
                if has_admin_role:
                    return True
        
        print("❌ Aucun rôle admin trouvé")
        return False

admin_manager = WebAdminManager()

# Routes principales
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if not admin_manager.is_admin(session['user']):
        return render_template('unauthorized.html')
    
    return render_template('dashboard.html')

@app.route('/login')
def login():
    if 'user' in session and admin_manager.is_admin(session['user']):
        return redirect(url_for('index'))
    
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return render_template('login.html', discord_url=discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('login'))
    
    # Échanger le code contre un token
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    import requests
    response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        
        # Récupérer les informations utilisateur
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get('https://discord.com/api/users/@me', headers=headers)
        guilds_response = requests.get('https://discord.com/api/users/@me/guilds', headers=headers)
        
        if user_response.status_code == 200 and guilds_response.status_code == 200:
            user_data = user_response.json()
            guilds_data = guilds_response.json()
            
            # Ajouter les rôles pour chaque serveur
            for guild in guilds_data:
                if guild['id'] == str(os.getenv('DISCORD_GUILD_ID')):
                    # Récupérer les rôles de l'utilisateur dans ce serveur
                    member_response = requests.get(f'https://discord.com/api/guilds/{guild["id"]}/members/{user_data["id"]}', 
                                                 headers={'Authorization': f'Bot {DISCORD_BOT_TOKEN}'})
                    if member_response.status_code == 200:
                        member_data = member_response.json()
                        guild['roles'] = member_data.get('roles', [])
                    else:
                        # Si on ne peut pas récupérer les rôles, essayer une approche alternative
                        print(f"Erreur récupération rôles: {member_response.status_code}")
                        guild['roles'] = []
            
            user_data['guilds'] = guilds_data
            session['user'] = user_data
            
            # Debug: afficher les informations de l'utilisateur
            print(f"Utilisateur connecté: {user_data['username']}")
            print(f"Guildes: {[g['name'] for g in guilds_data]}")
            print(f"Rôles admin configurés: {ADMIN_ROLE_IDS}")
            
            # Vérifier les permissions
            is_admin = admin_manager.is_admin(user_data)
            print(f"Est admin: {is_admin}")
            
            if is_admin:
                return redirect(url_for('index'))
            else:
                return render_template('unauthorized.html')
    
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# API Routes
@app.route('/api/countries')
def api_countries():
    if not admin_manager.is_admin(session.get('user')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        result = supabase.table('countries').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/countries/<country_id>', methods=['GET', 'PUT', 'DELETE'])
def api_country(country_id):
    if not admin_manager.is_admin(session.get('user')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if request.method == 'GET':
            result = supabase.table('countries').select('*').eq('id', country_id).execute()
            if result.data:
                return jsonify(result.data[0])
            return jsonify({'error': 'Country not found'}), 404
        
        elif request.method == 'PUT':
            data = request.json
            result = supabase.table('countries').update(data).eq('id', country_id).execute()
            return jsonify({'success': True, 'data': result.data})
        
        elif request.method == 'DELETE':
            # Expulser tous les joueurs
            supabase.table('players').update({
                'country_id': None,
                'role': 'recruit'
            }).eq('country_id', country_id).execute()
            
            # Supprimer le pays
            result = supabase.table('countries').delete().eq('id', country_id).execute()
            return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players')
def api_players():
    if not admin_manager.is_admin(session.get('user')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        result = supabase.table('players').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<player_id>', methods=['PUT', 'DELETE'])
def api_player(player_id):
    if not admin_manager.is_admin(session.get('user')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if request.method == 'PUT':
            data = request.json
            result = supabase.table('players').update(data).eq('id', player_id).execute()
            return jsonify({'success': True, 'data': result.data})
        
        elif request.method == 'DELETE':
            result = supabase.table('players').delete().eq('id', player_id).execute()
            return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wars')
def api_wars():
    if not admin_manager.is_admin(session.get('user')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        result = supabase.table('wars').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events')
def api_events():
    if not admin_manager.is_admin(session.get('user')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        result = supabase.table('events').select('*').order('created_at', desc=True).limit(50).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def api_statistics():
    if not admin_manager.is_admin(session.get('user')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Statistiques générales
        countries_count = supabase.table('countries').select('id', count='exact').execute()
        players_count = supabase.table('players').select('id', count='exact').execute()
        active_wars = supabase.table('wars').select('id', count='exact').is_('ended_at', 'null').execute()
        
        # Top pays par économie
        top_economy = supabase.table('countries').select('name, economy').order('economy', desc=True).limit(5).execute()
        
        # Top pays par force militaire
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

# WebSocket events
@socketio.on('connect')
def handle_connect():
    if not admin_manager.is_admin(session.get('user')):
        emit('error', {'message': 'Unauthorized'})
        return False
    
    emit('connected', {'message': 'Connected to admin dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Admin disconnected')

@socketio.on('request_update')
def handle_update_request():
    if not admin_manager.is_admin(session.get('user')):
        emit('error', {'message': 'Unauthorized'})
        return
    
    # Envoyer les données mises à jour
    try:
        countries = supabase.table('countries').select('*').execute()
        players = supabase.table('players').select('*').execute()
        wars = supabase.table('wars').select('*').execute()
        
        emit('data_update', {
            'countries': countries.data,
            'players': players.data,
            'wars': wars.data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    # Démarrer le serveur web directement
    # Le bot Discord sera initialisé de manière asynchrone
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
