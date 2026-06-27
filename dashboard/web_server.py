# dashboard/web_server.py
import logging
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO
from core.event_bus import bus
from execution.risk_manager import risk_manager
from brokers.broker_router import active_broker
from config.settings import settings

app = Flask(__name__, template_folder="templates")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class DashboardServer:
    """
    Bridges the internal EventBus to an external Web Browser via Socket.io.
    """
    def __init__(self, host="0.0.0.0", port=8080):
        self.host = host
        self.port = port
        
        # State tracker to push to the UI
        self.ui_state = {
            "system": {
                "mode": settings.broker.MODE, 
                "active_broker": settings.broker.ACTIVE_BROKER
            },
            "broker_status": "DISCONNECTED",
            "market_info": {"price": 0.0, "high": 0.0, "low": 0.0},
            "ai_state": {"buy_prob": 0.0, "sell_prob": 0.0, "status": "MARKET CLOSED - STANDBY"},
            "risk_state": {"daily_pnl": 0.0, "loss_streak": 0, "total_trades": 0, "max_trades": 5, "max_streak": 2},
            "active_trade": None,
            "journal": []
        }

        bus.subscribe("TICK_UPDATE", self._on_tick)
        bus.subscribe("AI_STATE_UPDATE", self._on_ai_update)
        bus.subscribe("TRADE_OPENED", self._on_trade_opened)
        bus.subscribe("TRADE_CLOSED", self._on_trade_closed)

    def _add_log(self, msg: str):
        self.ui_state["journal"].insert(0, msg)
        if len(self.ui_state["journal"]) > 50:
            self.ui_state["journal"].pop()

    def _on_tick(self, tick: dict):
        if tick.get("token") == 256265: # Nifty Spot/Fut token
            ltp = tick["ltp"]
            mi = self.ui_state["market_info"]
            mi["price"] = ltp
            
            # Track High/Low for the UI
            if mi["high"] == 0 or ltp > mi["high"]: mi["high"] = ltp
            if mi["low"] == 0 or ltp < mi["low"]: mi["low"] = ltp
            
            socketio.emit('metrics', self.ui_state)

    def _on_ai_update(self, ai_data: dict):
        self.ui_state["ai_state"]["buy_prob"] = ai_data["buy_prob"]
        self.ui_state["ai_state"]["sell_prob"] = ai_data["sell_prob"]
        
        if ai_data["buy_prob"] > settings.ai.BUY_THRESHOLD or ai_data["sell_prob"] > settings.ai.SELL_THRESHOLD:
            self.ui_state["ai_state"]["status"] = "HIGH CONVICTION ZONE"
        else:
            self.ui_state["ai_state"]["status"] = "SCANNING V6 PRICE ACTION ZONES..."

    def _on_trade_opened(self, trade: dict):
        self.ui_state["active_trade"] = trade
        self._add_log(f"🚀 [ORDER] {trade['side']} {trade['option_symbol']} @ Spot {trade['spot_entry']}")
        socketio.emit('metrics', self.ui_state)

    def _on_trade_closed(self, trade: dict):
        self.ui_state["active_trade"] = None
        self.ui_state["risk_state"]["daily_pnl"] = risk_manager.daily_pnl
        self.ui_state["risk_state"]["loss_streak"] = risk_manager.consecutive_losses
        self.ui_state["risk_state"]["total_trades"] = risk_manager.total_trades
        
        pnl_str = f"₹{trade['pnl']:.2f}" if 'pnl' in trade else "N/A"
        self._add_log(f"🏁 [CLOSED] {trade['symbol']} | {trade['reason']} | PnL: {pnl_str}")
        socketio.emit('metrics', self.ui_state)

    def start(self):
        self.ui_state["broker_status"] = "CONNECTED" if active_broker.is_connected else "DISCONNECTED"
        self.ui_state["risk_state"]["daily_pnl"] = risk_manager.daily_pnl
        self.ui_state["risk_state"]["loss_streak"] = risk_manager.consecutive_losses
        self.ui_state["risk_state"]["total_trades"] = risk_manager.total_trades
        
        self._add_log("⏳ [STARTUP SYNC] Fetching MongoDB cloud data...")
        self._add_log("⚙️ ZERODHA Ported Quantitative Framework Initialized Engine Dynamic...")
        self._add_log(f"🔁 [MODE RECOVERY] Restored to {settings.broker.MODE} mode from cloud.")
        
        logging.info(f"🌐 [DASHBOARD] Starting web server on http://{self.host}:{self.port}")
        thread = threading.Thread(
            target=socketio.run, 
            args=(app,), 
            kwargs={"host": self.host, "port": self.port, "allow_unsafe_werkzeug": True},
            daemon=True
        )
        thread.start()

@app.route('/')
def index():
    return render_template('index.html')

dashboard = DashboardServer()