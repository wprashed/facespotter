import cv2
import face_recognition
import numpy as np
import time
import os
import csv
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import simpledialog
from PIL import Image, ImageTk  # For embedding images
import uuid  # For generating random names

# Paths
ENCODINGS_DIR = "encodings"
IMAGES_DIR = "images"
CSV_FILE = "users.csv"

# Ensure encoding and images directories exist
os.makedirs(ENCODINGS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Load registered users from CSV and encodings directory
def load_registered_users():
    registered_users = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) != 3:  # Expecting name, encoding_path, image_path
                    continue
                name, encoding_path, image_path = row
                if os.path.exists(encoding_path):
                    registered_users[name] = {
                        "encoding": np.load(encoding_path),
                        "image_path": image_path
                    }
    return registered_users

# Save user data to CSV
def save_user_data(name, encoding_path, image_path):
    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([name, encoding_path, image_path])

# Function to register new user manually
def register_user():
    name = name_entry.get().strip()
    if not name:
        messagebox.showerror("Error", "Please enter a name")
        return
    
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
        image_path = os.path.join(IMAGES_DIR, f"{name}.jpg")
        
        # Save encoding and image
        np.save(encoding_path, encoding)
        cv2.imwrite(image_path, cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB))
        
        # Save to CSV
        save_user_data(name, encoding_path, image_path)
        
        # Add to registered users
        registered_users[name] = {"encoding": encoding, "image_path": image_path}
        messagebox.showinfo("Success", "User Registered Successfully")
    
    else:
        messagebox.showerror("Error", "Could not detect a face, try another image.")

# Initialize tracking data
tracking_data = {}

# Helper function to format time as HH:MM:SS
def format_time(seconds):
    return str(timedelta(seconds=int(seconds))).zfill(8)  # Ensures leading zeros (e.g., 01:10:56)

# Helper function to generate a random name
def generate_random_name():
    return f"User_{str(uuid.uuid4())[:8]}"  # Generate a unique name like "User_12345678"

# Load registered users at startup
registered_users = load_registered_users()

