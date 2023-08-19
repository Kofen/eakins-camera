#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/un.h>
#include <signal.h>

#define DEFAULT_PORT 1234
#define UNIX_SOCKET_PATH "/tmp/UNIX.domain"
#define LED_PATH "/sys/class/gpio/gpio89/"
#define BLINK_RATE 30E-3 //In seconds

volatile int KeepOnRunning = 1;  // Global flag to indicate if the server should keep running

// Declare a global file pointer for the LED
FILE *led_file;

void print_debug_data(const char *data, ssize_t size) {
    printf("Received data (%zd bytes): ", size);
    for (ssize_t i = 0; i < size; i++) {
        printf("%02x ", data[i]);
    }
    printf("\n");
}

void initialize_led() {
    led_file = fopen(LED_PATH "value", "w");
    if (led_file == NULL) {
        perror("Failed to open LED value file");
        exit(EXIT_FAILURE);
    }
}

void set_led_value(int value) {
    fprintf(led_file, "%d", value);
    fflush(led_file); // Flush the buffer to ensure immediate update
}

void flash_led(int num) {
    for (int i = 0; i < num; i++) {
        set_led_value(0);
        usleep(BLINK_RATE); 
        set_led_value(1);
        usleep(BLINK_RATE); 
    }
}

void sig_handler(int sig) {
    KeepOnRunning = 0;  // Set the flag to stop the server
}

static void setup_sighandlers(void) {
    for (int i = 0; i < 64; i++) {
        struct sigaction sa;
        memset(&sa, 0, sizeof(sa));
        sa.sa_handler = sig_handler;
        sigaction(i, &sa, NULL);
    }
}

int main(int argc, char *argv[]) {
    setup_sighandlers(); // Setup signal interupts so we can close sockets and file to exit cleanly
    int port = DEFAULT_PORT;
    int debug = 0;
    initialize_led();
    set_led_value(1); // App is running, let's indicate that with the power led

    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-p") == 0) {
            if (i + 1 < argc) {
                port = atoi(argv[i + 1]);
                i++;  // Skip the next argument since it's the port number
            } else {
                fprintf(stderr, "Error: -p option requires a port number argument.\n");
                exit(EXIT_FAILURE);
            }
        } else if (strcmp(argv[i], "-d") == 0) {
            debug = 1;
        } else if (strcmp(argv[i], "-h") == 0) {
            printf("Usage: %s [-p <port>] [-d]\n", argv[0]);
            printf("Options:\n");
            printf("  -p <port>   Set the port number (default: %d)\n", DEFAULT_PORT);
            printf("  -d          Enable debug mode\n");
            printf("  -h          Display this help message\n");
            exit(EXIT_SUCCESS);
        }
    }

    // Create a TCP socket
    int tcp_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (tcp_socket == -1) {
        perror("TCP socket creation error");
        exit(EXIT_FAILURE);
    }

    // Prepare the TCP address structure
    struct sockaddr_in tcp_addr;
    tcp_addr.sin_family = AF_INET;
    tcp_addr.sin_addr.s_addr = INADDR_ANY;
    tcp_addr.sin_port = htons(port);

    // Bind the TCP socket to the address
    if (bind(tcp_socket, (struct sockaddr *)&tcp_addr, sizeof(tcp_addr)) == -1) {
        perror("TCP socket bind error");
        exit(EXIT_FAILURE);
    }

    // Listen for incoming TCP connections
    if (listen(tcp_socket, 5) == -1) {
        perror("TCP socket listen error");
        exit(EXIT_FAILURE);
    }

    printf("Server listening on port %d\n", port);

    while (KeepOnRunning) {
        // Create a Unix domain socket
        int unix_socket = socket(AF_UNIX, SOCK_STREAM, 0);
        if (unix_socket == -1) {
            perror("Unix socket creation error");
            exit(EXIT_FAILURE);
        }

        // Prepare the Unix domain address structure
        struct sockaddr_un unix_addr;
        unix_addr.sun_family = AF_UNIX;
        strcpy(unix_addr.sun_path, UNIX_SOCKET_PATH);

        // Connect to the Unix domain socket
        if (connect(unix_socket, (struct sockaddr *)&unix_addr, sizeof(unix_addr)) == -1) {
            perror("Unix socket connect error");
            exit(EXIT_FAILURE);
        }
        
        // Accept a TCP connection
        int tcp_client_socket = accept(tcp_socket, NULL, NULL);
        if (tcp_client_socket == -1) {
            perror("TCP socket accept error");
            continue;
        }

        // Read data from the TCP client and send it to the Unix domain socket, if debug, print the data and send it back to the client. 
        char buffer[1024];
        ssize_t bytes_read;
        while ((bytes_read = read(tcp_client_socket, buffer, sizeof(buffer))) > 0) {
            if (debug) {
                print_debug_data(buffer, bytes_read);
                write(tcp_client_socket, buffer, bytes_read);
            }
            write(unix_socket, buffer, bytes_read);
            flash_led(2);
        }
        // Close the sockets
        close(tcp_client_socket);
        close(unix_socket);
    }
    // Turn off the power led, indicating that the app is not running
    set_led_value(0);
    // Close the gpio file
    fclose(led_file);
    // Close the TCP socket
    close(tcp_socket);
    printf("\n\n\n\n\nItj fårra nålles!\n\n\n\n\n");
    return 0;
}

