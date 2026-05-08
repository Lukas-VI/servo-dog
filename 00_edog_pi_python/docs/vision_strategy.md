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
- Split the far ROI into left, straight, and right zones to detect forks.

This is a deliberate upgrade over the old pixel scan. It remains simple enough
for Raspberry Pi, but is less brittle under broken line segments and lighting
changes.

## V2 Candidate

Because the current course has no QR code, AprilTag, or ArUco anchors, the next
production step is line-only topological localization:

- treat each confident fork as a node in a route graph;
- store available exits as `left`, `straight`, and `right`;
- use odometry only between forks, then snap decisions back to the route graph;
- keep `branch.default_turn`, `branch.fork_confidence`, and `branch.turn_bias`
  configurable from the browser panel.

This is more practical than full visual SLAM for a marked race track: it gives
the state machine useful semantic progress without requiring textured walls,
camera calibration, or loop closure to be perfect.

## Browser SLAM Demo

The debug console includes a browser-side SLAM demo tab. It is intentionally a
teaching and tuning surface, not the robot's production localization backend:

- simulates feature odometry, pose drift, local landmarks, fork nodes, and a
  loop-closure candidate signal;
- keeps feature count, map decay, motion scale, and loop threshold in
  `config.yaml`;
- shares branch parameters with the production state machine;
- can run next to the live camera stream while pure-vision tracking remains the
  default control path.

If the rules later allow visual anchors, AprilTag/ArUco fixed-point resets can
be added back as optional corrections. They are no longer the first production
assumption.

## Research Only

ORB-SLAM3 and similar visual SLAM stacks are useful references, but they are not
the default path for this robot because deployment, calibration, and real-time
performance risk are high on Raspberry Pi.
