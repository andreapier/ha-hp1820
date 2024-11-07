"""Constants for Hp1820 integration."""

CONF_SYSTEM_IP = "system_ip"
CONF_SCAN_INTERVAL = "scan_interval"
DOMAIN = "hp1820"
NOTIFICATION_MESSAGE = (
    "Toggling the switch failed. Please check the device and try again."
)
NOTIFICATION_TITLE = "Unable to toggle the switch"
NOTIFICATION_IDENTIFIER = "hp1820_output_fail"
KEY_DEVICE = "device"
KEY_COORDINATOR = "coordinator"
KEY_UNSUBSCRIBER = "options_unsubscriber"
# Defines the default scan interval in seconds.
SCAN_INTERVAL_DEFAULT = 120
