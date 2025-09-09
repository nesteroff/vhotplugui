import logging
import argparse
import customtkinter as ctk
from vhotplugui.apiclient import APIClient

logger = logging.getLogger("vhotplugui")

main_window = None # pylint: disable=invalid-name

def message_box(title, message):
    window = ctk.CTkToplevel()
    window.title(title)
    window.geometry("400x150")
    window.resizable(False, False)
    window.attributes("-topmost", True)

    label = ctk.CTkLabel(window, text=message, wraplength=380, justify="center", font=ctk.CTkFont(size=16, weight="bold"))
    label.pack(pady=20, padx=10)
    btn = ctk.CTkButton(window, text="OK", width=80, command=window.destroy)
    btn.pack(pady=10)

    window.grab_set()
    window.wait_window()

def connect_device(usb_dev, vm_combo, window):
    selected_vm = vm_combo.get()
    device_node = usb_dev.get("device_node")
    logger.info("Connecting %s to %s", device_node, selected_vm)
    client = APIClient(transport="tcp")
    client.connect()
    logger.info("Attaching %s to %s", device_node, selected_vm)
    res = client.usb_attach(device_node, selected_vm)
    logger.info("Result: %s", res)
    if res.get("result") == "failed":
        error_msg = res.get("error")
        message_box("USB Attach Failed", f"Failed to attach: {error_msg}")
    else:
        logger.info("Successfully attached")
    window.destroy()

def deny_device(_usb_dev, window):
    window.destroy()

def show_usb_window(usb_dev, vm_list):
    window = ctk.CTkToplevel()
    window.title("Choose Virtual Machine for USB Device")
    window.geometry("450x160")
    window.resizable(False, False)
    window.attributes("-topmost", True)

    usb_name = usb_dev.get("vendor_name") + " " + usb_dev.get("product_name")
    label = ctk.CTkLabel(window, text=usb_name, font=ctk.CTkFont(size=16, weight="bold"))
    label.pack(pady=10)

    vm_combo = ctk.CTkComboBox(window, values=vm_list)
    vm_combo.set(vm_list[0])
    vm_combo.pack(fill="x", padx=20, pady=10)

    button_frame = ctk.CTkFrame(window, fg_color="transparent")
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)
    button_frame.pack(fill="x", padx=10, pady=10)
    deny_btn = ctk.CTkButton(button_frame, text="Deny", width=100, command=lambda: deny_device(usb_dev, window))
    deny_btn.grid(row=0, column=0, padx=10, sticky="W")
    connect_btn = ctk.CTkButton(button_frame, text="Connect", width=100, command=lambda: connect_device(usb_dev, vm_combo, window))
    connect_btn.grid(row=0, column=1, padx=10, sticky="E")

    window.mainloop()

def notification(msg):
    logger.info("Notification received: %s", msg)
    try:
        if msg["event"] == "usb_select_vm":
            usb_dev = msg.get("usb_device")
            vm_list = msg.get("allowed_vms")
            main_window.after(0, show_usb_window, usb_dev, vm_list)
    except ValueError:
        logger.error("Invalid notification format: %s", msg)

def main():
    global main_window # pylint: disable=global-statement
    parser = argparse.ArgumentParser(description="User interface for vhotplug")
    parser.add_argument("-d", "--debug", default=False, action=argparse.BooleanOptionalAction, help="Enable debug messages")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("-p", "--port", type=int, default=2000)
    parser.add_argument("-c", "--cid", type=int, default=2)
    parser.add_argument("-t", "--transport", type=str, default="tcp")
    args = parser.parse_args()

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    client = APIClient(host=args.host, port=args.port, cid = args.cid, transport=args.transport)
    client.connect()
    usb_list = client.usb_list()
    logger.info("USB Devices: %s", usb_list)

    APIClient.recv_notifications(callback=notification, host=args.host, port=args.port, cid = args.cid, transport=args.transport)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    main_window = ctk.CTk()
    main_window.withdraw()
    try:
        main_window.mainloop()
    except KeyboardInterrupt:
        logger.info("Ctrl+C pressed")
    logger.info("Exiting")
