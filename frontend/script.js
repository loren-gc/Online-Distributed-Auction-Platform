const API_URL = "http://localhost:5000"; 

// --- FUNÇÕES DA PÁGINA INICIAL (INDEX) ---

async function loadAuctions() {
    try {
        const response = await fetch(`${API_URL}/view-auctions`);
        const auctions = await response.json();
        
        const container = document.getElementById('auctions-list');
        container.innerHTML = '';

        if(auctions.length === 0) {
            container.innerHTML = '<p>Nenhum leilão ativo no momento.</p>';
            return;
        }

        auctions.forEach(auction => {
            const div = document.createElement('div');
            div.className = 'card';
            div.innerHTML = `
                <h3>${auction.title}</h3>
                <p>${auction.description}</p>
                <p><strong>Lance Atual:</strong> R$ ${auction.current_bid}</p>
                <button onclick="window.location.href='auction.html?id=${auction.id}'">Entrar no Leilão</button>
            `;
            container.appendChild(div);
        });
    } catch (error) {
        console.error("Erro ao carregar leilões:", error);
    }
}

async function createAuction(event) {
    event.preventDefault();
    const title = document.getElementById('title').value;
    const desc = document.getElementById('desc').value;
    const price = document.getElementById('price').value;
    const user = document.getElementById('creator').value;
    
    // Calcula data de fim (ex: +10 minutos a partir de agora para teste)
    // No seu HTML você pode colocar um input datetime-local se preferir
    const endTime = new Date(Date.now() + 10 * 60000).toISOString(); 

    const payload = {
        title: title,
        description: desc,
        initial_price: price,
        end_time: endTime,
        user: user
    };

    try {
        const res = await fetch(`${API_URL}/create-auction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        alert(data.message || "Erro ao criar");
        loadAuctions();
    } catch (e) {
        alert("Erro na conexão");
    }
}

// --- FUNÇÕES DA PÁGINA DE DETALHES (AUCTION) ---

async function loadAuctionDetails() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    if (!id) return;

    try {
        const res = await fetch(`${API_URL}/auction/${id}`);
        if (!res.ok) {
            document.body.innerHTML = "<h1>Leilão não encontrado ou encerrado</h1><a href='index.html'>Voltar</a>";
            return;
        }
        const data = await res.json();

        document.getElementById('auction-title').innerText = data.title;
        document.getElementById('auction-desc').innerText = data.description;
        document.getElementById('current-bid').innerText = `R$ ${data.current_bid}`;
        document.getElementById('highest-bidder').innerText = data.highest_bidder;
        document.getElementById('timer').innerText = `Encerra em: ${new Date(data.end_time).toLocaleString()}`;

        // Histórico de Lances
        const historyDiv = document.getElementById('bid-history');
        historyDiv.innerHTML = '';
        if (data.bids_history) {
            data.bids_history.forEach(bid => {
                const item = document.createElement('div');
                item.className = 'bid-item';
                item.innerText = `${bid.user} apostou R$ ${bid.amount}`;
                historyDiv.appendChild(item);
            });
        }
    } catch (e) {
        console.error(e);
    }
}

async function placeBid(event) {
    event.preventDefault();
    const params = new URLSearchParams(window.location.search);
    const auctionId = params.get('id');
    const user = document.getElementById('bid-user').value;
    const amount = document.getElementById('bid-amount').value;

    try {
        const res = await fetch(`${API_URL}/place-bid`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auction_id: auctionId, user: user, amount: amount })
        });
        const data = await res.json();
        
        const msgDiv = document.getElementById('msg');
        if (res.ok) {
            msgDiv.innerText = "Lance aceito!";
            msgDiv.className = "success";
            loadAuctionDetails(); // Atualiza na hora
        } else {
            msgDiv.innerText = data.message;
            msgDiv.className = "error";
        }
    } catch (e) {
        console.error(e);
    }
}

// Polling: Atualiza os dados a cada 2 segundos (Simulação de Real-time simples)
function startPolling() {
    if (window.location.pathname.includes('auction.html')) {
        loadAuctionDetails();
        setInterval(loadAuctionDetails, 2000);
    } else {
        loadAuctions();
        setInterval(loadAuctions, 5000);
    }
}

document.addEventListener("DOMContentLoaded", startPolling);