from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import os
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
BASE_URL = os.getenv('RENDER_EXTERNAL_URL') or os.getenv('WEB_PANEL_URL') or os.getenv('HOST_IP', 'http://localhost:5000')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', BASE_URL + '/callback')
ADMIN_ROLE_IDS = [int(x) for x in os.getenv('ADMIN_ROLE_IDS', '').split(',') if x.strip()]

LOG_CHANNEL_ID = 1432369899635871894

# Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        print(f"� Recherche dans la guilde: {guild_id}")
        print(f"� Rôles admin configurés: {ADMIN_ROLE_IDS}")
        
        for guild in user_data['guilds']:
            print(f"� Guilde trouvée: {guild['id']} - {guild.get('name', 'Inconnu')}")
            if guild['id'] == guild_id:
                user_roles = guild.get('roles', [])
                print(f"� Rôles de l'utilisateur: {user_roles}")
                
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
                            print(f"❌ Erreur API: {member_response.status_code}")
                            if guild.get('permissions'):
                                permissions = int(guild.get('permissions', '0'))
                                if permissions & 0x8:
                                    print("✅ Utilisateur a les permissions admin dans la guilde")
                                    return True
                    except Exception as e:
                        print(f"❌ Erreur lors de la récupération des rôles: {e}")
                
                user_role_ids = []
                for role_id in user_roles:
                    try:
                        user_role_ids.append(int(role_id))
                    except (ValueError, TypeError):
                        pass
                
                print(f"� Rôles convertis: {user_role_ids}")
                
                has_admin_role = any(role_id in ADMIN_ROLE_IDS for role_id in user_role_ids)
                print(f"� A un rôle admin: {has_admin_role}")
                
                if has_admin_role:
                    return True
        
        print("❌ Aucun rôle admin trouvé")
        return False

admin_manager = WebAdminManager()

def is_user_admin():
    """Vérifier si l'utilisateur dans la session est admin"""
    if 'user' not in session:
        return False
    return session['user'].get('admin', False)

def send_discord_log(action, details):
    """Envoyer un log sur Discord"""
    try:
        import requests
        
        username = session.get('user', {}).get('username', 'Inconnu')
        user_id = session.get('user', {}).get('id', 'Inconnu')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"**� {action}**\n� **Utilisateur:** {username} ({user_id})\n� **Date:** {timestamp}\n� **Détails:** {details}"
        
        payload = {
            'content': message,
            'username': 'Web Admin Panel'
        }
        
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if webhook_url:
            requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"❌ Erreur envoi log Discord: {e}")

# Routes principales
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if not is_user_admin():
        return render_template('unauthorized.html')
    
    return render_template('dashboard.html')

