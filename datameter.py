import psutil
import time
import FreeSimpleGUI as sg
from threading import Thread, Event
from plyer import notification
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def get_network_usage():
    net_io = psutil.net_io_counters()
    return net_io.bytes_sent, net_io.bytes_recv

def update_usage_label(window, start_sent, start_recv, data_limit_var, stop_event, x_data, y_data_sent, y_data_recv, line_sent, line_recv, canvas):
    while not stop_event.is_set():
        current_sent, current_recv = get_network_usage()
        sent = current_sent - start_sent
        recv = current_recv - start_recv
        window['-SENT-'].update(f"Data sent: {sent / (1024 * 1024):.2f} MB")
        window['-RECV-'].update(f"Data received: {recv / (1024 * 1024):.2f} MB")
        
        total_data = (sent + recv) / (1024 * 1024)  # Total data in MB
        data_limit = float(data_limit_var)
        
        if recv / (1024 * 1024) >= data_limit:
            window['-RECV-'].update(text_color='red')
            notification.notify(
                title="Data Usage Alert",
                message=f"Data received has reached {recv / (1024 * 1024):.2f} MB",
                timeout=10
            )
        else:
            window['-RECV-'].update(text_color='black')
        
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

def start_monitoring(window, start_sent, start_recv, data_limit_var, stop_event, x_data, y_data_sent, y_data_recv, line_sent, line_recv, canvas):
    stop_event.clear()
    thread = Thread(target=update_usage_label, args=(window, start_sent, start_recv, data_limit_var, stop_event, x_data, y_data_sent, y_data_recv, line_sent, line_recv, canvas))
    thread.daemon = True
    thread.start()
    return thread

def stop_monitoring(stop_event):
    stop_event.set()

def main():
    start_sent, start_recv = get_network_usage()
    stop_event = Event()

    sg.theme('DarkBlue')
    
    layout = [
        [sg.Text("Network Usage Monitor", font=("Helvetica", 16))],
        [sg.Text("Data sent: 0.00 MB", key='-SENT-', font=("Helvetica", 16))],
        [sg.Text("Data received: 0.00 MB", key='-RECV-', font=("Helvetica", 16))],
        [sg.Text("Set Data Limit (MB):", font=("Helvetica", 16))],
        [sg.InputText("100", key='-LIMIT-', font=("Helvetica", 16))],
        [sg.Button("Start", key='-START-', font=("Helvetica", 16)), sg.Button("Stop", key='-STOP-', font=("Helvetica", 16))],
        [sg.Canvas(key='-CANVAS-')]
    ]

    window = sg.Window("Network Usage Monitor", layout, finalize=True)

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
    canvas = FigureCanvasTkAgg(fig, master=window['-CANVAS-'].TKCanvas)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=20)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == '-START-':
            data_limit_var = values['-LIMIT-']
            start_monitoring(window, start_sent, start_recv, data_limit_var, stop_event, x_data, y_data_sent, y_data_recv, line_sent, line_recv, canvas)
        elif event == '-STOP-':
            stop_monitoring(stop_event)

    window.close()

if __name__ == "__main__":
    main()
