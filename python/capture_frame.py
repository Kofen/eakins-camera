import cv2
import os
import argparse
from datetime import datetime

def capture_frame(device_id, output_path):
    # Open video capture device
    cap = cv2.VideoCapture(device_id)

    if not cap.isOpened():
        print("Error: Could not open video capture device.")
        return

    # Capture a frame
    ret, frame = cap.read()

    # Release the video capture device
    cap.release()

    if not ret:
        print("Error: Failed to capture frame.")
        return

    # Save the frame as a PNG file
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}.png"
    if output_path:
        filename = os.path.join(output_path, filename)

    cv2.imwrite(filename, frame)
    print(f"Frame captured and saved as {filename}")

def main():
    parser = argparse.ArgumentParser(description="Capture a frame from a video capture card.")
    parser.add_argument("-f", "--output_folder", type=str, default="", help="Path to the output folder for saving the PNG file.")
    parser.add_argument("-c", "--capture_device", type=int, default=0, help="Capture device ID (e.g., 0, 1, 2, ...)")
    args = parser.parse_args()

    if args.output_folder and not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    capture_frame(args.capture_device, args.output_folder)

if __name__ == "__main__":
    main()

