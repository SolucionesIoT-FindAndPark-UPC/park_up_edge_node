# ESP32 Cam Integration Guide

This guide explains how to integrate your ESP32 camera with the edge node for automatic license plate recognition.

## Overview

The system now supports real-time processing of ESP32 camera streams for automatic license plate detection. It captures frames from your ESP32 cam stream and processes them using your existing plate recognition system.

## ESP32 Cam Setup

1. **ESP32 Cam Stream URL Format**: 
   - Your ESP32 uses: `http://192.168.18.85/capture`
   - Standard format: `http://YOUR_ESP32_IP/capture` (for image capture)
   - Alternative: `http://YOUR_ESP32_IP:81/stream` (for video stream, if available)

2. **Make sure your ESP32 cam is**:
   - Connected to the same WiFi network
   - Running a stream server (usually on port 81)
   - Accessible from your edge node

## Available Endpoints

### 1. Start Stream Processing
```http
POST /edge/camera/stream/start-processing
Content-Type: application/json

{
    "cameraId": "esp32_cam_01",
    "streamUrl": "http://192.168.18.85/capture",
    "processInterval": 3
}
```

### 2. Stop Stream Processing
```http
POST /edge/camera/stream/stop-processing
Content-Type: application/json

{
    "cameraId": "esp32_cam_01"
}
```

### 3. Check Active Streams
```http
GET /edge/camera/stream/status
```

### 4. Start Circulation Monitoring (Simplified)
```http
POST /edge/parking/circulation/esp32/{camera_id}?stream_url=http://192.168.18.85/capture
```

### 5. Stop Circulation Monitoring
```http
DELETE /edge/parking/circulation/esp32/{camera_id}
```

### 6. Test ESP32 Connection
```http
GET /edge/camera/stream/test/{camera_id}
```

## Quick Start

1. **Update ESP32 IP**: Edit the IP address in the test files to match your ESP32 cam
2. **Start the server**: 
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
3. **Test connection**: Run the test script
   ```bash
   python test_esp32_cam.py
   ```
4. **Start processing**: Use the HTTP requests in `test_esp32_stream.http`

## Configuration

### Process Interval
- Default: 3 seconds between plate recognition attempts
- Adjustable via `processInterval` parameter
- Lower values = more frequent processing (higher CPU usage)
- Higher values = less frequent processing (lower CPU usage)

### Callback Functions
The system includes callback functions that trigger when a plate is detected:
- Print detected plates to console
- Can be extended to update parking site occupancy
- Can send data to backend systems
- Can trigger notifications

## Testing

### Option 1: Use the Python Test Script
```bash
python test_esp32_cam.py
```

### Option 2: Use HTTP Requests
Open `test_esp32_stream.http` in VS Code and run the requests

### Option 3: Manual Testing
1. Start stream processing
2. Point your ESP32 cam at a license plate
3. Check console output for detected plates
4. Stop processing when done

## Troubleshooting

### Common Issues

1. **Cannot connect to ESP32 stream**
   - Check ESP32 IP address
   - Verify ESP32 is on the same network
   - Test stream URL in browser
   - Check ESP32 cam is powered and running

2. **No plates detected**
   - Ensure good lighting
   - Check camera angle and distance
   - Verify plate is clearly visible
   - Check console for processing logs

3. **High CPU usage**
   - Increase `processInterval` value
   - Reduce frame processing frequency
   - Check system resources

### Debugging

Enable detailed logging by checking the console output when processing is active. You'll see:
- Stream connection status
- Frame processing attempts
- Detected plates with timestamps
- Error messages if any

## Integration with Existing System

The ESP32 cam integration works alongside your existing `/edge/parking/circulation` endpoint:

- **File upload**: Use existing endpoint for manual plate recognition
- **Stream processing**: Use new endpoints for automatic real-time recognition
- **Both methods**: Use the same plate recognizer and return the same format

## Next Steps

You can extend the system by:
1. Adding database storage for detected plates
2. Implementing parking site occupancy updates
3. Adding real-time notifications
4. Creating a web dashboard for monitoring
5. Adding multiple camera support
6. Implementing vehicle tracking between cameras
