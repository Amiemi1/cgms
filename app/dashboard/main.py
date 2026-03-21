from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory import Memory

app = FastAPI()


# =========================
# API
# =========================
@app.get("/memories")
def get_memories(chat_id: int):
    session = SessionLocal()
    try:
        memories = session.exec(
            select(Memory).where(Memory.chat_id == chat_id)
        ).all()

        return [
            {
                "summary": m.summary,
                "priority": m.priority,
                "type": m.memory_type
            }
            for m in memories
        ]
    finally:
        session.close()


# =========================
# DASHBOARD UI (UPGRADED)
# =========================
@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <html>
    <head>
        <title>CGMS Dashboard</title>

        <style>
            body {
                font-family: Arial;
                background: #f4f6f8;
                margin: 0;
                padding: 20px;
            }

            h1 {
                text-align: center;
                color: #333;
            }

            .controls {
                text-align: center;
                margin-bottom: 20px;
            }

            input, select, button {
                padding: 10px;
                margin: 5px;
                border-radius: 6px;
                border: 1px solid #ccc;
            }

            button {
                background: #007bff;
                color: white;
                border: none;
                cursor: pointer;
            }

            button:hover {
                background: #0056b3;
            }

            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 15px;
            }

            .card {
                background: white;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 3px 8px rgba(0,0,0,0.1);
            }

            .priority {
                font-weight: bold;
                margin-top: 10px;
            }

            .task { border-left: 5px solid #28a745; }
            .event { border-left: 5px solid #ffc107; }
            .decision { border-left: 5px solid #17a2b8; }

        </style>
    </head>

    <body>

        <h1>📊 CGMS Dashboard</h1>

        <div class="controls">
            <input id="chatId" placeholder="Enter Chat ID" />
            
            <select id="filter">
                <option value="all">All</option>
                <option value="task">Task</option>
                <option value="event">Event</option>
                <option value="decision">Decision</option>
            </select>

            <button onclick="loadData()">Load</button>
        </div>

        <div id="data" class="grid"></div>

        <script>
            let allData = [];

            async function loadData() {
                const chatId = document.getElementById("chatId").value;
                const res = await fetch(`/memories?chat_id=${chatId}`);
                allData = await res.json();

                renderData();
            }

            function renderData() {
                const filter = document.getElementById("filter").value;
                const container = document.getElementById("data");

                container.innerHTML = "";

                let filtered = allData;

                if (filter !== "all") {
                    filtered = allData.filter(x => x.type === filter);
                }

                // sort by priority
                filtered.sort((a, b) => b.priority - a.priority);

                filtered.forEach(item => {
                    const div = document.createElement("div");
                    div.className = "card " + item.type;

                    div.innerHTML = `
                        <div><b>${item.summary}</b></div>
                        <div class="priority">Priority: ${item.priority}</div>
                        <div>Type: ${item.type}</div>
                    `;

                    container.appendChild(div);
                });
            }
        </script>

    </body>
    </html>
    """