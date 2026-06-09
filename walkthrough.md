# Drone Simulation Walkthrough 🚁

I have successfully developed and launched the Pygame drone simulation! A window titled **"Drone V-Formation & FPGA Interactive Sim"** should now be visible entirely running on your machine.

## What was Changed

#### [NEW] [drone_simulation.py](file:///C:/Users/nimma/OneDrive/Desktop/%23%20production%20no%201/drone_simulation.py)
A completely independent and responsive physical simulation of drones.
- Developed a procedurally drawn `Drone` class, rendering 4 continuous sweeping propellers for visual immersion without requiring external images.
- Implemented an `FPGA` entity functioning as the central hardware controller that actively coordinates target relative positions based on physical offsets.
- Handled environmental packaging issues with modern Python installations by utilizing the Pygame Community Edition (`pygame-ce`).

## Verification & How to Interact

> [!NOTE] 
> In this simulated environment, moving a single drone acts as setting a new baseline. Unlike real life where an FPGA might hold the swarm entirely stationary relative to Earth, the simulation dynamically shifts the origin to whatever drone you interact with to let you see the collision/adjustment math in action.

Here is how you can verify the execution:
1. **Drag a Drone**: Use your mouse to left-click and hold onto any drone on the screen. Try moving it continuously.
2. **Observe the Adjustments**: The remaining two drones will automatically detect they are out of the designated V-shape constraints relative to the tracked "leader" drone, and propel themselves fluidly to their new target positions.
3. **Follow the Signal Paths**:
   - **Cyan Signals (Telemetry):** Continuous data streams pulsing from the Drones inwards to the FPGA, checking bounds.
   - **Red Signals (Alert/Command):** The FPGA box visually highlights its internal Alert mode when corrections are calculating. The glowing red packets visually flow from the FPGA hardware node directly to whichever drones are off course, simulating the data dispatch.
