# User Tracker Application

The **User Tracker** application is a Python-based tool designed to detect, track, and manage users via facial recognition. It allows you to register users, track their activity in real-time using a camera, generate reports, and manage user details (e.g., rename or update images).

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
4. [File Structure](#file-structure)
5. [Troubleshooting](#troubleshooting)
6. [Contributing](#contributing)
7. [License](#license)

---

## Features

- **User Registration**: Register new users manually by providing a name and uploading an image.
- **Real-Time Tracking**: Detect and track registered users in real-time using a webcam.
- **Automatic Unknown User Registration**: Automatically registers unknown faces with random names.
- **Activity Reporting**: Generate detailed reports of user activity, including start time, end time, and duration.
- **User Management**:
  - Rename users.
  - Update user profile images.
  - Delete users.
- **Customizable Timeout**: Configure the timeout period for closing user tracking intervals.
- **Filterable Reports**: View reports filtered by specific users or all users.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- A webcam or camera connected to your system
- Supported operating systems: macOS, Windows, Linux

### Dependencies

Install the required Python libraries using `pip`:

```bash
pip install opencv-python face-recognition numpy pillow
```

For macOS users, you may need to install OpenCV with AVFoundation support:

```bash
pip install opencv-python-headless
```

### Setup

1. Clone the repository or download the source code.
2. Ensure the following directories exist in the project folder:
   - `encodings/` (for storing user encodings)
   - `images/` (for storing user profile images)
3. Place a custom icon file (`icon.png`) in the root directory if you want to use a custom application icon.

---

## Usage

### Running the Application

Run the application using the following command:

```bash
python app.py
```

### Main Features

1. **Register a New User**:
   - Enter a name in the input field.
   - Click "Register User" and select an image file containing the user's face.

2. **Start Tracking**:
   - Click "Start Tracking" to begin detecting and tracking users in real-time.
   - Detected users will be displayed on the camera feed with their names and active durations.

3. **Manage Users**:
   - Click "Manage Users" to view, rename, update images, or delete users.

4. **View Reports**:
   - Click "View Report" to see a detailed report of user activity.
   - Use the dropdown menu to filter reports by a specific user or view all users.

---

## File Structure

```
user-tracker/
├── app.py                  # Main application script
├── encodings/              # Directory for storing user encodings (.npy files)
├── images/                 # Directory for storing user profile images (.jpg files)
├── users.csv               # CSV file for storing user data (name, encoding path, image path)
├── user_tracking_report.csv # Generated report file for user activity
├── icon.png                # Custom application icon (optional)
└── README.md               # Documentation file
```

---

## Troubleshooting

### Common Issues and Solutions

1. **Camera Not Working**:
   - Ensure your camera is connected and working properly.
   - On macOS, try installing OpenCV with AVFoundation support:
     ```bash
     pip install opencv-python-headless
     ```

2. **Indentation Errors**:
   - Ensure all code blocks are properly indented (Python uses 4 spaces per indentation level).

3. **Missing Dependencies**:
   - Install missing dependencies using `pip install <package-name>`.

4. **Face Not Detected**:
   - Ensure the uploaded image has a clear, visible face.
   - Adjust lighting conditions when using the camera.

5. **Old Reports Not Updated After Renaming a User**:
   - Ensure the `update_username` function is correctly implemented to update both the `users.csv` and `user_tracking_report.csv` files.

---

## Contributing

We welcome contributions to improve this project! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.