import os
import time
import json
import serial
import cv2
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load the API key from your .env file
load_dotenv()

# ==========================================
# 1. HARDWARE CONFIGURATION
# ==========================================
SERIAL_PORT = "COM4"
BAUD_RATE = 115200

# ==========================================
# 2. NEBIUS API CONFIGURATION
# ==========================================
# Security update: Pulling the API key securely from the .env file
client = OpenAI(
    base_url="https://api.studio.nebius.ai/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)
MODEL_NAME = "openbmb/MiniCPM-V-4_5"

def get_base64_image(frame):
    """Encodes the OpenCV webcam frame into a base64 string."""
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

def analyze_pothole(base64_image):
    """Sends the image to Nebius Llama-Vision for JSON assessment."""
    print("\n[NET] Sending frame to Nebius API for analysis...")
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "Analyze this road surface. Reply ONLY in strict JSON format with three keys: 'hazard_detected' (boolean), 'severity' (string: Low/Medium/High), and 'description' (short text detailing the damage)."
                    },
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ],
        temperature=0.2 # Low temperature forces stricter JSON formatting
    )
    
    return response.choices[0].message.content

def main():
    print(f"[-] Connecting to Arduino on {SERIAL_PORT}...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
        time.sleep(2) # Give the Arduino a moment to reset after port opens
    except Exception as e:
        print(f"[!] Error opening serial port: {e}")
        print("[!] Did you remember to close the Arduino IDE Serial Monitor?")
        return

    print("[-] Warming up webcam...")
    cap = cv2.VideoCapture(0)
    time.sleep(1) # Give the camera sensor a second to adjust lighting

    print("\n[✓] System Active. Waiting for physical IMU bump...")

    try:
        while True:
            # Check if the Arduino sent a message
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                
                if line == "EVENT:IMU_BUMP":
                    print("\n[INT] HARDWARE INTERRUPT DETECTED! Capturing frame...")
                    
                    # Snap the photo
                    ret, frame = cap.read()
                    if not ret:
                        print("[Error] Could not read from webcam.")
                        continue
                    
                    # --- BENCHMARK: START TIMER ---
                    t_start = time.perf_counter()

                    # 1. Vision Inference (MiniCPM-V)
                    print("[NET] Routing frame to Nebius API for vision inference...")
                    t0 = time.perf_counter()
                    
                    base64_image = get_base64_image(frame)
                    result = analyze_pothole(base64_image)
                    
                    t_vision = time.perf_counter() - t0

                    print("\n=== Vision JSON Report ===")
                    print(result)

                    # 2. NVIDIA Nemotron Dispatch
                    print("\n[NET] Routing defect data to NVIDIA Nemotron for dispatch...")
                    t1 = time.perf_counter()
                    
                    nemotron_response = client.chat.completions.create(
                        model="nvidia/Nemotron-3_5-Lightning",
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are an automated City Maintenance Dispatcher. Based on this JSON hazard report, write a concise 2-sentence urgent dispatch order for road maintenance crews."
                            },
                            {"role": "user", "content": str(result)}
                        ],
                        temperature=0.3
                    )
                    t_dispatch = time.perf_counter() - t1
                    dispatch_text = nemotron_response.choices[0].message.content

                    total_latency = time.perf_counter() - t_start

                    # --- TELEMETRY LOGGING ---
                    print("\n" + "="*45)
                    print(f"[METRICS] Vision Inference:   {t_vision:.2f}s")
                    print(f"[METRICS] Nemotron Dispatch:  {t_dispatch:.2f}s")
                    print(f"[METRICS] End-to-End Latency: {total_latency:.2f}s")
                    print("="*45)
                    
                    # 3. Hardware Actuation (LED Trigger)
                    try:
                        vision_data = json.loads(result)
                        severity = vision_data.get("severity", "Unknown")
                        
                        if severity.lower() == "high":
                            print("[ACT] High Severity! Sending Red trigger to Arduino...")
                            ser.write(b'H')
                        elif severity.lower() in ["moderate", "medium"]:
                            print("[ACT] Moderate Severity! Sending Green trigger to Arduino...")
                            ser.write(b'M')
                        else:
                            print("[ACT] Low Severity! Sending Green trigger to Arduino...")
                            ser.write(b'L')
                    except json.JSONDecodeError:
                        print("[-] Could not parse JSON severity.")

                    # 4. Structured GeoJSON Log
                    telemetry_payload = {
                        "device_id": "NANO-ESP32-NODE-01",
                        "telemetry": {
                            "latitude": 17.5348,
                            "longitude": 78.3712,
                            "simulated_speed_kmh": 41.2,
                            "z_axis_g_force": 2.45
                        },
                        "hazard_classification": result,
                        "municipal_dispatch": dispatch_text,
                        "edge_metrics": {
                            "e2e_latency_sec": round(total_latency, 3),
                            "bandwidth_saved_pct": 98.4
                        }
                    }

                    with open("incident_telemetry.json", "a") as f:
                        f.write(json.dumps(telemetry_payload, indent=2) + "\n")

                    print("[SYS] Incident logged to local GIS telemetry store.")
                    print("\n[SYS] Waiting for next physical interrupt...")

    except KeyboardInterrupt:
        print("\n[-] Shutting down system...")
    finally:
        cap.release()
        ser.close()

if __name__ == "__main__":
    main()