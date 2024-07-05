import psutil
import time
import tkinter as tk
from threading import Thread, Event
from plyer import notification
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def get_network_usage():
    net_io = psutil.net_io_counters()
    return net_io.bytes_sent, net_io.bytes_recv

def update_usage_label(label_sent, label_recv, start_sent, start_recv, data_limit_var, stop_event, style_normal, style_alert, x_data, y_data_sent, y_data_recv, line_sent, line_recv, canvas):
    while not stop_event.is_set():
        current_sent, current_recv = get_network_usage()
        sent = current_sent - start_sent
        recv = current_recv - start_recv
        label_sent.config(text=f"Data sent: {sent / (1024 * 1024):.2f} MB")
        label_recv.config(text=f"Data received: {recv / (1024 * 1024):.2f} MB")
        
        total_data = (sent + recv) / (1024 * 1024)  # Total data in MB
        data_limit = float(data_limit_var.get())
        
        if recv / (1024 * 1024) >= data_limit:
            label_recv.config(style=style_alert)
            notification.notify(
                title="Data Usage Alert",
                message=f"Data received has reached {recv / (1024 * 1024):.2f} MB",
                timeout=10
            )
        else:
            label_recv.config(style=style_normal)
        
        # Update graph data
        x_data.append(time.time())
        y_data_sent.append(sent / (1024 * 1024))
        y_data_recv.append(recv / (1024 * 1024))
        
        # Update graph lines
        line_sent.set_data(x_data, y_data_sent)
        line_recv.set_data(x_data, y_data_recv)
        
        # Rescale the graph
        ax = canvas.figure.axes[0]
        ax.relim()
        ax.autoscale_view()
        
        # Redraw the canvas
        canvas.draw()
        
        time.sleep(1)

def start_monitoring(label_sent, label_recv, start_sent, start_recv, data_limit_var, stop_event, style_normal, style_alert, x_data, y_data_sent, y_data_recv, line_sent, line_recv, canvas):
    stop_event.clear()
    thread = Thread(target=update_usage_label, args=(label_sent, label_recv, start_sent, start_recv, data_limit_var, stop_event, style_normal, style_alert, x_data, y_data_sent, y_data_recv, line_sent, line_recv, canvas))
    thread.daemon = True
    thread.start()
    return thread

def stop_monitoring(stop_event):
    stop_event.set()

def main():
    start_sent, start_recv = get_network_usage()
    stop_event = Event()

    root = ttk.Window(themename="darkly")  # Set the theme
    root.title("Network Usage Monitor")
    root.geometry("800x600")  # Set the initial size of the window

    font_settings = ("Helvetica", 16)  # Set the font and size

    style_normal = "TLabel"
    style_alert = "Alert.TLabel"

    style = ttk.Style()
    style.configure(style_alert, foreground="red")

    label_sent = ttk.Label(root, text="Data sent: 0.00 MB", font=font_settings)
    label_sent.pack(pady=10)

    label_recv = ttk.Label(root, text="Data received: 0.00 MB", font=font_settings)
    label_recv.pack(pady=10)

    data_limit_var = tk.StringVar(value="100")  # Default data limit
    label_limit = ttk.Label(root, text="Set Data Limit (MB):", font=font_settings)
    label_limit.pack(pady=10)
    entry_limit = ttk.Entry(root, textvariable=data_limit_var, font=font_settings)
    entry_limit.pack(pady=10)

    # Start and Stop buttons
    start_button = ttk.Button(root, text="Start", command=lambda: start_monitoring(label_sent, label_recv, start_sent, start_recv, data_limit_var, stop_event, style_normal, style_alert, x_data, y_data_sent, y_data_recv, line_sent, line_recv, canvas))
    start_button.pack(pady=10)

    stop_button = ttk.Button(root, text="Stop", command=lambda: stop_monitoring(stop_event))
    stop_button.pack(pady=10)

    # Create a figure for the graph
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_title("Network Usage Over Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Data (MB)")

    # Initialize data lists
    x_data = []
    y_data_sent = []
    y_data_recv = []

    # Create line objects
    line_sent, = ax.plot(x_data, y_data_sent, label="Data Sent (MB)")
    line_recv, = ax.plot(x_data, y_data_recv, label="Data Received (MB)")

    ax.legend()

    # Create a canvas to display the graph
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()