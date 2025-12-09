# Sample Malicious Logs for Testing

These sample logs contain various attack patterns designed to trigger Sigma rules.

## Files

### 1. `nginx_malicious.log` 
**Attacks Included:**
- ✅ SQL Injection (`sqlmap`, `UNION SELECT`, `OR '1'='1`)
- ✅ XSS (Cross-Site Scripting) (`<script>alert`)
- ✅ Directory Traversal (`../../etc/passwd`, `../windows/system32`)
- ✅ Command Injection (`?cmd=whoami`, `?cmd=ls`)
- ✅ Web Shell Upload (`shell.php`)
- ✅ Open Redirect (`redirect=http://evil.com`)
- ✅ Remote File Inclusion (`file=http://attacker.com`)
- ✅ XXE (XML External Entity) (`<!ENTITY xxe`)
- ✅ Automated Tool Detection (`sqlmap`, `Nikto`, `Havij`, `hydra`, `Burp Suite`)
- ✅ Brute Force Login (multiple 401 responses)

### 2. `linux_malicious.log`
**Attacks Included:**
- ✅ SSH Brute Force (multiple failed root login attempts)
- ✅ Privilege Escalation (`sudo` to root)
- ✅ Reverse Shell (`nc -e /bin/bash`)
- ✅ Suspicious Cron Job (`/tmp/evil.sh`)
- ✅ Port Scanning (UFW BLOCK on unusual ports)
- ✅ Service Crashes (nginx killed, out of memory)
- ✅ Suspicious System Calls (audit logs)
- ✅ Suspicious Service Installation

### 3. `windows_malicious.json`
**Attacks Included:**
- ✅ Failed Login Attempts (EventID 4625 - Brute Force)
- ✅ User Account Creation (`net user hacker`)
- ✅ Malicious Service Installation (EventID 4697, 7045)
- ✅ Privilege Escalation (SeDebugPrivilege)
- ✅ Registry Persistence (`HKLM\\...\\Run`)
- ✅ Admin Share Access (`C$`)
- ✅ PowerShell Encoded Command (Base64 obfuscation)
- ✅ Mimikatz Execution (credential dumping)
- ✅ Suspicious Process Creation (EventID 4688)

## Usage

### Upload via Web UI:
1. Start the server: `uvicorn src.app.server:app --host 0.0.0.0 --port 8000`
2. Go to: `http://localhost:8000`
3. Click "Upload Log File" button
4. Select one of the sample files
5. Watch alerts generate in real-time! 🔥

### Expected Results:
- **Nginx**: ~10-15 alerts (SQL injection, XSS, directory traversal, etc.)
- **Linux**: ~8-12 alerts (brute force, privilege escalation, reverse shell, etc.)
- **Windows**: ~10-15 alerts (account creation, service installation, mimikatz, etc.)

## Demo Script for Judges

**"Let me demonstrate our real-time threat detection system..."**

1. **Show Dashboard** - "Here's our live security dashboard"
2. **Click Upload** - "We can ingest logs from any source"
3. **Select `nginx_malicious.log`** - "This contains real attack patterns"
4. **Watch Progress** - "Processing... analyzing with Sigma rules..."
5. **Show Results** - "✅ 15 logs processed, 🚨 12 critical alerts detected!"
6. **Click Alert Details** - "SQL injection detected, XSS attempt blocked..."
7. **Show Network Graph** - "Visual representation of attack sources"

🎯 **Key Points:**
- Instant detection using industry-standard Sigma rules
- Automated threat classification (critical/high/medium/low)
- Real-time dashboard updates
- Multi-platform support (Windows, Linux, Nginx, Zeek)
