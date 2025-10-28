<<<<<<< HEAD
// Variables globales (unifiées)
let rolesChart, economyChart, statisticsChart;
let currentData = { countries: [], players: [], wars: [], events: [] };
=======
// Variables globales
let rolesChart, economyChart, statisticsChart;
let currentData = {
    countries: [],
    players: [],
    wars: [],
    events: []
};

// Fonction d'initialisation
document.addEventListener('DOMContentLoaded', function() {
    showLoading(false);
    requestUpdate();
});
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6

// Mise à jour du dashboard
function updateDashboard() {
    if (!currentData.countries || !currentData.players) return;
    
    // Update statistics
    document.getElementById('countries-count').textContent = currentData.countries.length;
    document.getElementById('players-count').textContent = currentData.players.length;
    document.getElementById('wars-count').textContent = currentData.wars ? currentData.wars.filter(w => !w.ended_at).length : 0;
    
    const totalEconomy = currentData.countries.reduce((sum, country) => sum + (country.economy || 0), 0);
    document.getElementById('total-economy').textContent = formatNumber(totalEconomy);
    
    // Update charts
    updateRolesChart();
    updateEconomyChart();
    updateTables();
    updateRecentActivity();
    updateAlerts();
}

function updateRolesChart() {
    if (!currentData.players) return;
    
    const roleCounts = {};
    currentData.players.forEach(player => {
        const role = player.role || 'recruit';
        roleCounts[role] = (roleCounts[role] || 0) + 1;
    });
    
    const ctx = document.getElementById('rolesChart').getContext('2d');
    if (rolesChart) rolesChart.destroy();
    
    rolesChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(roleCounts),
            datasets: [{
                data: Object.values(roleCounts),
                backgroundColor: [
                    '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                }
            }
        }
    });
}

function updateEconomyChart() {
    if (!currentData.countries) return;
    
    const topCountries = currentData.countries
        .sort((a, b) => (b.economy || 0) - (a.economy || 0))
        .slice(0, 5);
    
    const ctx = document.getElementById('economyChart').getContext('2d');
    if (economyChart) economyChart.destroy();
    
    economyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topCountries.map(c => c.name),
            datasets: [{
                label: 'Économie',
                data: topCountries.map(c => c.economy || 0),
                backgroundColor: '#5865f2'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                }
            },
            scales: {
                y: {
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: '#40444b'
                    }
                },
                x: {
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: '#40444b'
                    }
                }
            }
        }
    });
}

function updateTables() {
    updateCountriesTable();
    updatePlayersTable();
    updateWarsTable();
    updateEventsTable();
}

