import logging
import argparse
import customtkinter as ctk
from vhotplugui.apiclient import APIClient

logger = logging.getLogger("vhotplugui")

class MainWindow:
    def __init__(self, client: APIClient):
        self.client = client
        self.main_window = ctk.CTk()
        self.main_window.title("USB Devices")
        self.main_window.geometry("500x250")

        header = ctk.CTkFrame(self.main_window)
        header.pack(fill="x", padx=5, pady=(10, 0))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        lbl_usb_head = ctk.CTkLabel(header, text="USB Device", anchor="w", font=("Arial", 14, "bold"))
        lbl_usb_head.grid(row=0, column=0, padx=5, pady=5, sticky="we")
        lbl_vm_head = ctk.CTkLabel(header, text="Virtual Machine", anchor="w", font=("Arial", 14, "bold"), width=180,)
        lbl_vm_head.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.content_frame = ctk.CTkFrame(self.main_window)
        self.content_frame.pack(fill="both", expand=True, padx=0, pady=0)

    def message_box(self, title, message):
        window = ctk.CTkToplevel(self.main_window)
        window.title(title)
        window.geometry("400x150")
        window.resizable(False, False)
        window.attributes("-topmost", True)

        label = ctk.CTkLabel(window, text=message, wraplength=380, justify="center", font=ctk.CTkFont(size=16, weight="bold"),)
        label.pack(pady=20, padx=10)
        btn = ctk.CTkButton(window, text="OK", width=80, command=window.destroy)
        btn.pack(pady=10)

        window.grab_set()
        window.wait_window()

    def connect_device(self, usb_dev, vm_combo, window):
        selected_vm = vm_combo.get()
        device_node = usb_dev.get("device_node")
        logger.info("Connecting %s to %s", device_node, selected_vm)

        res = self.client.usb_attach(device_node, selected_vm)
        logger.info("Result: %s", res)

        if res.get("result") == "failed":
            error_msg = res.get("error")
            self.message_box("USB Attach Failed", f"Failed to attach: {error_msg}")
        else:
            logger.info("Successfully attached")

        window.destroy()

    def deny_device(self, _usb_dev, window):
        window.destroy()

    def show_select_window(self, usb_dev, vm_list):
        window = ctk.CTkToplevel(self.main_window)
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

        deny_btn = ctk.CTkButton(button_frame, text="Deny", width=100, command=lambda: self.deny_device(usb_dev, window),)
        deny_btn.grid(row=0, column=0, padx=10, sticky="W")

        connect_btn = ctk.CTkButton(button_frame, text="Connect", width=100, command=lambda: self.connect_device(usb_dev, vm_combo, window),)
        connect_btn.grid(row=0, column=1, padx=10, sticky="E")

        #window.mainloop()

    def refresh_list(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        usb_list = self.client.usb_list()
        for dev in usb_list.get("usb_devices"):
            dev_name = dev.get("vendor_name") + " " + dev.get("product_name")
            vm = dev.get("vm")

            row = ctk.CTkFrame(self.content_frame)
            row.pack(fill="x", padx=5, pady=2)

            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)

            lbl_usb = ctk.CTkLabel(row, text=dev_name, anchor="w")
            lbl_usb.grid(row=0, column=0, padx=5, pady=5, sticky="we")

            lbl_vm = ctk.CTkLabel(row, text=vm, anchor="w", width=180)
            lbl_vm.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    def notification(self, msg):
        logger.info("Notification received: %s", msg)
        try:
            if msg["event"] == "usb_select_vm":
                usb_dev = msg.get("usb_device")
                vm_list = msg.get("allowed_vms")
                self.main_window.after(0, self.show_select_window, usb_dev, vm_list)
        except ValueError:
            logger.error("Invalid notification format: %s", msg)

        self.main_window.after(0, self.refresh_list)

    def run(self):
        self.refresh_list()
        self.main_window.mainloop()

def main():
    parser = argparse.ArgumentParser(description="User interface for vhotplug")
    parser.add_argument("-d", "--debug", default=False, action=argparse.BooleanOptionalAction, help="Enable debug messages",)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("-p", "--port", type=int, default=2000)
    parser.add_argument("-c", "--cid", type=int, default=2)
    parser.add_argument("-t", "--transport", type=str, default="tcp")
    args = parser.parse_args()

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    client = APIClient(host=args.host, port=args.port, cid=args.cid, transport=args.transport)
    client.connect()
    usb_list = client.usb_list()
    logger.info("USB Devices: %s", usb_list)

    main_window = MainWindow(client)
    APIClient.recv_notifications(callback=main_window.notification, host=args.host, port=args.port, cid=args.cid, transport=args.transport,)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    try:
        main_window.run()
    except KeyboardInterrupt:
        logger.info("Ctrl+C pressed")
    logger.info("Exiting")
