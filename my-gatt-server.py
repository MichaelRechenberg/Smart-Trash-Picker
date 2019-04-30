import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

import array
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject
import sys

from random import randint


# Example BLE code from bluez
from ble_advertisement import Advertisement, find_adapter, \
        BLUEZ_SERVICE_NAME, LE_ADVERTISING_MANAGER_IFACE, \
        DBUS_OM_IFACE, DBUS_PROP_IFACE
from ble_gatt_server import Service, Characteristic, Descriptor



# Application UIUDS
# See https://www.argenox.com/library/bluetooth-low-energy/ble-advertising-primer/#a-quick-look-into-uuids
#    for overview of BLE UIUDs
SMART_TRASH_PICKER_SERVICE_FULL_UIUD = '00001337-0000-1000-8000-00805f9b34fb'
SMART_TRASH_PICKER_SERVICE_16_BIT_UIUD = '1337'


class SmartTrashPickerAdvertisement(Advertisement):
    """Advertisement for the SmartTrashPicker
    """

    def __init__(self, bus, index):
        # This is a peripheral device
        Advertisement.__init__(self, bus, index, 'peripheral')
        # Have our custom UIUD 
        # TODO: See if I need to send whole 128-bit UIUD b/c its non-standard :(
        self.add_service_uuid(SMART_TRASH_PICKER_SERVICE_16_BIT_UIUD)
        # We don't need to add manufacturer data
        # self.add_manufacturer_data(0xffff, [0x00, 0x01, 0x02, 0x03, 0x04])
        # We don't need to add service data 
        # self.add_service_data('9999', [0x00, 0x01, 0x02, 0x03, 0x04])
        self.add_local_name('SmartTrashPickerAdvertisement')
        self.include_tx_power = True
        # Transport Discovery Data
        self.add_data(0x26, [0x01, 0x01, 0x00])

# Callbacks to register with the advertising manager
def stp_register_ad_cb():
    print("STP Advertisement registered")

def stp_register_ad_error_cb(error):
    print("Failed to register advertisment")
    print(error)


# Main code
if __name__ == '__main__':

    # Initialize the main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # Get access to the system bus (so we can communicate with BlueZ components)
    bus = dbus.SystemBus()

    adapter = find_adapter(bus)
    if not adapter:
        print('LEAdvertisingManager interface not found')
        exit(1)

    # Turn on the BLE adapter
    adapter_props = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            "org.freedesktop.DBus.Properties"
    )
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))


    # Get the advertisment manager from DBus
    ad_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            LE_ADVERTISING_MANAGER_IFACE
    )


    # Get the main loop
    mainloop = GObject.MainLoop()

    # Register our advertisment with bluez's advertising managager
    stp_advertisement = SmartTrashPickerAdvertisement(bus, 0)

    ad_manager.RegisterAdvertisement(
            stp_advertisement.get_path(),
            {},
            reply_handler=stp_register_ad_cb,
            error_handler=stp_register_ad_error_cb
    )


    # Start the main loop (blocks until process is killed/keyboard interrupt/etc)
    print("Advertising forever")
    mainloop.run()


        

