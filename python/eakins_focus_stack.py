import argparse
import socket
import struct
import cv2
import numpy as np
import time

def send_command(server, port, command_address, data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server, port))
        message = bytearray(32)
        message[0] = command_address
        message[16:16+len(data)] = data
        s.sendall(message)
        if False: #When the eakins server is not in debug, we do not get anything back, set to False
            response = s.recv(32) 
        else:
            response = bytearray(1)
        return response

def set_focus(server, port, focus_value):
    focus_address = 0x2C
    focus_offset = int(focus_value + 175)  # Offset, zero focus value in the Qt app is 0xaf = 175
    # Pack focus value as a little-endian signed 32-bit integer
    focus_data = struct.pack('<i', focus_offset)
    response = send_command(server, port, focus_address, focus_data)
    return response

#Get a frame frome the video capture card
def capture_snapshot():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Unable to open camera")
        return

    ret, frame = cap.read()  
    cap.release()  

    return frame

def align_images(frames):
    reference_frame = frames[len(frames) // 2]  # Choose a reference frame (e.g., the middle frame)
    reference_frame = frames[-1]  # Choose a reference frame (e.g., the middle frame)
    
    aligned_frames = [reference_frame]

    for frame in frames:
        warp_mode = cv2.MOTION_EUCLIDEAN
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 1000, 1e-5)
        warp_matrix = np.eye(2, 3, dtype=np.float32)

        (cc, warp_matrix) = cv2.findTransformECC(cv2.cvtColor(reference_frame, cv2.COLOR_BGR2GRAY),
                                                 cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                                                 warp_matrix, warp_mode, criteria)
        aligned_frame = cv2.warpAffine(frame, warp_matrix, (frame.shape[1], frame.shape[0]),
                                       flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
        aligned_frames.append(aligned_frame)

    return aligned_frames

def compute_laplacian(images):
    """Gaussian blur and compute the gradient map of the image. This is proxy for finding the focus regions.
    """
    gbkl = 3
    lks = 9
    laplacians = []
    for image in images:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(
            gray,
            (gbkl, gbkl),
            0,
        )
        laplacian_gradient = cv2.Laplacian(
            blurred, cv2.CV_64F, ksize=lks
        )
        laplacians.append(laplacian_gradient)
    laplacians = np.asarray(laplacians)
    return laplacians

def focus_regions(images, laplacian_gradient):
    """Take the absolute value of the Laplacian (2nd order gradient) of the Gaussian blur result.
    This will quantify the strength of the edges with respect to the size and strength of the kernel (focus regions).

    Then create a blank image, loop through each pixel and find the strongest edge in the LoG
    (i.e. the highest value in the image stack) and take the RGB value for that
    pixel from the corresponding image.

    Then for each pixel [x,y] in the output image, copy the pixel [x,y] from
    the input image which has the largest gradient [x,y]
    """
    output = np.zeros(shape=images[0].shape, dtype=images[0].dtype)
    abs_laplacian = np.absolute(laplacian_gradient)
    maxima = abs_laplacian.max(axis=0)
    bool_mask = np.array(abs_laplacian == maxima)
    threshold = maxima * 1
    for i, img in enumerate(images):
        mask = (abs_laplacian[i] >= threshold).astype(np.uint8)
        output = cv2.bitwise_not(img, output, mask=mask)

    return 255 - output

def main():
    parser = argparse.ArgumentParser(description="Camera control client")
    parser.add_argument("--server", default="192.168.1.10", help="Server address")
    parser.add_argument("--port", type=int, default=1234, help="Port number")
    parser.add_argument("--focus_range", type=int, default=200, help="Focus value range")
    parser.add_argument("--focus_steps", type=int, default=10, help="Number of focus steps")

    args = parser.parse_args()

    #focus_values = np.arange(-args.focus_range, args.focus_range, args.focus_steps)
    focus_values = np.arange(178, 200, args.focus_steps)
    captured_frames = []

    for focus_value in focus_values:
        if -200 <= focus_value <= 200:
            response = set_focus(args.server, args.port, focus_value)
            print(f"Focus: {focus_value}, Response: {response.hex()}")
            time.sleep(0.5)
            snapshot = capture_snapshot()
            captured_frames.append(snapshot)
        else:
            print(f"Invalid focus value: {focus_value}")

    aligned_frames = align_images(captured_frames)
    laplacian_gradient = compute_laplacian(aligned_frames)
    focus_aligned = focus_regions(aligned_frames, laplacian_gradient)
    focus_stacked = np.hstack((focus_aligned, aligned_frames[1]))
    cv2.imshow("Focus Stacked Image", focus_stacked)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