# Start video capture
def start_tracking():
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)  # Use AVFoundation backend for macOS
    
    # Check if the camera opened successfully
    if not cap.isOpened():
        messagebox.showerror("Error", "Unable to open camera. Please check your camera connection.")
        return
    
    # Set higher resolution for better face detection
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Width
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Height

    # Timeout period (in seconds) to wait before closing an interval
    TIMEOUT = 5  # Adjust this value as needed

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Failed to grab frame from the camera.")
            break

        # Resize frame to speed up processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        # Track who is currently detected in this frame
        detected_users = set()

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown"
            min_distance = 0.6  # Threshold for best match
            
            for registered_name, user_data in registered_users.items():
                distance = face_recognition.face_distance([user_data["encoding"]], face_encoding)[0]
                if distance < min_distance:
                    min_distance = distance
                    name = registered_name
            
            # If the face is unknown, register it automatically
            if name == "Unknown":
                # Check if the face encoding already exists in the system
                is_duplicate = False
                for existing_name, user_data in registered_users.items():
                    distance = face_recognition.face_distance([user_data["encoding"]], face_encoding)[0]
                    if distance < 0.5:  # Lower threshold for stricter matching
                        is_duplicate = True
                        name = existing_name  # Assign the existing user's name
                        break

                if not is_duplicate:
                    # Generate a random name and register the user
                    random_name = generate_random_name()
                    encoding_path = os.path.join(ENCODINGS_DIR, f"{random_name}.npy")
                    image_path = os.path.join(IMAGES_DIR, f"{random_name}.jpg")

                    # Save encoding and image
                    np.save(encoding_path, face_encoding)
                    cv2.imwrite(image_path, cv2.cvtColor(frame[top*2:bottom*2, left*2:right*2], cv2.COLOR_BGR2RGB))

                    # Append to CSV
                    save_user_data(random_name, encoding_path, image_path)

                    # Add to registered users
                    registered_users[random_name] = {"encoding": face_encoding, "image_path": image_path}
                    name = random_name  # Update the name to the newly registered user
            
            # Add the user to the detected_users set
            detected_users.add(name)

            # Start or update tracking for this user
            current_time = time.time()
            if name not in tracking_data:
                tracking_data[name] = {'intervals': [[current_time, None]], 'last_seen': current_time}
            else:
                # If the last interval is closed, start a new one
                if tracking_data[name]['intervals'][-1][1] is not None:
                    # Check if the timeout period has passed since the last detection
                    if current_time - tracking_data[name]['last_seen'] > TIMEOUT:
                        tracking_data[name]['intervals'].append([current_time, None])
                # Update last seen time
                tracking_data[name]['last_seen'] = current_time

            # Get the current active interval
            active_interval = tracking_data[name]['intervals'][-1]
            start_time, end_time = active_interval
            active_duration = current_time - start_time if end_time is None else end_time - start_time

            # Scale back to original frame size
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, f"{name}: {format_time(active_duration)}", 
                        (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Close intervals for users who are no longer detected
        for name in tracking_data.keys():
            if name not in detected_users:
                # Check if the timeout period has passed since the last detection
                if time.time() - tracking_data[name]['last_seen'] > TIMEOUT:
                    if tracking_data[name]['intervals'][-1][1] is None:  # If the last interval is open
                        tracking_data[name]['intervals'][-1][1] = time.time()  # Close the interval
        
        # Show the frame
        cv2.imshow("User Tracker", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Close any open intervals before generating the report
    for name in tracking_data.keys():
        if tracking_data[name]['intervals'][-1][1] is None:  # If the last interval is open
            tracking_data[name]['intervals'][-1][1] = time.time()  # Close the interval

    # Generate report (exclude unknown users)
    with open("user_tracking_report.csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Username", "Image", "Start Time", "End Time", "Duration (HH:MM:SS)"])
        for name, data in tracking_data.items():
            if name == "Unknown":  # Skip unknown users from the report
                continue
            for interval in data['intervals']:
                start_time, end_time = interval
                duration = round(end_time - start_time, 1) if end_time is not None else 0
                writer.writerow([name, 
                                 registered_users[name]["image_path"], 
                                 time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)), 
                                 time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)) if end_time else "N/A",
                                 format_time(duration)])
    
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
    user_dropdown['values'] = ["All"] + [name for name in tracking_data.keys() if name != "Unknown"]
    user_dropdown.current(0)
    user_dropdown.pack(pady=5)

    # Treeview for displaying the report
    columns = ("Username", "Image", "Start Time", "End Time", "Duration (HH:MM:SS)")
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
                    username, image_path, start_time, end_time, duration = row
                    if selected_user == "All" or username == selected_user:
                        tree.insert("", "end", values=(username, image_path, start_time, end_time, duration))

    # Button to refresh the report
    tk.Button(report_window, text="Refresh Report", command=update_report).pack(pady=10)

    # Initial load of the report
    update_report()

