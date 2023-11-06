#simple pc test device for send and receive data
#ai generated code for testing 

# Import the serial module
import serial

# Create a serial object for COM1 port
ser = serial.Serial('COM1')

# Define a function to send a string every 6 seconds
def send_string():
    # Create a string with humidity info
    data = "humidity,1"
    # Encode the string as bytes
    data = data.encode()
    # Write the bytes to the serial port
    ser.write(data)
    # Print a message to the terminal
    print("Sent data: " + data.decode())
    # Schedule the function to run again after 6 seconds
    ser.timeout(6, send_string)

# Start the function
send_string()

# Create an infinite loop to check for bytes to read
while True:
    # If there are bytes available in the input buffer
    if ser.in_waiting > 0:
        # Read the bytes and store them in a variable
        received = ser.read(ser.in_waiting)
        # Decode the bytes as a string
        received = received.decode()
        # Print the received string to the terminal
        print("Received data: " + received)