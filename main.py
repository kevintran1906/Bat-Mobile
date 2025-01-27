from time import sleep
from machine import Pin, PWM
import network
import socket

# Motor setup
EN_A = PWM(Pin(11))  # Left motor PWM
EN_B = PWM(Pin(18))  # Right motor PWM
In1 = Pin(12, Pin.OUT)
In2 = Pin(13, Pin.OUT)
In3 = Pin(20, Pin.OUT)
In4 = Pin(19, Pin.OUT)

# Set PWM frequency
EN_A.freq(1000)
EN_B.freq(1000)

# Calibration factors for motors
LEFT_CALIBRATION = 1.0  # No scaling for the left motor
RIGHT_CALIBRATION = 0.5  # Scale down the right motor to 50% of input speed

# Initialize LEDs
led_power = Pin(14, Pin.OUT)  # LED that turns on when powered
led_server = Pin(15, Pin.OUT)  # LED that turns on when connected to server

# Turn on the power LED when the device is powered
led_power.on()

# Initialize Wi-Fi
#ssid = "Rogers82"
#pw = "5198037457"

#ssid = "Kevin's Iphone"
#pw = "12345666"

ssid = "CYBERTRON"
pw = "Mr.LamYo"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, pw)

while not wlan.isconnected():
    print("Connecting...")
    sleep(1)
print("Connected!")

# Turn on the server LED when connected to Wi-Fi
led_server.on()

wlan_info = wlan.ifconfig()
print("My Pico's IP address is:", wlan_info[0])

# Motor control function
def set_motor_speed(motor, speed):
    pwm = EN_A if motor == "left" else EN_B
    direction_pin1 = In1 if motor == "left" else In3
    direction_pin2 = In2 if motor == "left" else In4

    # Apply calibration
    if motor == "left":
        speed *= LEFT_CALIBRATION
    else:
        speed *= RIGHT_CALIBRATION

    if speed == 0:  # Stop the motor
        pwm.duty_u16(0)
        direction_pin1.low()
        direction_pin2.low()
    elif speed > 0:  # Forward direction
        pwm.duty_u16(int(speed * 65535 / 100))  # Convert speed (0-100) to duty cycle
        direction_pin1.high()
        direction_pin2.low()
    else:  # Reverse direction
        pwm.duty_u16(int(abs(speed) * 65535 / 100))  # Convert speed (0-100) to duty cycle
        direction_pin1.low()
        direction_pin2.high()

# Web server to handle slider updates
def start_server():
    addr = socket.getaddrinfo(wlan_info[0], 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)

    while True:
        cl, addr = s.accept()
        request = cl.recv(1024).decode()
        print("Request:", request)

        # Extract motor and speed values from request
        if "left" in request or "right" in request:
            try:
                motor = "left" if "left" in request else "right"
                # Slider value range is 0-100; map to -100 to 100
                slider_value = int(request.split("speed=")[1].split(" ")[0])
                speed = slider_value - 50  # Convert slider range (0-100) to speed range (-50 to 50)
                set_motor_speed(motor, speed)
            except Exception as e:
                print("Error parsing speed:", e)

        # Serve the HTML file once
        if "GET / " in request or "GET /index.html" in request:
            cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            cl.send('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Motor Control</title>
    <style>
        body {
            margin: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #D3D3D3;
            font-family: Arial, sans-serif;
            overflow: hidden;
            position: relative;
        }

        h1 {
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 36px;
            color: #FF1C1C;
            margin: 0;
            text-align: center;
        }

        .slider-container {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            justify-content: space-between;
            width: 100%;
            padding: 0 20px;
            box-sizing: border-box;
        }

        .slider {
            writing-mode: bt-lr; /* Rotate the slider vertically */
            -webkit-appearance: none;
            width: 300px; /* Length of the slider */
            height: 40px; /* Thickness for easier grabbing */
            background: #FFDD57;
            border-radius: 10px;
            outline: none;
            transform: rotate(-90deg); /* Make the slider vertical */
            cursor: pointer;
        }

        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 40px; /* Thumb width */
            height: 40px; /* Thumb height */
            background: #FF4500;
            border-radius: 50%;
            cursor: pointer;
        }

        .slider::-moz-range-thumb {
            width: 40px;
            height: 40px;
            background: #FF4500;
            border-radius: 50%;
            cursor: pointer;
        }

        .left-slider {
            position: absolute;
            left: 20px;
        }

        .right-slider {
            position: absolute;
            right: 20px;
        }
    </style>
</head>
<body>
    <h1>Motor Control</h1>
    <div class="slider-container">
        <input
            type="range"
            min="0"
            max="100"
            value="50"
            class="slider left-slider"
            id="leftSlider"
            onchange="updateMotor('left', this.value)"
        />
        <input
            type="range"
            min="0"
            max="100"
            value="50"
            class="slider right-slider"
            id="rightSlider"
            onchange="updateMotor('right', this.value)"
        />
    </div>

    <script>
        function updateMotor(motor, value) {
            const xhr = new XMLHttpRequest();
            xhr.open("GET", `/${motor}?speed=${value}`, true);
            xhr.send();
        }
    </script>
</body>
</html>''')
        else:
            cl.send('HTTP/1.1 204 No Content\r\n\r\n')

        cl.close()

# Start the server
start_server()

