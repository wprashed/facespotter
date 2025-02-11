import cv2
import face_recognition
import numpy as np
import time
import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Paths
ENCODINGS_DIR = "encodings"
CSV_FILE = "users.csv"

# Ensure encoding directory exists
os.makedirs(ENCODINGS_DIR, exist_ok=True)

# Function to register new user
def register_user():
    name = name_entry.get().strip()
    if not name:
        messagebox.showerror("Error", "Please enter a name")
        return
    
    # Simplify the file dialog to avoid potential issues
    file_path = filedialog.askopenfilename()
    if not file_path:
        messagebox.showerror("Error", "No file selected")
        return
    
    if not os.path.exists(file_path):
        messagebox.showerror("Error", "Selected file does not exist")
        return
    
    image = face_recognition.load_image_file(file_path)
    encoding = face_recognition.face_encodings(image)
    
    if encoding:
        encoding = encoding[0]  # Extract the first encoding
        encoding_path = os.path.join(ENCODINGS_DIR, f"{name}.npy")
        
        # Save encoding
        np.save(encoding_path, encoding)

        # Save to CSV
        with open(CSV_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([name, encoding_path])

        registered_users[name] = encoding  # Store in memory
        messagebox.showinfo("Success", "User Registered Successfully")
    
    else:
        messagebox.showerror("Error", "Could not detect a face, try another image.")

# Load registered users
registered_users = {}
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) != 2:
                continue
            name, encoding_path = row
            if os.path.exists(encoding_path):
                registered_users[name] = np.load(encoding_path)  # Load encodings properly

# Initialize tracking data
tracking_data = {}

# Start video capture
def start_tracking():
    cap = cv2.VideoCapture(0)
    
    # Reduce resolution for better performance
    cap.set(3, 640)  # Width
    cap.set(4, 480)  # Height

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Resize frame to speed up processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown"
            min_distance = 0.6  # Threshold for best match
            
            for registered_name, registered_encoding in registered_users.items():
                distance = face_recognition.face_distance([registered_encoding], face_encoding)[0]
                if distance < min_distance:
                    min_distance = distance
                    name = registered_name
            
            # Start tracking time for recognized user
            if name != "Unknown":
                if name not in tracking_data:
                    tracking_data[name] = {'start_time': time.time(), 'total_time': 0}
                else:
                    # Update total time only if the user is still being tracked
                    tracking_data[name]['total_time'] += time.time() - tracking_data[name]['start_time']
                    tracking_data[name]['start_time'] = time.time()  # Reset start time for next interval
            
            # Scale back to original frame size
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, f"{name}: {tracking_data.get(name, {}).get('total_time', 0):.1f}s", 
                        (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.imshow("User Tracker", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Generate report
    with open("user_tracking_report.csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Username", "Date", "Start Time", "End Time", "Total Time (s)"])
        for name, data in tracking_data.items():
            end_time = time.time()
            writer.writerow([name, datetime.now().strftime("%Y-%m-%d"), 
                             time.strftime("%H:%M:%S", time.localtime(data['start_time'])), 
                             time.strftime("%H:%M:%S", time.localtime(end_time)), 
                             round(data['total_time'], 1)])
    
    cap.release()
    cv2.destroyAllWindows()

# Function to view report with user filter
def view_report():
    # Create a new window for the report
    report_window = tk.Toplevel(root)
    report_window.title("User Tracking Report")
    report_window.geometry("800x400")

    # Dropdown for user selection
    tk.Label(report_window, text="Filter by User:").pack(pady=5)
    user_var = tk.StringVar(report_window)
    user_dropdown = ttk.Combobox(report_window, textvariable=user_var, state="readonly")
    user_dropdown['values'] = ["All"] + list(tracking_data.keys())
    user_dropdown.current(0)
    user_dropdown.pack(pady=5)

    # Treeview for displaying the report
    columns = ("Username", "Date", "Start Time", "End Time", "Total Time (s)")
    tree = ttk.Treeview(report_window, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # Function to update the report based on the selected user
    def update_report():
        selected_user = user_var.get()
        tree.delete(*tree.get_children())  # Clear existing rows

        if os.path.exists("user_tracking_report.csv"):
            with open("user_tracking_report.csv", "r") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    username, date, start_time, end_time, total_time = row
                    if selected_user == "All" or username == selected_user:
                        tree.insert("", "end", values=(username, date, start_time, end_time, total_time))

    # Button to refresh the report
    tk.Button(report_window, text="Refresh Report", command=update_report).pack(pady=10)

    # Initial load of the report
    update_report()

# GUI Setup
root = tk.Tk()
root.title("User Tracker")

tk.Label(root, text="Enter Name:").pack()
name_entry = tk.Entry(root)
name_entry.pack()

tk.Button(root, text="Register User", command=register_user).pack(pady=5)
tk.Button(root, text="Start Tracking", command=start_tracking).pack(pady=5)
tk.Button(root, text="View Report", command=view_report).pack(pady=5)

root.mainloop()