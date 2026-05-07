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

## Browser SLAM Demo

The debug console includes a browser-side SLAM demo tab. It is intentionally a
teaching and tuning surface, not the robot's production localization backend:

- simulates feature odometry, pose drift, local landmarks, and a loop-closure
  candidate signal;
- keeps feature count, map decay, motion scale, and loop threshold in
  `config.yaml`;
- can run next to the live camera stream while pure-vision tracking remains the
  default control path.

The production path should still prefer AprilTag/ArUco fixed-point resets before
attempting ORB-SLAM3 or another heavy visual SLAM stack on the Raspberry Pi.

## Research Only

ORB-SLAM3 and similar visual SLAM stacks are useful references, but they are not
the default path for this robot because deployment, calibration, and real-time
performance risk are high on Raspberry Pi.
