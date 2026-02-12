# Example Queries for Linux MCP Server Chatbot

This document contains example queries you can try with the chatbot, organized by category.

## 🔍 System Information

### Basic System Info
```
What system am I running?
Show me basic system information
What's the hostname and OS version?
How long has the system been running?
```

### CPU and Performance
```
What's the current CPU usage?
Show me CPU information and current load
Which processes are using the most CPU?
Is the CPU overloaded?
```

### Memory Status
```
How much memory is being used?
Show me RAM and swap usage
Is the system running low on memory?
What's consuming the most memory?
```

## 💾 Disk and Storage

### Disk Usage
```
Show disk space usage
Which filesystems are almost full?
How much free space is left on /?
Show me all mounted filesystems
```

### Finding Large Files/Directories
```
What's using the most disk space in /var?
Show me the largest directories in /home
List the top 10 largest directories on the system
Which log files are taking up space?
```

## 🔧 Services and Processes

### Service Status
```
List all running services
Which services are failed or failing?
Show me the status of sshd
Is the firewall running?
Show me all active systemd services
```

### Service Logs
```
Show me the last 50 lines of sshd logs
What errors are in the systemd journal from the last hour?
Show me logs for the nginx service
Are there any critical errors in the system logs?
```

### Process Management
```
List all running processes
Show me processes owned by user apache
Which process is listening on port 80?
What's process 1234 doing?
```

## 🌐 Network Diagnostics

### Network Interfaces
```
Show me all network interfaces
What's the IP address of this system?
List network interfaces and their status
Is the bond0 interface up?
Are there any network interface errors?
```

### Network Connections
```
Show active network connections
What ports are listening?
Show me established connections
Is anyone connected to port 22?
List all TCP connections
```

### Network Troubleshooting
```
Why is the network slow?
Are there packet drops on any interface?
Show me network interface statistics
Is the DNS server reachable?
```

## 📋 Logs and Debugging

### System Logs
```
Show me kernel errors from the last hour
What's in the audit logs?
Show me systemd journal entries for today
Are there any critical errors in dmesg?
Read /var/log/messages
```

### Application Logs
```
Show me the Apache error log
What's in /var/log/nginx/error.log?
Show me the last 100 lines of /var/log/secure
Are there authentication failures in the logs?
```

## 🖥️ Hardware Information

### Hardware Details
```
Show me hardware information
What CPU architecture is this?
List PCI devices
Show USB devices connected
What block devices are available?
```

### Storage Devices
```
List all block devices
Show me disk I/O statistics
What RAID devices are configured?
Show me partition information
```

## 🔐 Security and Auditing

### Security Checks
```
Show me failed login attempts
Are there any security violations in the audit logs?
Show me recent sudo commands
List users who have logged in today
```

### File System Checks
```
List files in /etc/ssh
Show me the contents of /etc/hosts
What files are in /var/crash?
Show me systemd unit files in /etc/systemd/system
```

## 🌍 Remote Host Queries

For remote hosts, just mention the hostname in your query:

### Single Host
```
Check the health of demo.example.local
What's the disk usage on prod-server.example.com?
Show me running services on web01.internal
Is nginx running on api-server.local?
```

### Comparative Analysis
```
Compare disk usage between web01 and web02
Check if both db-primary and db-replica are running MySQL
Show me CPU usage on all application servers
```

## 🚨 Troubleshooting Scenarios

### Performance Issues
```
The application is slow, what's wrong?
Why is the system running out of memory?
Which process is causing high CPU usage?
Is the disk I/O bottleneck?
```

### Service Problems
```
Why won't Apache start?
The database is down, what happened?
Why is SSH not responding?
What's causing the firewall to block traffic?
```

### Network Issues
```
Why can't I connect to port 80?
The network is slow, what's the problem?
Are there any interface errors?
Why is the bonding interface failing?
```

### Disk Problems
```
The system is running out of space, what can I delete?
Where is all the disk space going?
Can I remove old log files?
What's filling up /var?
```

## 🔬 Multi-Step Diagnostics

The chatbot can perform multi-step analysis:

### Complete Health Check
```
Check the overall health of demo.example.local
Perform a complete system diagnostic
Is everything running normally on this server?
```

The chatbot will automatically:
1. Get system information
2. Check CPU usage
3. Check memory usage
4. Check disk space
5. List services
6. Check for errors in logs
7. Provide a summary

### Root Cause Analysis
```
The web server is responding slowly, investigate the cause
Database queries are timing out, what's the problem?
Users can't log in, help me troubleshoot
```

The chatbot will:
1. Check the relevant service status
2. Look at resource usage (CPU, memory, disk)
3. Review logs for errors
4. Identify the root cause
5. Suggest fixes

### Proactive Monitoring
```
Are there any potential issues I should know about?
What maintenance is needed on this server?
Check for common problems
```

## 💡 Tips for Effective Queries

1. **Be specific about the host**: For remote hosts, always mention the hostname
   ```
   Good: "Check disk space on web-server.local"
   Bad: "Check disk space" (will check local system)
   ```

2. **Ask follow-up questions**: The chatbot maintains conversation context
   ```
   You: "Show me failed services"
   Bot: [Shows results]
   You: "Show me the logs for the first one"
   ```

3. **Combine multiple checks**: Ask compound questions
   ```
   "Check CPU, memory, and disk usage on prod-db.local"
   "Show me running services and their logs on web01"
   ```

4. **Use natural language**: Don't worry about exact syntax
   ```
   "What's eating up all the RAM?"
   "Why is my disk full?"
   "Is anything broken?"
   ```

5. **Ask for explanations**: The chatbot can explain what it finds
   ```
   "Why is process 1234 using so much CPU?"
   "Explain what's causing the memory pressure"
   "What does this error in the logs mean?"
   ```

## 🎯 Advanced Queries

### Pattern Matching
```
Show me all services with "web" in the name
List files in /etc that were modified today
Find processes running as user www-data
```

### Trending and History
```
Show me system load over the last hour
Has memory usage been increasing?
When did the last reboot happen?
```

### Configuration Review
```
What's the current network configuration?
Show me firewall rules
What's in the SSH configuration?
List all systemd timer units
```

Enjoy exploring your Linux systems with natural language! 🚀
