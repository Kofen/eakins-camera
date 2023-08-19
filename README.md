# Eakins Camera

## EAKINS C212 Auto Focus Camera

This project builds upon the fantastic work of charliex:
- Blog Post: [Eakins Camera Hackery Pokery and the Legend of Measuretwice](https://charliex2.wordpress.com/2020/01/14/eakins-camera-hackery-pokery-and-the-legend-of-measuretwice/)
- GitHub Repository: [charlie-x/eakins-camera](https://github.com/charlie-x/eakins-camera)

The updated version of the camera is no longer as easy to access as before. My camera lacks an SD card slot but instead has two USB ports. It is identified by the model number C212. U-Boot and Linux have been updated, but the debug port remains with the same pinout. However, the camera now requires a root password.

## Internal Serial Port

[]- RX
 0- TX
 0- GND

The serial setup is 3.3V 115200, 8N1.

I soldered a 1.27mm pin-header for easy connection and removal of the debug cable, as I don't plan to have a permanent cable attached.

## Getting U-Boot Access and Root Access

Since the camera now requires a root password and keyboard input is disabled in U-Boot, we must try to boot into single-user mode. This can be accomplished by setting the bootargs in U-Boot. However, the first obstacle arises here: they have disabled all keyboard input in U-Boot, making it impossible to interrupt the boot and change the environment variables.

The only way to get in now is to try to interrupt the boot in hardware. The theory is that if we can interrupt the flash reading, if it can't find a valid image and drops us to the U-Boot shell.

**NB! Be very careful**, if you fry the flash, you have no recovery unless you clone a flash (I plan to dump the flash content, but I have no idea when I get the time).

Before powering the camera, short pin TBD TBD with a screwdriver and power up the camera. U-Boot now complains that there's no valid image, dropping us to the U-Boot shell. **Remove the short/screwdriver**.

1. Type `printenv`.
2. Copy the line after `bootargs =`.
3. Set the bootargs: `setenv bootargs <copied line> single`.
4. Type `boot`. The camera should boot into single-user mode.
5. Change the root password with `passwd`. I set the password to blank.
6. Type `reboot`, and now you can log in with user root and your chosen password.

## Setting Up Network Access

The good news is that the camera now includes an R8152 USB network driver, making it easy to use a USB-Ethernet adapter. The shell script executed at boot is located at `/` and named `mm.sh`.

1. Open `mm.sh`, comment out the `ifconfig` line for `eth0`.
2. Copy the line and paste it at the end of the script. Change the interface to `eth1` and your IP of choice.
3. Save and close the file.

Connect your USB Ethernet dongle. You should see a message from the kernel module that it loaded the R8152 module (if not, your adapter might not be compatible with the driver, try another one). Leave the dongle connected and reboot the camera.

After reboot, you should be able to telnet into it with `telnet <your ip>`.

## Copying Files and Setting Up the Server

You can use `netcat` to copy files to the camera. I've placed all my files in `/`.

To use netcat to receive a file on the camera:

On the receiver side:
1. Listen for a file: `nc -l -p 1234 > server`.

On the sender side:
1. Send the file: `nc -w 3 192.168.1.10 1234 < server`.

Copy the compiled `server` binary from the `bin` folder. If you're feeling brave, copy over my modified `mm.sh` from the `scripts` folder. I strongly recommend taking a copy of the camera's `mm.sh` and comparing my modified version with yours in case your camera runs a different firmware. Make the `server` app executable on the camera: `chmod +x server`.

You can test the app by running it directly: `./server <args>`. If no arguments are given, the server listens on port 1234. With `-d` args, it prints all received data and sends it back to the client.

If you want to start the server at boot and you copied over the `mm.sh` file:
- Change the port to listen on or remove the -p arg, leaving it on the default 1234.
- Change the IP in `eth1` to your IP of choice.

After a reboot, the Qt app is disabled, and the camera listens on your chosen port. In the `python` folder, there are Python scripts that send commands to the camera as a starter. There's no problem with letting the Qt app run if you like, but it's not responsive while the server runs, and the Qt GUI will get out of sync if you send commands to the camera via the server. I commented out the Qt app in `mm.sh` to prevent it from running.

## `server.c` and Python Script

My original idea was to build further on Charlie's work, but after cross-compiling `talk.c` to run on this camera, I discovered that while some commands are the same, many have changed, and the data bytes have new placements (the Qt app now sends a whopping 584 bytes to the camera app).

By using an arm7v compiled `strace` binary, we can recreate Charlie's setup to find out what's changed. Check the `monitor.sh` script in the `scripts` folder for more.

At this point, I figured it might be better to have a generic server application that just resends whatever it receives on a TCP socket to the UNIX domain socket. This has the benefit of adding or changing command structures without cross-compiling the camera app each time (until they upgrade the Linux version to something too new). Hopefully, this makes it a bit more robust in case things change in the future and much easier for users to add commands if they don't have a cross-compiling environment set up.

With the script in place, I documented all the commands and added them in JSON structure, along with some explanations in `eakins_control.py`. I started the structure before fully realizing all the ways the camera receives data, but hopefully, it is readable.

In the `json` file `commands.json`, we have the camera and commands. The camera structure sets the default IP and port to send to unless arguments are given. You can change these to your chosen ones if you wish. In the command structure, we have all the commands I bothered to figure out. In the Python script `eakins_control.py`, we open the JSON file, set the camera IP and port, build the arguments based on the commands in the JSON file, execute any commands given, and pack them in a signed little-endian format to send to the camera.
Example `python eakins_control.py --bw` sets the camera to B/W mode. All args can be printed with `-h`

There are many improvements to do here, and there's also a very crude focus-stacking script to experiment with.

The focus stacking script uses part of functions written by Mohit Nalavadi.  
- GitHub Repository:[momonala/focus-stack](https://github.com/momonala/focus-stack)


