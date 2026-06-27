# brokers/broker_router.py
import logging
from config.settings import settings
from brokers.kite_broker import KiteBroker
# from brokers.groww_broker import GrowwBroker # (To be implemented later)

class BrokerRouter:
    """
    Factory class that routes all trading commands to the active broker 
    defined in the system settings.
    """
    @staticmethod
    def get_broker():
        active = settings.broker.ACTIVE_BROKER.upper()
        
        if active == "KITE":
            logging.info("⚙️ [ROUTER] Routing to KiteBroker...")
            return KiteBroker()
        elif active == "GROWW":
            logging.info("⚙️ [ROUTER] Routing to GrowwBroker...")
            # return GrowwBroker()
            raise NotImplementedError("Groww broker module pending.")
        else:
            raise ValueError(f"❌ Unknown broker specified in settings: {active}")

# Instantiate the globally active broker
active_broker = BrokerRouter.get_broker()