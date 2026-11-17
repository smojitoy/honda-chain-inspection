# SSH Access to the NVIDIA Jetson

This guide explains how team members can connect to the **Honda Chain Inspection Project's NVIDIA Jetson** from their own computers using a terminal or **VS Code Remote - SSH**.

> **Before connecting:** The Jetson must be powered on, have Linux/JetPack installed and initial user setup completed, and be reachable on the network. Replace every placeholder (such as `<JETSON_USERNAME>` and `<JETSON_IP>`) with your team's actual settings. **Do not commit passwords or private SSH keys to GitHub.**

## 1. Set up SSH on the Jetson (one-time setup)

These steps are performed **on the Jetson itself**, using its local terminal (monitor + keyboard, or another existing console connection).

### 1.1 Check or install the SSH server

```bash
sudo systemctl status ssh
```

If the SSH server is not installed, install it:

```bash
sudo apt update
sudo apt install -y openssh-server
```

Start SSH now and enable it on startup:

```bash
sudo systemctl enable --now ssh
sudo systemctl status ssh
```

The service should show **active (running)**. Press `q` to exit the status view.

### 1.2 Find the Jetson username and IP address

```bash
whoami
hostname -I
```

- `whoami` shows the Linux username created during Jetson setup.
- `hostname -I` shows the Jetson's network IP address(es). Choose the address reachable from your computer (for example, `192.168.1.50`). The example IP is **not** the team's actual address.
- The Jetson and your computer must be on the same reachable network, or connected through an approved VPN/network route. Some campus or guest Wi-Fi networks prevent devices from reaching one another.

Record these two values somewhere accessible to team members:

```text
JETSON_USERNAME=<JETSON_USERNAME>
JETSON_IP=<JETSON_IP>
```

## 2. Connect from a Mac using Terminal

On your **Mac**, open **Terminal** (not the Jetson terminal) and run:

```bash
ssh <JETSON_USERNAME>@<JETSON_IP>
```

For example (illustrative values only):

```bash
ssh jetsonuser@192.168.1.50
```

On first connection, SSH may ask whether you trust the host's fingerprint. **Verify the fingerprint with the person who set up the Jetson** before typing `yes`.

When prompted, enter the password for the **Jetson's Linux account**, not your Mac password. The cursor will not move while you type; this is normal.

To verify that you are connected to the Jetson:

```bash
hostname
whoami
pwd
```

To end the SSH session:

```bash
exit
```

> Windows/Linux users can use the same `ssh <JETSON_USERNAME>@<JETSON_IP>` command in a terminal with OpenSSH installed (such as Windows PowerShell or a Linux terminal).

## 3. Connect from VS Code (recommended for development)

1. Install **Visual Studio Code** on your computer.
2. In VS Code, open **Extensions** (`Cmd + Shift + X` on macOS) and install Microsoft's **Remote - SSH** extension.
3. Open the **Command Palette** (`Cmd + Shift + P` on macOS).
4. Run **Remote-SSH: Connect to Host...**.
5. Enter:

   ```text
   <JETSON_USERNAME>@<JETSON_IP>
   ```

6. If prompted, select **Linux** as the remote operating system and authenticate with the Jetson account password (or your configured SSH key).
7. Wait for the remote connection to finish, then choose **File > Open Folder...** to open a directory **on the Jetson**.
8. Open **Terminal > New Terminal**. The new terminal should now run commands on the Jetson.

### Optional: Save the Jetson as an SSH host

On your **Mac**, edit `~/.ssh/config` (create it if it does not exist):

```sshconfig
Host honda-jetson
    HostName <JETSON_IP>
    User <JETSON_USERNAME>
    Port 22
```

Then connect from Terminal with:

```bash
ssh honda-jetson
```

Or select `honda-jetson` from **Remote-SSH: Connect to Host...** in VS Code.

**Note:** If you also use VS Code to connect to OSC or another server, you can keep those connections in separate VS Code windows. Opening the Jetson host does not require changing the existing OSC SSH configuration.

## 4. Troubleshooting

| Problem | What to check |
| --- | --- |
| `Connection timed out` / `No route to host` | Make sure the Jetson is on, the IP address is correct, and the two devices can reach each other over the network. |
| `Connection refused` | On the Jetson, run `sudo systemctl status ssh` and start it with `sudo systemctl enable --now ssh` if necessary. |
| `Permission denied` | Confirm the Jetson username and authentication method. The Jetson password may be different from your Mac or OSC password. |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | Stop and verify with the team whether the Jetson was reinstalled or its IP address was reassigned. Do not blindly remove the known-host entry. |
| VS Code hangs or cannot connect | Test `ssh <JETSON_USERNAME>@<JETSON_IP>` in your Mac Terminal first. In VS Code, check **View > Output > Remote - SSH** for the error. |

If a firewall is enabled on the Jetson, check whether it permits SSH connections on TCP port 22. Do not expose SSH to the public internet just to make local team access work; use an approved secure network or VPN for remote access.

## 5. Team checklist

- [ ] Jetson operating system and Linux account are set up.
- [ ] SSH service is running on the Jetson.
- [ ] Team members know the Jetson's current reachable IP address and username.
- [ ] Each member can connect from a computer using `ssh <JETSON_USERNAME>@<JETSON_IP>`.
- [ ] VS Code Remote - SSH can open the project directory on the Jetson.
- [ ] No passwords or private keys have been committed to the repository.

## References

- [NVIDIA: Setting Up the Jetson Environment](https://docs.nvidia.com/learning/physical-ai/getting-started-with-isaac-sim/latest/leveraging-ros-2-and-hil-in-isaac-sim/03-setting-up-the-jetson-environment.html)
- [Visual Studio Code: Remote Development using SSH](https://code.visualstudio.com/docs/remote/ssh)
- [VS Code: Remote SSH Troubleshooting](https://code.visualstudio.com/docs/remote/troubleshooting)
