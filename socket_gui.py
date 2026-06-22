import tkinter as tk
from tkinter import Button, ttk, messagebox
from tkinter.scrolledtext import ScrolledText

import socket_listener as sl

FONT = ("Segoe UI", 10)

class SocketListenerGUI:
    #init method to create the main GUI window
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Socket Listener GUI")
        self.root.geometry("600x400")


        Button.frame = ttk.Frame(self.root)
        Button.frame.pack(fill="x", pady=12, padx=16)

        self.run_button = ttk.Button(Button.frame, text="Open Socket Panel", command=self.open_socket_panel)
        self.run_button.pack()

    #Beginning of the socket GUI panel
    def open_socket_panel(self) -> None:
        if hasattr(self, "socket_panel") and self.socket_panel.winfo_exists():
            self.socket_panel.lift()
            return

        self.socket_panel = tk.Toplevel(self.root)
        self.socket_panel.title("Socket Listeners")
        self.socket_panel.geometry("600x600")

        left_frame = ttk.Frame(self.socket_panel)
        left_frame.pack(side="left", fill="y", padx=8, pady=8)

        ttk.Label(left_frame, text="Active Listeners:").pack(anchor="w")
        self.socket_listbox = tk.Listbox(left_frame, height=10, width=25)
        self.socket_listbox.pack(pady=(4, 8))

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_socket_list).pack(side="left")
        ttk.Button(btn_frame, text="Stop Selected", command=self.stop_selected_listener).pack(side="left", padx=6)

        # Controls to start a new listener
        ttk.Label(left_frame, text="Start New Listener:").pack(anchor="w", pady=(12, 0))
        host_frame = ttk.Frame(left_frame)
        host_frame.pack(fill="x", pady=2)
        ttk.Label(host_frame, text="Host:").pack(side="left")
        self.socket_host_entry = ttk.Entry(host_frame)
        self.socket_host_entry.insert(0, "localhost")
        self.socket_host_entry.pack(side="left", fill="x", expand=True, padx=4)

        port_frame = ttk.Frame(left_frame)
        port_frame.pack(fill="x", pady=2)
        ttk.Label(port_frame, text="Port:").pack(side="left")
        self.socket_port_entry = ttk.Entry(port_frame)
        self.socket_port_entry.insert(0, "9999")
        self.socket_port_entry.pack(side="left", fill="x", expand=True, padx=4)

        ttk.Button(left_frame, text="Start", command=self.start_listener_from_ui).pack(pady=(8, 0))

        # Message send controls
        ttk.Label(left_frame, text="Send Message:").pack(anchor="w", pady=(12, 0))
        self.send_host_entry = ttk.Entry(left_frame)
        self.send_host_entry.insert(0, "localhost")
        self.send_host_entry.pack(fill="x", pady=2)
        self.send_port_entry = ttk.Entry(left_frame)
        self.send_port_entry.insert(0, "9999")
        self.send_port_entry.pack(fill="x", pady=2)
        self.send_message_entry = ttk.Entry(left_frame)
        self.send_message_entry.insert(0, "Hello from GUI")
        self.send_message_entry.pack(fill="x", pady=2)
        ttk.Button(left_frame, text="Send", command=self.send_message_from_ui).pack(pady=(4, 0))

        # Right side: message log
        right_frame = ttk.Frame(self.socket_panel)
        right_frame.pack(side="right", fill="both", expand=True, padx=8, pady=8)
        ttk.Label(right_frame, text="Messages:").pack(anchor="w")
        self.socket_message_log = ScrolledText(right_frame, state="disabled", wrap="word")
        self.socket_message_log.pack(fill="both", expand=True)

        self.refresh_socket_list()


    def refresh_socket_list(self) -> None:
        self.socket_listbox.delete(0, tk.END)
        #If listing active ports fails, show an error message and return
        try:
            ports = sl.list_active_ports()
        except Exception as exc:  # pragma: no cover - defensive UI
            messagebox.showerror("Error", f"Could not list active listeners: {exc}")
            return
        #Display active listeners in the listbox
        for host, port in ports:
            self.socket_listbox.insert(tk.END, f"{host}:{port}")


    def start_listener_from_ui(self) -> None:
        #Get host and port from the UI entries, defaulting to localhost:9999 if empty
        #The host needs to be either a valid hostname or IP address, and the port needs to be an integer between 1 and 65535
        host = self.socket_host_entry.get().strip() or "localhost"
        port_str = self.socket_port_entry.get().strip() or "9999"
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Invalid port", "Port must be an integer")
            return

        try:
            sl.start_socket_listener(host, port, self.on_socket_message)
        except OSError as exc:
            messagebox.showerror("Bind Error", f"Could not bind to {host}:{port} — {exc}")
            return
        except Exception as exc:  # pragma: no cover - defensive UI
            messagebox.showerror("Error", f"Failed to start listener: {exc}")
            return

        self.refresh_socket_list()


    def stop_selected_listener(self) -> None:
        sel = self.socket_listbox.curselection()
        if not sel:
            return
        value = self.socket_listbox.get(sel[0])
        if ":" not in value:
            return
        host, port_str = value.split(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            return
        sl.stop_socket_listener(host, port)
        self.refresh_socket_list()


    def send_message_from_ui(self) -> None:
        host = self.send_host_entry.get().strip() or "localhost"
        port_str = self.send_port_entry.get().strip() or "9999"
        message = self.send_message_entry.get().strip()

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Invalid port", "Port must be an integer")
            return

        try:
            sl.send_message(host, port, message)
        except Exception as exc:
            messagebox.showerror("Send Error", f"Failed to send message: {exc}")
            return

        messagebox.showinfo("Sent", f"Message sent to {host}:{port}")


    def on_socket_message(self, message: str) -> None:
        try:
            self.socket_message_log.config(state="normal")
            self.socket_message_log.insert(tk.END, message + "\n")
            self.socket_message_log.see(tk.END)
            self.socket_message_log.config(state="disabled")
        except Exception:
            # UI might be closed; ignore
            pass


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Socket Listener GUI Test")
    root.geometry("600x400")
    gui = SocketListenerGUI(root)
    root.mainloop()