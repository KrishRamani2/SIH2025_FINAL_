# Trishul – Next-Gen SIEM & Security Dashboard

Trishul is a premium, high-performance Security Information and Event Management (SIEM) dashboard designed for modern security operations centers (SOCs). It provides real-time visibility into system logs, network threats, and security alerts through a stunning, highly interactive interface.

## 🚀 Key Features

### 1. **Unified Security Dashboard**
*   **Real-Time Monitoring**: Visualize threat levels, total logs, and active devices instantly.
*   **Event Velocity Graph**: A dynamic, live-updating graph showing the velocity of incoming network events.
*   **Interactive Widgets**: Draggable and customizable widgets for personalized monitoring.
*   **Visual Analytics**:
    *   **Threat Attack Map**: Visual representation of MITRE ATT&CK tactics.
    *   **Alert Distribution**: Breakdown of alerts by severity.
    *   **Log Source Analysis**: Distribution of logs across different sources (Linux, Windows, etc.).

### 2. **Advanced Log Management**
*   **Multi-Source Ingestion**: Seamlessly collect and parse logs from **Linux** (Syslog) and **Windows** (Event Logs) systems.
*   **OCFS Export**: Download system logs in **Open Cyber Security Framework (OCFS)** format, tailored for both Linux and Windows environments.
*   **Live Log Streaming**: Watch logs arrive in real-time with powerful search and filtering capabilities.

### 3. **Intelligent Alert System**
*   **Severity Mapping**: Alerts are automatically categorized into **Critical**, **Warning**, and **Info** levels for prioritized response.
*   **Encrypted Reporting**:
    *   **Client-Side Encryption**: Securely export alert reports as encrypted `.bin` files.
    *   **Decrypt Report**: A dedicated, secure interface to decrypt and view sensitive alert reports using a unique key.

### 4. **Sigma Rule Engine**
*   **Integrated Editor**: A full-featured code editor for managing Sigma rules.
*   **Tree View Navigation**: Easily browse and organize rules by category and folder.
*   **Rule Management**: Create, edit, and save Sigma rules directly within the dashboard.
*   **Validation**: Built-in YAML validation ensures rule integrity.

### 5. **TTP Intelligence (Tactics, Techniques, & Procedures)**
*   **TTP Editor**: Manage and refine TTP documentation and logic.
*   **TTP Logs**: View and analyze logs specifically related to known adversary tactics.
*   **File Detection**: Automatic detection and listing of intelligence files within the `TTP_Intelligence` directory.

### 6. **Network & Device Discovery**
*   **Device Scanning**: Automatically discover and list devices on the network.
*   **Status Monitoring**: Track the online/offline status of connected assets.
*   **Network Logs**: Dedicated view for analyzing network-specific traffic and events.

### 7. **Extensible Plugin System**
*   **Dynamic Loading**: Upload and integrate custom plugins (`.html`, `.py`) on the fly.
*   **Modular Architecture**: Extend the dashboard's functionality without altering the core codebase.

### 8. **Enterprise-Grade Security**
*   **Role-Based Access Control (RBAC)**:
    *   **Admin**: Full access to all features.
    *   **NodeAdmin**: Restricted access (Read-only Sigma, no decryption/plugins).
*   **Secure Authentication**: Custom login portal with configurable sender ports.
*   **Session Locking**: One-click session lock for immediate privacy.

---

## 🛠️ Technology Stack

*   **Backend**: Python 3.x, FastAPI, Uvicorn, SQLite
*   **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS
*   **Visualization**: Chart.js, Three.js, Vis.js
*   **Packaging**: PyInstaller (for standalone executable creation)

---

## 📦 Installation & Setup

### Prerequisites
*   Python 3.8+
*   Node.js (optional, for development tools)

### Quick Start

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-repo/trishul-siem.git
    cd trishul-siem
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Server**
    ```bash
    python main.py
    ```
    *   The server will start on `http://0.0.0.0:8000` (or the configured port).

4.  **Access the Dashboard**
    *   Open your browser and navigate to `http://localhost:8000`.
    *   Login with your credentials.

---

## 📂 Project Structure

```
├── src/
│   ├── app/                # Frontend application (HTML, JS, CSS)
│   │   ├── assets/         # Static assets
│   │   ├── routes/         # Backend API routes
│   │   └── index.html      # Main dashboard entry point
│   └── ...
├── Sigma_Rules/            # Directory for Sigma detection rules
├── TTP_Intelligence/       # Directory for TTP intelligence files
├── collected_logs/         # Storage for ingested logs (SQLite DB)
├── main.py                 # Application entry point
└── requirements.txt        # Python dependencies
```

---

## 🛡️ Usage Guide

### Decrypting Reports
1.  Navigate to the **Decrypt Report** section.
2.  Upload the encrypted `.bin` file you received.
3.  Enter the unique **Decryption Key**.
4.  The system will decrypt and display the sensitive alert data in a secure table.

### Managing Sigma Rules
1.  Go to the **Sigma Rule Editor**.
2.  Use the file tree on the left to navigate folders.
3.  Click a rule to edit it, or use the "+" button to create a new rule.
4.  Save your changes to update the detection logic.

### Exporting Logs
1.  Navigate to **System Logs**.
2.  Filter by **Linux** or **Windows**.
3.  Click the **Download OCFS** button to get a standardized log export.

---


