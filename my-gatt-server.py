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
from ble_gatt_server import Service, Characteristic, Descriptor, \
        Application, \
        GATT_SERVICE_IFACE, GATT_CHRC_IFACE, GATT_DESC_IFACE, \
        GATT_MANAGER_IFACE



# Application UIUDS
# See https://www.argenox.com/library/bluetooth-low-energy/ble-advertising-primer/#a-quick-look-into-uuids
#    for overview of BLE UIUDs
SMART_TRASH_PICKER_SERVICE_FULL_UIUD = '00001337-0000-1000-8000-00805f9b34fb'
SMART_TRASH_PICKER_SERVICE_16_BIT_UIUD = '1337'


# Advertisment classes
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

############################################################3
# GATT classes (Service, Characteristic, Descriptor)

# TODO: switch to 'indicate' flag if reliability is an issue
class TrashGrabbedChrc(Characteristic):
    """Characteristic that will notify/indicate when trash has been picked up

    """

    # 16-bit UIUD for the TrashGrabbed characteristic
    TRASH_GRABBED_CHRC_UIUD = '1574'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.TRASH_GRABBED_CHRC_UIUD,
                # TODO: remove 'read' after debugging
                ['notify', 'read'],
                service)
        self.notifying = False

    def notify_trash_grabbed(self):
        """Invoke this method to notify that trash has been grabbed
            (e.g. one thread will invoke this when it sees that the
            IR sensor has been tripped in the handle)
        """
        if not self.notifying:
            return
        self.PropertiesChanged(
                GATT_CHRC_IFACE,
                { 'Value': [dbus.Boolean(1)] },
                []
        )


    # TODO: Remove ReadValue after debugging
    def ReadValue(self, options):
        print("ReadValue invoked")
        return [ dbus.Byte('H'), dbus.Byte('I') ]

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False



class SmartTrashPickerService(Service):
    """Smart Trash Picker Service (notify client when trash is picked up)
    """

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, SMART_TRASH_PICKER_SERVICE_FULL_UIUD, True)
        self.add_characteristic(TrashGrabbedChrc(bus, 0, self))



class SmartTrashPickerApplication(Application):
    """Smart Trash Picker Application

        As of now, it only hosts one service, SmartTrashPickerService
    """

    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(SmartTrashPickerService(bus, 36))

def register_app_cb():
    print("STP Application successfully registered")

def register_app_error_cb(error):
    print("Failed to register STP Application")
    print(error)




# TODO: spawn another thread to listen for GPIO inputs and add shit (or have another process get it???)
#      Gobject makes this more complicated...perhaps GBus from another thread???
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
    print("Turning on the Bluetooth Adapter")
    adapter_props = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            "org.freedesktop.DBus.Properties"
    )
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))


    # Get the advertisment manager from DBus
    print("Registering Advertisment")
    ad_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            LE_ADVERTISING_MANAGER_IFACE
    )


    # Register our advertisment with bluez's advertising manager
    stp_advertisement = SmartTrashPickerAdvertisement(bus, 0)

    ad_manager.RegisterAdvertisement(
            stp_advertisement.get_path(),
            {},
            reply_handler=stp_register_ad_cb,
            error_handler=stp_register_ad_error_cb
    )


    # Register the GATT Application
    print("Registering the Application")
    service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE
    )

    stp_app = SmartTrashPickerApplication(bus)

    service_manager.RegisterApplication(
            stp_app.get_path(),
            {},
            reply_handler=register_app_cb,
            error_handler=register_app_error_cb
    )



    # Get the main loop
    mainloop = GObject.MainLoop()


    # Start the main loop (blocks until process is killed/keyboard interrupt/etc)
    print()
    print("STARTING MAIN LOOP")
    print()

    try:
        mainloop.run()

    except Exception as e:
        print("Exception occurred in mainloop")
        print(e)
    finally:
        print("Exiting mainloop")

        # remove any DBus objects for cleanup
        stp_app.remove_from_connection()
        stp_advertisement.remove_from_connection()


        

