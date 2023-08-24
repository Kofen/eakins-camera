import pkg_resources
import argparse
import socket
import json
import os

json_path = pkg_resources.resource_filename(__name__, 'commands.json')
with open(json_path, "r") as json_file:
    data = json.load(json_file)

if os.path.exists('/etc/camera.json'):
    with open('/etc/camera.json', "r") as json_file:
        data["camera"] = json.load(json_file)["camera"]

def send_command(server, port, command_address, data=None, data_start=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server, port))
        if data is not None:
            data = data.to_bytes(12, byteorder='little', signed=True)
            message = bytearray(data_start+len(data))
            message[data_start:data_start+len(data)] = data
        else:
            message = bytearray(32)
        message[0] = int(command_address,16)
        s.sendall(message)
        if False: #Debug print, if the server app is not in debug we do not get any response, set to False during normal operation 
            response = s.recv(len(message))
            response_hex = ' '.join(format(byte, '02x') for byte in response) 
            print("Response:", response_hex)

def main():
    parser = argparse.ArgumentParser(description="Camera control client")
    parser.add_argument("--server", default=data["camera"]["ip"], help="Server address")
    parser.add_argument("--port", type=int, default=data["camera"]["port"], help="Port number")
    
    # A bit of a hack were done on the args type, even if we only give integers in the argument, we add them as strings.
    # This was done in order to be able to send a value of 0 as the if getattr will take a 0 int as False and not run the command.
    for command, details in data["commands"].items():
        if details.get("type") == "str":
            if details.get("nargs"):    
                parser.add_argument(f"--{command}", type=str, metavar=tuple(details.get("metavar").split(' ')), nargs=details.get("nargs"), help=details.get("help_text", ""))
            else:
                parser.add_argument(f"--{command}", type=str, help=details.get("help_text", ""))
        else:
            parser.add_argument(f"--{command}", action="store_true", help=details.get("help_text", ""))
    
    args = parser.parse_args()

    # Access the parsed command arguments and execute corresponding actions
    for command, details in data["commands"].items():
        if getattr(args, command):
            print(f"Executing {command} command")
            if details.get("type") == "str":
                if command == "roi":
                    #Correctly space the X and Y value
                    x,y = (getattr(args,command))
                    print(f"X {x}\nY {y}")
                    value = (int(y) << 64) | int(x)    
                elif command == "rgb":
                    #Correctly space the R,G,B value
                    r,g,b = (getattr(args,command))
                    print(f"Red {r}\nGreen {g}\nBlue {b}")
                    value = (int(b) << 64) | (int(g) << 32) | int(r)
                else:
                    print(f"Value: {getattr(args,command)}")
                    value = int(getattr(args, command))+details.get("offset",0)
                send_command(args.server, args.port, details["address"], value, details["start_byte"]) 
            elif details.get("data"):
                send_command(args.server, args.port, details["address"], details["data"], details["start_byte"])
            else:
                send_command(args.server, args.port, details["address"])

if __name__ == "__main__":
    main()


"""
ROI: 
_____________________   
|         14        |
|                   |
|                   |
|0                16| 
|                   |
|                   |
|         0         |
---------------------
X startbyte == 64. Y startbyte == 72
Center of the screen is (x,y) = (7,6)
HDR: 0 to 255
BRIGHTNESS: 0 to 100
EXPOSURE: 0 to 333 (One would think this should be 0-335, todo, test)
GAIN: 0 to 50 
RGB:
R: 0 to 4095 
G: 0 to 4095
B: 0 to 4095
About rgb, all of them are sent in one package, the address is 0x0F and then each color has it space, R32+33, G36+37, B40+41
This means we can't just set a single value without sending them all. 
SAT: 0-255
CONT: 0-100
SHARP: 0-15
ZOOM: 1-50
FOCUS: The focus range in the Qt app is -200 to 200. This is offset so that 0 focus value is 175 sent to the camera app. 
"""
