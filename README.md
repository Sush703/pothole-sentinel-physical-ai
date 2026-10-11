# Pothole Sentinel: Physical AI Edge Node

**Nebius x NVIDIA Hackathon Submission | Track: Physical AI**

An edge-to-cloud Physical AI system that transforms standard vehicles into real-time road infrastructure monitors. It detects physical impacts, classifies road damage using Nebius vision models, and dispatches crews using NVIDIA Nemotron—all in under 3 seconds.

---

## System Architecture & Hardware-in-the-Loop

This project bridges embedded microcontrollers with cloud AI to create a seamless edge-to-cloud-to-edge pipeline:

1. **Physical Interrupt:** An Arduino Nano ESP32 acts as the edge device, simulating a physical road hazard impact via a timer loop triggering wire pins to initiate the pipeline.
2. **Visual Capture:** The edge script instantly wakes a connected webcam to snap a real-time frame of the road surface.
3. **Vision Inference:** The image is routed to the Nebius Token Factory running `openbmb/MiniCPM-V-4_5`. It returns a strict JSON payload grading the severity of the hazard.
4. **Automated Dispatch:** The JSON data is piped into NVIDIA `Nemotron-3.5-Lightning`, which acts as a virtual City Maintenance Dispatcher to generate urgent, context-aware repair instructions.
5. **Hardware Actuation:** The edge script parses the severity and fires a command back to the Arduino, triggering an RGB LED (Red for High severity, Green for Low) to alert the driver.
6. **Telemetry Logging:** All metrics, dispatch texts, and simulated GPS coordinates are appended to a local `incident_telemetry.json` GIS datastore for city planners.

## Nebius & NVIDIA Integration

* **NVIDIA Nemotron-3.5-Lightning:** Used as the core decision engine for dispatch operations. By feeding it the raw JSON output from the vision model, Nemotron instantly generated concise, actionable deployment orders for municipal maintenance crews.
* **Nebius Token Factory & AI Cloud:** Nebius was critical for achieving the sub-3-second end-to-end latency required for a moving vehicle. The Token Factory provided instant, reliable API access to MiniCPM-V, allowing the project to bypass heavy local model deployment and focus entirely on the physical hardware integration and pipeline logic.

## Hardware Requirements
* Arduino Nano ESP32
* USB Webcam
* Serial connection cable

  ### Hardware Feedback (RGB LED)
Once the cloud AI dispatches the severity score, the Arduino board actuates the LED:
*  **Red:** High Severity (Immediate dispatch required)
*  **Green:** Low Severity (Monitor condition/Scheduled Maintainence)

## Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/Sush703/pothole-sentinel-physical-ai.git
cd pothole-sentinel-physical-ai
```
**2. Install dependencies**

```Bash
pip install opencv-python pyserial openai python-dotenv
```
**3. Configure Environment Variables**

Create a .env file in the root directory and add your Nebius API key:

```bash
NEBIUS_API_KEY=your_api_key_here
```
**4. Update Hardware Ports**

*In sentinel.py, update the SERIAL_PORT variable to match your Arduino's active COM port.

*Running the System*

*Upload your interrupt script to the Arduino via the Arduino IDE.

*Close the Arduino IDE Serial Monitor to free the COM port.

*Run the edge Python script:

```Bash
python sentinel.py
```
*Allow the Arduino timer loop to trigger the detection pipeline.
