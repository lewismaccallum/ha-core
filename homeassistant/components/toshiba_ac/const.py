"""Constants for the Toshiba AC integration."""

from datetime import timedelta

DOMAIN = "toshiba_ac"

# API endpoints
API_BASE_URL = "https://mobileapi.toshibahomeaccontrols.com"
API_LOGIN_ENDPOINT = "/api/Consumer/Login"
API_AC_MAPPING_ENDPOINT = "/api/AC/GetConsumerACMapping"
API_AC_STATE_ENDPOINT = "/api/AC/GetCurrentACState"

# Config
CONF_BRAND_ID = "brand_id"
CONF_CONSUMER_ID = "consumer_id"
CONF_CONSUMER_MASTER_ID = "consumer_master_id"
CONF_ACCESS_TOKEN = "access_token"

# Polling interval (cloud service - minimum 60 seconds)
API_TIMEOUT = 10
SCAN_INTERVAL = timedelta(seconds=60)

# Payload byte positions
PAYLOAD_STATE_POS = 0
PAYLOAD_MODE_POS = 1
PAYLOAD_TEMP_POS = 2
PAYLOAD_FAN_POS = 3
PAYLOAD_SWING_POS = 4
PAYLOAD_POWER_POS = 5
PAYLOAD_SELF_CLEAN_POS = 14  # Position 28-29 in hex string = byte 14

# State values (hex)
STATE_ON = "30"
STATE_OFF = "31"

# Mode values (hex)
MODE_HEAT = "43"
MODE_COOL = "42"
MODE_DRY = "44"
MODE_FAN_ONLY = "45"

# Fan speed values (hex)
FAN_AUTO = "41"
FAN_HIGH = "36"
FAN_LOW = "32"

# Swing values (hex)
SWING_OFF = "31"
SWING_AUTO = "32"
SWING_DOWN = "33"

# Power level values (hex)
POWER_NONE = "00"
POWER_50 = "32"
POWER_75 = "4B"
POWER_100 = "64"

# Self-cleaning values (hex)
SELF_CLEAN_OFF = "10"
SELF_CLEAN_ON = "18"

# Temperature range
MIN_TEMP = 16
MAX_TEMP = 30