function updateCountriesTable() {
    const tbody = document.getElementById('countries-table');
    if (!currentData.countries) return;
    
    tbody.innerHTML = currentData.countries.map(country => {
        const resources = country.resources || {};
        const leader = currentData.players ? currentData.players.find(p => p.id === country.leader_id) : null;
        
        return `
            <tr>
                <td><strong>${country.name}</strong></td>
                <td>${leader ? leader.username : 'Aucun'}</td>
                <td>${formatNumber(country.population || 0)}</td>
                <td><span class="badge bg-success">${country.economy || 0}/100</span></td>
                <td><span class="badge bg-danger">${country.army_strength || 0}/100</span></td>
                <td><span class="badge bg-info">${country.stability || 0}%</span></td>
                <td>
                    <span class="badge ${country.is_locked ? 'bg-warning' : 'bg-success'}">
                        ${country.is_locked ? 'Verrouillé' : 'Ouvert'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editCountry('${country.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteCountry('${country.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function updatePlayersTable() {
    const tbody = document.getElementById('players-table');
    if (!currentData.players) return;
    
    tbody.innerHTML = currentData.players.map(player => {
        const country = currentData.countries ? currentData.countries.find(c => c.id === player.country_id) : null;
        
        return `
            <tr>
                <td><strong>${player.username}</strong></td>
                <td>${country ? country.name : 'Aucun pays'}</td>
                <td><span class="badge bg-primary">${player.role || 'recruit'}</span></td>
                <td>${formatNumber(player.balance || 0)} �</td>
                <td>${formatDate(player.joined_at)}</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="editPlayer('${player.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deletePlayer('${player.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function updateWarsTable() {
    const tbody = document.getElementById('wars-table');
    if (!currentData.wars) return;
    
    tbody.innerHTML = currentData.wars.map(war => {
        const attacker = currentData.countries ? currentData.countries.find(c => c.id === war.attacker_id) : null;
        const defender = currentData.countries ? currentData.countries.find(c => c.id === war.defender_id) : null;
        const status = war.ended_at ? 'Terminée' : 'Active';
        const statusClass = war.ended_at ? 'bg-secondary' : 'bg-danger';
        
        return `
            <tr>
                <td>${attacker ? attacker.name : 'Inconnu'}</td>
                <td>${defender ? defender.name : 'Inconnu'}</td>
                <td>${formatDate(war.started_at)}</td>
                <td><span class="badge ${statusClass}">${status}</span></td>
                <td>
                    ${!war.ended_at ? `
                        <button class="btn btn-sm btn-warning" onclick="endWar('${war.id}')">
                            <i class="fas fa-stop"></i> Terminer
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-danger" onclick="deleteWar('${war.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function updateEventsTable() {
    const tbody = document.getElementById('events-table');
    if (!currentData.events) return;
    
    tbody.innerHTML = currentData.events.map(event => {
        const country = currentData.countries ? currentData.countries.find(c => c.id === event.target_country) : null;
        const impact = event.impact ? JSON.stringify(event.impact) : 'Aucun';
        
        return `
            <tr>
                <td><span class="badge bg-warning">${event.type}</span></td>
                <td>${event.description}</td>
                <td>${country ? country.name : 'Global'}</td>
                <td>${formatDate(event.created_at)}</td>
                <td><small>${impact}</small></td>
            </tr>
        `;
    }).join('');
}

function updateRecentActivity() {
    const container = document.getElementById('recent-activity');
    if (!currentData.events || currentData.events.length === 0) {
        container.innerHTML = '<div class="text-muted">Aucune activité récente</div>';
        return;
    }
    
    const recentEvents = currentData.events.slice(0, 5);
    container.innerHTML = recentEvents.map(event => {
        let icon = 'fa-clock';
        let color = 'text-info';
        
        if (event.type === 'war') {
            icon = 'fa-sword';
            color = 'text-danger';
        } else if (event.type === 'trade') {
            icon = 'fa-coins';
            color = 'text-warning';
        } else if (event.type === 'player_join') {
            icon = 'fa-user-plus';
            color = 'text-success';
        }
        
        return `
            <div class="d-flex align-items-center mb-2">
                <i class="fas ${icon} ${color} me-2"></i>
                <small>${event.description}</small>
            </div>
        `;
    }).join('');
}

function updateAlerts() {
    const container = document.getElementById('alerts');
    const alerts = [];
    
    // Vérifier les pays avec une stabilité faible
    if (currentData.countries) {
        const lowStability = currentData.countries.filter(c => c.stability < 30);
        if (lowStability.length > 0) {
            alerts.push({
                type: 'warning',
                message: `${lowStability.length} pays avec une stabilité faible`
            });
        }
    }
    
    // Vérifier les guerres actives
    if (currentData.wars) {
        const activeWars = currentData.wars.filter(w => !w.ended_at);
        if (activeWars.length > 5) {
            alerts.push({
                type: 'danger',
                message: `${activeWars.length} guerres actives`
            });
        }
    }
    
    if (alerts.length === 0) {
        container.innerHTML = '<div class="text-success"><i class="fas fa-check-circle"></i> Aucune alerte</div>';
    } else {
        container.innerHTML = alerts.map(alert => `
            <div class="alert alert-${alert.type} alert-sm mb-2">
                <i class="fas fa-exclamation-triangle"></i> ${alert.message}
            </div>
        `).join('');
    }
}

<<<<<<< HEAD
// ==================== TRANSACTIONS ====================
function loadTransactions() {
    const t = document.getElementById('txType').value;
    const c = document.getElementById('txCountry').value.trim();
    const p = document.getElementById('txPlayer').value.trim();
    const params = new URLSearchParams();
    if (t) params.set('type', t);
    if (c) params.set('country_id', c);
    if (p) params.set('player_id', p);
    fetch(`/api/transactions?${params.toString()}`)
    .then(r => r.json())
    .then(data => {
        const tbody = document.getElementById('transactions-table');
        if (!data.success) { tbody.innerHTML = '<tr><td colspan="5">Erreur</td></tr>'; return; }
        const rows = (data.data || []).map(tx => {
            const details = tx.type === 'work' ? `+${formatNumber(tx.amount||0)} 💵`
                : tx.type === 'produce' ? `${tx.resource||''}: +${formatNumber(tx.amount||0)}`
                : tx.type === 'trade' ? `Give: ${JSON.stringify(tx.give||{})} / Receive: ${JSON.stringify(tx.receive||{})} / Fee: ${formatNumber(tx.fee||0)}`
                : tx.type === 'tick' ? `Maintenance/Inflation: ${formatNumber(tx.amount||0)}`
                : '';
            const badge = tx.type === 'work' ? 'bg-success'
                : tx.type === 'produce' ? 'bg-info'
                : tx.type === 'trade' ? 'bg-warning'
                : 'bg-secondary';
            return `
                <tr>
                    <td>${formatDate(tx.created_at)}</td>
                    <td><span class="badge ${badge}">${tx.type}</span></td>
                    <td><small>${tx.country_id||''}</small></td>
                    <td><small>${tx.player_id||''}</small></td>
                    <td><small>${details}</small></td>
                </tr>
            `;
        }).join('');
        tbody.innerHTML = rows || '<tr><td colspan="5" class="text-center text-muted">Aucune transaction</td></tr>';
    })
    .catch(() => showAlert('danger','Erreur de connexion'));
}

function exportTransactions() {
    const t = document.getElementById('txType').value;
    const c = document.getElementById('txCountry').value.trim();
    const p = document.getElementById('txPlayer').value.trim();
    const params = new URLSearchParams();
    if (t) params.set('type', t);
    if (c) params.set('country_id', c);
    if (p) params.set('player_id', p);
    fetch(`/api/transactions?${params.toString()}`)
    .then(r => r.json())
    .then(data => {
        if (!data.success) { showAlert('danger', 'Erreur'); return; }
        const dataStr = JSON.stringify(data.data||[], null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        const name = `transactions_${new Date().toISOString().split('T')[0]}.json`;
        const a = document.createElement('a');
        a.setAttribute('href', dataUri);
        a.setAttribute('download', name);
        a.click();
        showAlert('success','Transactions exportées');
    })
    .catch(() => showAlert('danger','Erreur de connexion'));
}

// Auto: ouvrir Transactions au chargement
document.addEventListener('DOMContentLoaded', function() {
    try {
        // masquer toutes les sections puis afficher transactions
        const sections = document.querySelectorAll('.section');
        sections.forEach(s => s.style.display = 'none');
        const tx = document.getElementById('transactions');
        if (tx) tx.style.display = 'block';
        // charger les données
        loadTransactions();
    } catch (e) {
        // fallback silencieux
    }
});

=======
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
// ==================== COUNTRIES ====================

function showCreateCountryModal() {
    const modal = new bootstrap.Modal(document.getElementById('createCountryModal'));
    modal.show();
}

function createCountry() {
    const name = document.getElementById('countryName').value;
    const population = parseInt(document.getElementById('countryPopulation').value);
    const economy = parseInt(document.getElementById('countryEconomy').value);
    
    if (!name) {
        showAlert('danger', 'Le nom du pays est requis');
        return;
    }
    
    fetch('/api/countries', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name,
            population: population,
            economy: economy,
            army_strength: 20,
            stability: 80,
            resources: {
                money: 5000,
                food: 200,
                metal: 50,
                oil: 80,
                energy: 100,
                materials: 30
            },
            is_locked: false
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Pays créé avec succès');
            bootstrap.Modal.getInstance(document.getElementById('createCountryModal')).hide();
            document.getElementById('createCountryForm').reset();
            requestUpdate();
        } else {
            showAlert('danger', data.error || 'Erreur lors de la création');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function editCountry(countryId) {
    const country = currentData.countries.find(c => c.id === countryId);
    if (!country) return;
    
    document.getElementById('editCountryId').value = country.id;
    document.getElementById('editCountryName').value = country.name;
    document.getElementById('editCountryPopulation').value = country.population || 0;
    document.getElementById('editCountryEconomy').value = country.economy || 0;
    document.getElementById('editCountryArmy').value = country.army_strength || 0;
    document.getElementById('editCountryStability').value = country.stability || 0;
    document.getElementById('editCountryLocked').checked = country.is_locked || false;
    
    const resources = country.resources || {};
    document.getElementById('editCountryMoney').value = resources.money || 0;
    document.getElementById('editCountryFood').value = resources.food || 0;
    document.getElementById('editCountryMetal').value = resources.metal || 0;
    document.getElementById('editCountryOil').value = resources.oil || 0;
    document.getElementById('editCountryEnergy').value = resources.energy || 0;
    document.getElementById('editCountryMaterials').value = resources.materials || 0;
    
    const modal = new bootstrap.Modal(document.getElementById('editCountryModal'));
    modal.show();
}

function saveCountry() {
    const countryId = document.getElementById('editCountryId').value;
    const data = {
        name: document.getElementById('editCountryName').value,
        population: parseInt(document.getElementById('editCountryPopulation').value),
        economy: parseInt(document.getElementById('editCountryEconomy').value),
        army_strength: parseInt(document.getElementById('editCountryArmy').value),
        stability: parseInt(document.getElementById('editCountryStability').value),
        is_locked: document.getElementById('editCountryLocked').checked,
        resources: {
            money: parseInt(document.getElementById('editCountryMoney').value),
            food: parseInt(document.getElementById('editCountryFood').value),
            metal: parseInt(document.getElementById('editCountryMetal').value),
            oil: parseInt(document.getElementById('editCountryOil').value),
            energy: parseInt(document.getElementById('editCountryEnergy').value),
            materials: parseInt(document.getElementById('editCountryMaterials').value)
        }
    };
    
    fetch(`/api/countries/${countryId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Pays modifié avec succès');
            bootstrap.Modal.getInstance(document.getElementById('editCountryModal')).hide();
            requestUpdate();
        } else {
            showAlert('danger', data.error || 'Erreur lors de la modification');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function deleteCountry(countryId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce pays ? Cette action est irréversible.')) {
        return;
    }
    
    fetch(`/api/countries/${countryId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Pays supprimé avec succès');
            requestUpdate();
        } else {
            showAlert('danger', data.error || 'Erreur lors de la suppression');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

// ==================== PLAYERS ====================

function editPlayer(playerId) {
    const player = currentData.players.find(p => p.id === playerId);
    if (!player) return;
    
    const newBalance = prompt(`Nouveau solde pour ${player.username}:`, player.balance || 0);
    if (newBalance === null) return;
    
    fetch(`/api/players/${playerId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            balance: parseInt(newBalance)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Joueur modifié avec succès');
            requestUpdate();
        } else {
            showAlert('danger', data.error || 'Erreur lors de la modification');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function deletePlayer(playerId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce joueur ?')) {
        return;
    }
    
    fetch(`/api/players/${playerId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Joueur supprimé avec succès');
            requestUpdate();
        } else {
            showAlert('danger', data.error || 'Erreur lors de la suppression');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function exportPlayers() {
    fetch('/api/players/export')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Créer un fichier JSON à télécharger
            const dataStr = JSON.stringify(data.data, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            
            const exportFileDefaultName = `players_${new Date().toISOString().split('T')[0]}.json`;
            
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
            
            showAlert('success', 'Joueurs exportés avec succès');
        } else {
            showAlert('danger', 'Erreur lors de l\'export');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

// ==================== WARS ====================

function endWar(warId) {
    if (!confirm('Terminer cette guerre ?')) {
        return;
    }
    
    fetch(`/api/wars/${warId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            ended_at: new Date().toISOString()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Guerre terminée avec succès');
            requestUpdate();
        } else {
            showAlert('danger', data.error || 'Erreur');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function deleteWar(warId) {
    if (!confirm('Supprimer cette guerre ?')) {
        return;
    }
    
    fetch(`/api/wars/${warId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Guerre supprimée avec succès');
            requestUpdate();
        } else {
            showAlert('danger', data.error || 'Erreur');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function endAllWars() {
    if (!confirm('Terminer toutes les guerres actives ?')) return;
    
    fetch('/api/wars/end-all', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', `${data.count} guerre(s) terminée(s)`);
            requestUpdate();
        } else {
            showAlert('danger', 'Erreur lors de la fin des guerres');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

// ==================== EVENTS ====================

function triggerRandomEvent() {
    fetch('/api/events/trigger', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Événement déclenché avec succès');
            requestUpdate();
        } else {
            showAlert('danger', 'Erreur lors du déclenchement');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

// ==================== STATISTICS ====================

function generateReport() {
    showAlert('info', 'Génération du rapport...');
    
    const reportData = {
        date: new Date().toISOString(),
        countries: currentData.countries.length,
        players: currentData.players.length,
        activeWars: currentData.wars.filter(w => !w.ended_at).length,
        topEconomy: currentData.countries
            .sort((a, b) => (b.economy || 0) - (a.economy || 0))
            .slice(0, 5)
            .map(c => ({ name: c.name, economy: c.economy })),
        topMilitary: currentData.countries
            .sort((a, b) => (b.army_strength || 0) - (a.army_strength || 0))
            .slice(0, 5)
            .map(c => ({ name: c.name, army_strength: c.army_strength }))
    };
    
    const dataStr = JSON.stringify(reportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `report_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    showAlert('success', 'Rapport généré avec succès');
}

// ==================== TOOLS ====================

function resetAllResources() {
    if (!confirm('Réinitialiser toutes les ressources ? Cette action affectera tous les pays.')) return;
    
    fetch('/api/tools/reset-resources', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', `${data.count} pays réinitialisés`);
            requestUpdate();
        } else {
            showAlert('danger', 'Erreur lors de la réinitialisation');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function resetAllStats() {
    if (!confirm('Réinitialiser toutes les statistiques ? Cette action affectera tous les pays.')) return;
    
    fetch('/api/tools/reset-stats', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', `${data.count} pays réinitialisés`);
            requestUpdate();
        } else {
            showAlert('danger', 'Erreur lors de la réinitialisation');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function backupDatabase() {
    showAlert('info', 'Sauvegarde en cours...');
    
    fetch('/api/tools/backup', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', `Sauvegarde créée: ${data.file}`);
        } else {
            showAlert('danger', 'Erreur lors de la sauvegarde');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function promoteAllCitizens() {
    if (!confirm('Promouvoir tous les recrues en citoyens ?')) return;
    
    fetch('/api/tools/promote-citizens', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', `${data.count} joueur(s) promu(s)`);
            requestUpdate();
        } else {
            showAlert('danger', 'Erreur lors de la promotion');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function giveAllMoney() {
    const amount = prompt('Montant à donner à chaque joueur:', '1000');
    if (amount === null) return;
    
    fetch('/api/tools/give-money', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            amount: parseInt(amount)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', `${amount}� donnés à ${data.count} joueur(s)`);
            requestUpdate();
        } else {
            showAlert('danger', 'Erreur lors de la distribution');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function resetAllPlayers() {
    if (!confirm('Réinitialiser tous les joueurs ? Cette action est irréversible !')) return;
    
    fetch('/api/tools/reset-players', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', `${data.count} joueur(s) réinitialisé(s)`);
            requestUpdate();
        } else {
            showAlert('danger', 'Erreur lors de la réinitialisation');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur de connexion');
    });
}

function showConfigModal() {
    showAlert('info', 'Fonctionnalité en cours de développement');
}

function viewLogs() {
    showAlert('info', 'Les logs sont envoyés sur Discord via le webhook configuré');
}

function restartBot() {
    if (!confirm('Redémarrer le bot ? Cette action prendra quelques secondes.')) return;
    
    showAlert('info', 'Fonctionnalité en cours de développement - Contactez l\'administrateur système');
<<<<<<< HEAD
}

// Don (Admin)
function openGiveModal() {
    const targetType = prompt('Cible: player/country/all_players/all_countries', 'player');
    if (!targetType) return;
    let targetId = null;
    if (targetType === 'player' || targetType === 'country') {
        targetId = prompt('ID interne de la cible (players.id ou countries.id)');
        if (!targetId) return;
    }
    const resource = prompt('Ressource: balance (joueur) ou money/food/metal/oil/energy/materials (pays)', 'balance');
    if (!resource) return;
    const amountStr = prompt('Montant (entier, positif ou négatif)', '1000');
    if (amountStr === null) return;
    const amount = parseInt(amountStr);

    fetch('/api/tools/give', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_type: targetType, target_id: targetId, resource, amount })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) { showAlert('success', 'Don effectué'); requestUpdate(); }
        else { showAlert('danger', data.error || 'Erreur lors du don'); }
    })
    .catch(() => showAlert('danger', 'Erreur de connexion'));
=======
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
}