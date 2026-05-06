# Pure Vision Strategy

## V1 Default

The first version uses only camera input and OpenCV:

- Resize to a stable processing size.
- Crop the lower road region.
- Equalize grayscale, blur, adaptive threshold.
- Canny edges plus probabilistic Hough line segments.
- Weighted line center estimates lateral error.
- PID maps error to side velocity and yaw.
- HSV masks detect task colors.

This is a deliberate upgrade over the old pixel scan. It remains simple enough
for Raspberry Pi, but is less brittle under broken line segments and lighting
changes.

## V2 Candidate

Add AprilTag or ArUco markers at important course locations. This gives reliable
semantic anchors without full SLAM complexity.

## Research Only

ORB-SLAM3 and similar visual SLAM stacks are useful references, but they are not
the default path for this robot because deployment, calibration, and real-time
performance risk are high on Raspberry Pi.

