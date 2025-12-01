async function updateDashboard() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('nb-accepted').innerText = data.stats.accepted;
        document.getElementById('nb-refused').innerText = data.stats.refused;

        const ings = data.stats.ingredients;
        const total = ings.R + ings.J + ings.V + ings.B;

        const updateBar = (key, val) => {
            const elCount = document.getElementById(`count-${key}`);
            const elBar = document.getElementById(`bar-${key}`);
            
            if(elCount) elCount.innerText = val;
            
            const pct = total > 0 ? (val / total) * 100 : 0;
            if(elBar) elBar.style.width = `${pct}%`;
        };

        updateBar('R', ings.R);
        updateBar('J', ings.J);
        updateBar('V', ings.V);
        updateBar('B', ings.B);

        document.getElementById('connection-dot').style.backgroundColor = '#a6e3a1';

        const container = document.getElementById('stations-container');
        container.innerHTML = '';

        data.stations.sort((a, b) => a.id - b.id);

        data.stations.forEach(station => {
            const ratio = station.max_capacity > 0 ? (station.current_load / station.max_capacity) * 100 : 0;
            const isFull = ratio >= 100;
            const isDown = !station.available;

            let badgesHtml = `<span class="badge">Taille ${station.size}</span>`;
            
            let restrText = "";
            if (Array.isArray(station.restrictions)) {
                restrText = station.restrictions.join(', ');
            } else {
                restrText = station.restrictions;
            }

            if (restrText && restrText !== '-' && restrText !== '') {
                badgesHtml += `<span class="badge" style="border-color:var(--md-sys-color-error);">🚫 ${restrText}</span>`;
            }

            if (isDown) {
                badgesHtml += `<span class="badge" style="background:var(--md-sys-color-error-container); color:var(--md-sys-color-error);">HS</span>`;
            }

            const html = `
                <div class="station-row" style="opacity: ${isDown ? 0.5 : 1}">
                    <div class="station-header">
                        <span class="station-id">Poste #${station.id}</span>
                        <div class="station-badges">${badgesHtml}</div>
                    </div>
                    
                    <div class="progress-container">
                        <div class="progress-bar" style="width: ${ratio}%; ${isFull ? 'background-color: var(--md-sys-color-error);' : ''}"></div>
                    </div>
                    
                    <div class="load-text">
                        ${station.current_load} / ${station.max_capacity} pizzas
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', html);
        });

    } catch (error) {
        console.error("Erreur Web:", error);
        document.getElementById('connection-dot').style.backgroundColor = '#F2B8B5';
    }
}

setInterval(updateDashboard, 1000);
updateDashboard();