# Function to manage users
def manage_users():
    # Create a new window for managing users
    users_window = tk.Toplevel(root)
    users_window.title("Manage Users")
    users_window.geometry("800x600")

    # Treeview for displaying users
    columns = ("Username", "Image")
    tree = ttk.Treeview(users_window, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # Populate the treeview with registered users
    for name, data in registered_users.items():
        tree.insert("", "end", values=(name, data["image_path"]))

    # Function to delete a user
    def delete_user():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No user selected")
            return
        name = tree.item(selected_item)["values"][0]
        if name not in registered_users:
            messagebox.showerror("Error", "User not found in the system")
            return
        data = registered_users[name]  # Retrieve the user's data
        try:
            os.remove(os.path.join(ENCODINGS_DIR, f"{name}.npy"))  # Remove encoding file
            os.remove(data["image_path"])  # Remove image file
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete files: {e}")
            return
        del registered_users[name]  # Remove from memory
        tree.delete(selected_item)  # Remove from Treeview
        # Rewrite the CSV file
        try:
            with open(CSV_FILE, "w", newline="") as file:
                writer = csv.writer(file)
                for name, data in registered_users.items():
                    writer.writerow([name, os.path.join(ENCODINGS_DIR, f"{name}.npy"), data["image_path"]])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update CSV file: {e}")
            return
        messagebox.showinfo("Success", "User deleted successfully")

    # Function to update a user's name
    def update_username():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No user selected")
            return
        old_name = tree.item(selected_item)["values"][0]
        new_name = simpledialog.askstring("Update Username", "Enter new username:")
        if not new_name:
            return
        if new_name in registered_users:
            messagebox.showerror("Error", "Username already exists")
            return

        # Update registered_users dictionary
        registered_users[new_name] = registered_users.pop(old_name)

        # Rename files
        old_encoding_path = os.path.join(ENCODINGS_DIR, f"{old_name}.npy")
        new_encoding_path = os.path.join(ENCODINGS_DIR, f"{new_name}.npy")
        os.rename(old_encoding_path, new_encoding_path)
        old_image_path = registered_users[new_name]["image_path"]
        new_image_path = os.path.join(IMAGES_DIR, f"{new_name}.jpg")
        os.rename(old_image_path, new_image_path)
        registered_users[new_name]["image_path"] = new_image_path

        # Update tracking_data dictionary
        if old_name in tracking_data:
            tracking_data[new_name] = tracking_data.pop(old_name)

        # Update the CSV file
        try:
            with open(CSV_FILE, "w", newline="") as file:
                writer = csv.writer(file)
                for name, data in registered_users.items():
                    writer.writerow([name, os.path.join(ENCODINGS_DIR, f"{name}.npy"), data["image_path"]])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update CSV file: {e}")
            return

        # Update the user_tracking_report.csv file
        report_file = "user_tracking_report.csv"
        if os.path.exists(report_file):
            rows = []
            with open(report_file, "r") as file:
                reader = csv.reader(file)
                header = next(reader)  # Preserve the header
                rows.append(header)
                for row in reader:
                    username, image_path, start_time, end_time, duration = row
                    if username == old_name:
                        row[0] = new_name  # Replace old username with new username
                        row[1] = new_image_path  # Update image path
                    rows.append(row)

            # Rewrite the updated rows back to the report file
            with open(report_file, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerows(rows)

        # Update the treeview
        tree.item(selected_item, values=(new_name, new_image_path))
        messagebox.showinfo("Success", "Username updated successfully")

    # Function to update a user's image
    def update_image():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No user selected")
            return
        name = tree.item(selected_item)["values"][0]
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Selected file does not exist")
            return
        # Save the new image
        image_path = os.path.join(IMAGES_DIR, f"{name}.jpg")
        cv2.imwrite(image_path, cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB))
        # Update the registered_users dictionary
        registered_users[name]["image_path"] = image_path
        # Update the CSV file
        try:
            with open(CSV_FILE, "w", newline="") as file:
                writer = csv.writer(file)
                for name, data in registered_users.items():
                    writer.writerow([name, os.path.join(ENCODINGS_DIR, f"{name}.npy"), data["image_path"]])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update CSV file: {e}")
            return
        # Update the treeview
        tree.item(selected_item, values=(name, image_path))
        messagebox.showinfo("Success", "User image updated successfully")

    # Buttons for user management actions
    tk.Button(users_window, text="Delete User", command=delete_user).pack(pady=5)
    tk.Button(users_window, text="Update Username", command=update_username).pack(pady=5)
    tk.Button(users_window, text="Update Image", command=update_image).pack(pady=5)

# GUI Setup
root = tk.Tk()
root.title("User Tracker")

# Set custom application icon
try:
    # Ensure the icon file exists and is in a supported format (e.g., .png, .ico)
    root.iconphoto(False, tk.PhotoImage(file="icon.png"))  # Replace "icon.png" with your icon file
except Exception as e:
    print(f"Failed to load icon: {e}")

tk.Label(root, text="Enter Name:").pack()
name_entry = tk.Entry(root)
name_entry.pack()

tk.Button(root, text="Register User", command=register_user).pack(pady=5)
tk.Button(root, text="Manage Users", command=manage_users).pack(pady=5)
tk.Button(root, text="Start Tracking", command=start_tracking).pack(pady=5)
tk.Button(root, text="View Report", command=view_report).pack(pady=5)

root.mainloop()