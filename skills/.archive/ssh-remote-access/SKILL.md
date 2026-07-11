---
name: ssh-remote-access
category: devops
description: "Setting up SSH remote access on Ubuntu — enable SSH server, configure password/key auth, troubleshoot connection issues from Android/mobile clients."
tags: [ssh, remote-access, ubuntu, termux, android, linux]
---

# SSH Remote Access

Set up SSH on Ubuntu for remote access from mobile devices (Termux on Android, JuiceSSH, etc.).

## When to Use

- User wants to SSH into their Ubuntu machine from phone/tablet
- User installing Termux or other SSH clients
- SSH connection refused or closed immediately
- Host key verification issues

## Prerequisites

- Ubuntu with sudo access
- SSH server package (openssh-server)
- Mobile client (Termux, JuiceSSH, Termius, ConnectBot)

## Installation Steps

### 1. Enable and Start SSH Server

```bash
sudo systemctl enable ssh --now
sudo systemctl status ssh
```

### 2. Get the IP Address

```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

Look for the `192.168.x.x` or `10.x.x.x` address on your main network interface (not docker bridges).

### 3. Check Firewall

```bash
sudo ufw status
```

If active, allow SSH: `sudo ufw allow ssh`

## Common Pitfalls

### Host Key Verification Failed

```text
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

User must type `yes` (the full word), then Enter. This is a one-time confirmation — after this, the host key is stored in `~/.ssh/known_hosts` and won't prompt again.

### Connection Closed Immediately

```text
Connection closed by 192.168.x.x port 22
```

**Most likely cause: `KbdInteractiveAuthentication no` in sshd_config.**

Modern Ubuntu defaults to `KbdInteractiveAuthentication` for password-based login instead of the traditional `PasswordAuthentication`.

Fix:

```bash
# Edit sshd_config
sudo sed -i 's/^KbdInteractiveAuthentication no/KbdInteractiveAuthentication yes/' /etc/ssh/sshd_config

# Or edit manually:
# sudo nano /etc/ssh/sshd_config
# Change: KbdInteractiveAuthentication no → yes

sudo systemctl restart ssh
```

Also verify `PasswordAuthentication` is not set to `no`:
```bash
grep PasswordAuthentication /etc/ssh/sshd_config
```
If it's commented out (`#PasswordAuthentication yes`), that's fine — the default is yes.

### Permission Denied

```text
Permission denied (publickey,password).
```

Possible causes:
- Wrong password
- Both password and key auth disabled
- Wrong username

Check auth methods allowed:
```bash
sudo grep -E "PasswordAuthentication|KbdInteractiveAuthentication|ChallengeResponseAuthentication" /etc/ssh/sshd_config
```

### Network Connectivity

If SSH times out or can't connect:
1. Check if phone and computer are on **the same WiFi network**
2. Verify computer's IP hasn't changed (`ip addr show`)
3. Test with ping from the client: `ping 192.168.x.x`
4. Check if router has client isolation enabled (guest networks often block device-to-device)

## Client Configuration

### Termux (Android — Recommended)

```bash
# In Termux:
pkg update
pkg install openssh -y

# Connect:
ssh username@192.168.x.x
# On first connection: type "yes" then password
```

**Note:** Password input is invisible (no `****` shown). Type the password and press Enter — this is normal terminal behavior.

### JuiceSSH (Android)

- New connection → enter IP, username, password
- Saves sessions for quick reconnect

### Termius (Android/iOS)

- Cross-platform, UI-friendly
- Free tier supports basic SSH

## Security Notes

- Password auth is convenient for LAN but consider SSH keys for WAN access
- For external access: set up port forwarding on router, use a strong password, and consider fail2ban
- Avoid exposing SSH on default port 22 to the internet without additional protection

## Verification

After fixing, test locally first:
```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 username@127.0.0.1 "echo SSH_OK"
```
