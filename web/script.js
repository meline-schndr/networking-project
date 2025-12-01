async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('nb-accepted').innerText = data.accepted;
        document.getElementById('nb-refused').innerText = data.refused;
        
        document.querySelector('.status-dot').style.background = '#a6e3a1';
    } catch (error) {
        console.error("Erreur connexion serveur:", error);
        document.querySelector('.status-dot').style.background = '#f38ba8';
    }
}

setInterval(updateStats, 2000);
updateStats();