@app.route('/login')
def login():
    if 'user' in session and is_user_admin():
        return redirect(url_for('index'))
    
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return render_template('login.html', discord_url=discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        print("❌ Pas de code OAuth fourni")
        return redirect(url_for('login'))
    
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
                        print(f"❌ Erreur récupération rôles: {member_response.status_code}")
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
                print("❌ Accès refusé - pas admin")
                return render_template('unauthorized.html')
        else:
            print(f"❌ Erreur récupération données: User {user_response.status_code}, Guilds {guilds_response.status_code}")
    
    print("❌ Erreur OAuth")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# API Routes - Countries
@app.route('/api/countries')
def api_countries():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        result = supabase.table('countries').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/countries', methods=['POST'])
def api_create_country():
    """Créer un nouveau pays"""
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        result = supabase.table('countries').insert(data).execute()
        
        if result.data:
            country = result.data[0]
            send_discord_log(
                "� Création de pays",
                f"Pays: **{country.get('name', 'Inconnu')}** (ID: {country.get('id')})"
            )
            return jsonify({'success': True, 'data': result.data})
        
        return jsonify({'error': 'Failed to create country'}), 500
    
    except Exception as e:
        print(f"❌ Erreur création pays: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/countries/<country_id>', methods=['GET', 'PUT', 'DELETE'])
def api_country(country_id):
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
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
                
                send_discord_log(
                    "✏️ Modification de pays",
                    f"Pays: **{country.get('name')}** (ID: {country_id})\nChangements: {', '.join(changes)}"
                )
                
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
                send_discord_log(
                    "�️ Suppression de pays",
                    f"Pays: **{old_country.data[0].get('name', 'Inconnu')}** (ID: {country_id})"
                )
            
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
        result = supabase.table('players').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<player_id>', methods=['PUT', 'DELETE'])
def api_player(player_id):
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
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
                
                send_discord_log(
                    "� Modification de joueur",
                    f"Joueur: **{player.get('username', 'Inconnu')}** (ID: {player_id})\nChangements: {', '.join(changes)}"
                )
                
                return jsonify({'success': True, 'data': result.data})
            
            return jsonify({'error': 'Failed to update player'}), 500
        
        elif request.method == 'DELETE':
            old_player = supabase.table('players').select('*').eq('id', player_id).execute()
            
            result = supabase.table('players').delete().eq('id', player_id).execute()
            
            if old_player.data:
                send_discord_log(
                    "�️ Suppression de joueur",
                    f"Joueur: **{old_player.data[0].get('username', 'Inconnu')}** (ID: {player_id})"
                )
            
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
        result = supabase.table('wars').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wars/<war_id>', methods=['PUT', 'DELETE'])
def api_war(war_id):
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if request.method == 'PUT':
            data = request.json
            result = supabase.table('wars').update(data).eq('id', war_id).execute()
            
            if result.data:
                send_discord_log(
                    "⚔️ Fin de guerre",
                    f"Guerre ID: {war_id} terminée"
                )
                return jsonify({'success': True, 'data': result.data})
            
            return jsonify({'error': 'Failed to update war'}), 500
        
        elif request.method == 'DELETE':
            result = supabase.table('wars').delete().eq('id', war_id).execute()
            
            send_discord_log(
                "�️ Suppression de guerre",
                f"Guerre ID: {war_id} supprimée"
            )
            
            return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wars/end-all', methods=['POST'])
def api_end_all_wars():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        result = supabase.table('wars').update({
            'ended_at': datetime.now().isoformat()
        }).is_('ended_at', 'null').execute()
        
        send_discord_log(
            "� Fin de toutes les guerres",
            f"{len(result.data) if result.data else 0} guerres terminées"
        )
        
        return jsonify({'success': True, 'count': len(result.data) if result.data else 0})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes - Events
@app.route('/api/events')
def api_events():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        result = supabase.table('events').select('*').order('created_at', desc=True).limit(50).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/trigger', methods=['POST'])
def api_trigger_event():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
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
        
        result = supabase.table('events').insert(data).execute()
        
        if result.data:
            send_discord_log(
                "⚡ Événement déclenché",
                f"Type: **{data['type']}** - {data['description']}"
            )
            return jsonify({'success': True, 'data': result.data})
        
        return jsonify({'error': 'Failed to trigger event'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes - Statistics
@app.route('/api/statistics')
def api_statistics():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
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
        
        send_discord_log(
            "� Réinitialisation des ressources",
            f"{len(result.data) if result.data else 0} pays réinitialisés"
        )
        
        return jsonify({'success': True, 'count': len(result.data) if result.data else 0})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/reset-stats', methods=['POST'])
def api_reset_stats():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        result = supabase.table('countries').update({
            'economy': 50,
            'army_strength': 20,
            'stability': 80
        }).neq('id', 0).execute()
        
        send_discord_log(
            "� Réinitialisation des statistiques",
            f"{len(result.data) if result.data else 0} pays réinitialisés"
        )
        
        return jsonify({'success': True, 'count': len(result.data) if result.data else 0})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/backup', methods=['POST'])
def api_backup():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
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
        
        send_discord_log(
            "� Sauvegarde créée",
            f"Fichier: {backup_file}"
        )
        
        return jsonify({'success': True, 'file': backup_file})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/promote-citizens', methods=['POST'])
def api_promote_citizens():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        result = supabase.table('players').update({
            'role': 'citizen'
        }).eq('role', 'recruit').execute()
        
        send_discord_log(
            "⬆️ Promotion de tous les recrues",
            f"{len(result.data) if result.data else 0} joueurs promus"
        )
        
        return jsonify({'success': True, 'count': len(result.data) if result.data else 0})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/give-money', methods=['POST'])
def api_give_money():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        amount = request.json.get('amount', 1000)
        
        # Récupérer tous les joueurs
        players = supabase.table('players').select('*').execute()
        
        # Mettre à jour chaque joueur
        for player in players.data:
            new_balance = (player.get('balance', 0) or 0) + amount
            supabase.table('players').update({
                'balance': new_balance
            }).eq('id', player['id']).execute()
        
        send_discord_log(
            "� Distribution d'argent",
            f"{amount}� donnés à {len(players.data)} joueurs"
        )
        
        return jsonify({'success': True, 'count': len(players.data)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/reset-players', methods=['POST'])
def api_reset_players():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        result = supabase.table('players').update({
            'balance': 0,
            'role': 'recruit',
            'country_id': None
        }).neq('id', '0').execute()
        
        send_discord_log(
            "� Réinitialisation des joueurs",
            f"{len(result.data) if result.data else 0} joueurs réinitialisés"
        )
        
        return jsonify({'success': True, 'count': len(result.data) if result.data else 0})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/export')
def api_export_players():
    if not is_user_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        players = supabase.table('players').select('*').execute()
        
        send_discord_log(
            "� Export des joueurs",
            f"{len(players.data)} joueurs exportés"
        )
        
        return jsonify({'success': True, 'data': players.data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    if not is_user_admin():
        emit('error', {'message': 'Unauthorized'})
        return False
    
    emit('connected', {'message': 'Connected to admin dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Admin disconnected')

@socketio.on('request_update')
def handle_update_request():
    if not is_user_admin():
        emit('error', {'message': 'Unauthorized'})
        return
    
    try:
        countries = supabase.table('countries').select('*').execute()
        players = supabase.table('players').select('*').execute()
        wars = supabase.table('wars').select('*').execute()
        events = supabase.table('events').select('*').order('created_at', desc=True).limit(50).execute()
        
        emit('data_update', {
            'countries': countries.data,
            'players': players.data,
            'wars': wars.data,
            'events': events.data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('error', {'message': str(e)})

# Démarrage du serveur
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
