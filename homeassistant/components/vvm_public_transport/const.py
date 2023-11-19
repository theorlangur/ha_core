"""Constants for the vvm_transport integration."""
from datetime import timedelta

DOMAIN = "vvm_public_transport"
SCAN_INTERVAL = timedelta(minutes=1)

CONF_STOP_ID = "stop_id"
CONF_TIMEFRAME = "timeframe"
CONF_DIRECTION = "direction"
