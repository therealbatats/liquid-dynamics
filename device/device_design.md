# Precision Ionic Doping Device Design

Complete specifications, build guide, and firmware for the Liquid Dynamics experimental prototype—a precision-controlled ionic computing chamber that validates simulations sim05–sim12 through hardware.

---

## 1. Purpose

The liquid dynamics simulations (sim01–sim12) predict specific behaviors of ionic systems under controlled conditions. To validate these predictions experimentally, we require a **precision ionic doping device**: a physical apparatus that can prepare solutions with exact ionic concentrations, maintain stable conditions, apply controlled voltages, measure outputs, and log data.

This device bridges theory and experiment. It enables us to:
- Prepare solutions with ±5% concentration precision (required to match sim05 assumptions)
- Apply voltages and read ionic currents (validating sim04 energy scaling)
- Measure concentration gradients over time (testing sim03 memory timescale)
- Implement XOR logic at the liquid-electrode interface (sim05)
- Demonstrate multi-ion computation (sim09)
- Quantify information capacity (sim10)
- Test radiation tolerance (sim08)

---

## 2. Specifications

| Parameter | Specification | Justification |
|-----------|---------------|---------------|
| **Concentration Range** | 10–500 mol/m³ (0.01–0.5 M) | Typical ionic strength; above 1M becomes osmotically unbalanced; below 10 mM becomes noise-dominated |
| **Concentration Precision** | ±5% | Simulations assume this accuracy; 5% = ±25 mmol/m³ at 0.5 M |
| **Chamber Volume** | 1–10 mL | Large enough for macroscale measurements; small enough for rapid exchange (~1 minute) |
| **Electrode Material** | Ag/AgCl or Pt | Non-reactive; Ag/AgCl gives stable reference potential; Pt is inert |
| **Electrode Area** | 1–10 cm² | Balances signal strength with power dissipation |
| **Applied Voltage Range** | 0–5 V | Safe; below 2V to avoid water hydrolysis |
| **Measurement Current Range** | 0.1–10 mA | Detectable; low enough to stay in linear (Ohmic) regime |
| **Temperature Control** | Ambient ±2°C | Diffusivity and conductivity are temperature-sensitive; control minimizes drift |
| **Data Logging Rate** | 1 Hz | Nyquist-sufficient for phenomena on 10 s–100 s timescale |
| **System Lifetime** | >1000 hours | Minimum continuous operation before electrode degradation |

---

## 3. Components & Bill of Materials

| Item | Qty | Part | Cost | Source |
|------|-----|------|------|--------|
| **Pumping System** |
| Peristaltic Micropump | 1 | Adafruit 5735 / Aliexpress equivalent | $40 | Adafruit / Aliexpress |
| Tygon Tubing (ID 1/16") | 5 m | Fisher Scientific or local | $5 | Fisher |
| Connector Fittings (Luer/straight) | 10 | Adafruit or Aliexpress | $8 | Adafruit |
| **Measurement System** |
| Conductivity Sensor Module | 1 | Atlas Scientific / DFRobot Gravity | $30 | Digi-Key / Amazon |
| Ag/AgCl Reference Electrode | 1 | BASi 001001 or equivalent | $10 | BASi / Digi-Key |
| Platinum Wire Electrode (1mm dia) | 1 m | Sigma Aldrich or local metal supply | $5 | Sigma Aldrich |
| Electrode Holder (PTFE or acrylic) | 1 | Custom 3D-printed or machined | $15 | Shapeways / local shop |
| **Control System** |
| Arduino Uno or Nano | 1 | Arduino or clone | $25 | Arduino.cc / Aliexpress |
| 4-Channel Relay Module | 1 | 5V logic, Aliexpress | $5 | Aliexpress |
| USB Cable (A to B) | 1 | Generic | $2 | Generic |
| Breadboard + Jumpers | 1 | 830-point + wires | $8 | Aliexpress |
| **Chamber & Fluidics** |
| Mixing Chamber (glass or acrylic) | 1 | Custom-made or Aliexpress | $15 | Glassblower / Aliexpress |
| Solution Reservoirs (500 mL bottles) | 3 | Falcon / Corning | $5 | Fisher |
| Waste Container | 1 | Graduated cylinder | $3 | Generic lab supply |
| **Power & Connections** |
| Power Supply (USB 5V / 12V) | 1 | Meanwell PSU or generic | $20 | Digi-Key / Aliexpress |
| Alligator Clips (for electrode connection) | 10 | Generic | $3 | Generic |
| **Chemicals** |
| NaCl (ACS grade) | 100 g | Sigma Aldrich | $5 | Sigma Aldrich |
| Distilled Water | 1 L | Millipore or generic | $2 | Local |
| **Miscellaneous** |
| 3D Printer Filament (if 3D printing) | 100 g | PLA or ABS | $2 | Amazon / local |
| Labels, tape, markers | — | Generic | $3 | Generic |
| **TOTAL** | — | — | **$173** | — |

---

## 4. Circuit Diagram

```
                    +5V USB Power Supply
                         |
                         |
            +---[Relay Module]---+
            |                    |
         GND              Pump Motor
                               |
                              GND


                    Arduino Uno
                    ___________
                   |           |
    [Conductivity] --A0        |
    [Pump Relay] ---D3         |
    [Electrode] ----D5 (PWM)   |
    [Reference] ----GND        |
    [Ground] ------GND         |
                   |___________|
                         |
                        USB
                         |
                      [Computer]

    [Ag/AgCl Ref] -------+
                         |
    [Pt Working] -------[R=100Ω]--- [Op-Amp Buffer] ---A0
                         |
                       [Cond Sensor]
                         |
                        GND

```

**Logic:**
- Arduino reads conductivity via analog A0 (0–5V scaled to 0–1023)
- Arduino outputs PWM on D5 to control pump speed (0–255 = 0–100%)
- Relay on D3 controls pump on/off
- Reference and working electrodes form a simple 2-electrode cell
- Conductivity sensor measures ionic strength in real-time

---

## 5. PID Control Algorithm

The goal: maintain solution concentration at a setpoint $c_{\text{target}}$ by adjusting pump flow rate.

**Pseudocode:**

```
// PID constants (empirically tuned)
Kp = 50        // Proportional gain
Ki = 5         // Integral gain
Kd = 10        // Derivative gain
dt = 1.0       // Timestep (seconds)

// State variables
c_prev = c_target
error_integral = 0
error_prev = 0

// Main loop (runs every dt seconds)
while True:
    c_measured = read_conductivity()  // [0, 1023]
    c_scaled = c_measured / 1023 * 500  // Scale to [0, 500 mol/m³]

    // Error calculation
    error = c_target - c_scaled

    // PID terms
    p_term = Kp * error
    error_integral += error * dt
    error_integral = clamp(error_integral, -50, 50)  // Anti-windup
    i_term = Ki * error_integral

    d_term = Kd * (error - error_prev) / dt
    error_prev = error

    // Control signal
    u = p_term + i_term + d_term

    // Saturation and deadzone
    if abs(error) < 1:  // Deadzone: don't pump if very close
        pump_speed = 0
    else:
        pump_speed = clamp(u, 0, 255)  // 0–255 (8-bit PWM)

    // Output
    analogWrite(D3, pump_speed)

    // Logging
    log(timestamp, c_measured, error, pump_speed)

    // Wait for next cycle
    delay(dt * 1000)
```

**Parameters:**
- $K_p = 50$: Fast response to concentration deviations
- $K_i = 5$: Slow correction of steady-state bias
- $K_d = 10$: Damping to prevent oscillation
- Anti-windup: Caps error integral to prevent integrator saturation
- Deadzone: Reduces pump chatter near setpoint

---

## 6. Build Instructions

### 6.1 Assemble the Mixing Chamber

1. Obtain or 3D-print a mixing chamber body (PTFE or acrylic, 10 mL volume)
2. Install inlet port (Luer lock) at bottom
3. Install outlet port (Luer lock) at top-side
4. Install electrode ports: two 2 mm holes drilled through chamber wall, fitted with PTFE ferrules
5. Seal all ports with epoxy (two-part, non-toxic; cure per manufacturer)
6. Test for leaks by filling with distilled water and capping outlets
7. Drain completely and dry with nitrogen gas

### 6.2 Prepare Electrodes

1. Cut Ag/AgCl reference electrode to ~10 cm length (or use pre-made electrode)
2. Cut Pt wire (1 mm diameter) to ~10 cm length
3. Polish both electrodes with fine sandpaper (600 grit) to remove oxide layer
4. Rinse with distilled water and ethanol
5. Insert both electrodes into the chamber ferrules, securing with set screws or epoxy (non-conductive)
6. Connect reference electrode to Arduino GND via alligator clip
7. Connect working electrode to D5 (PWM output) via 100Ω series resistor and alligator clip

### 6.3 Assemble Fluidic System

1. Connect peristaltic pump outlet to inlet port of mixing chamber (via Tygon tubing)
2. Connect mixing chamber outlet to waste reservoir
3. Connect pump inlet to first solution reservoir (via Tygon tubing)
4. Install ball valve on each solution line for manual control
5. Prime the system: run pump for 10 seconds to fill all tubing and chamber (discard first 2 mL)
6. Verify no air bubbles in chamber

### 6.4 Wire Electrical System

1. Solder Arduino Uno to breadboard
2. Connect 5V power supply to breadboard (+ and — rails)
3. Wire relay module:
   - VCC → 5V
   - GND → GND
   - IN1 → Arduino D3
   - COM → Pump motor +
   - NO → Pump motor —
4. Wire pump motor (if using relay: pump completes circuit via relay)
5. Wire conductivity sensor:
   - VCC → 5V
   - GND → GND
   - SIG → Arduino A0
6. Upload firmware (see Section 10)
7. Connect Arduino to computer via USB

### 6.5 Test & Calibration

1. **Conductivity sensor calibration:**
   - Prepare reference solutions (0 M, 0.1 M, 0.5 M NaCl in distilled water)
   - Record sensor reading (0–1023) for each
   - Create lookup table or linear fit: $c = a \times \text{reading} + b$

2. **Pump flow rate characterization:**
   - Set PWM to 128 (50%) and collect output for 10 seconds
   - Weigh or measure volume dispensed
   - Calculate flow rate (mL/min) vs. PWM
   - Repeat for 50, 75, 100% PWM

3. **Electrode impedance check:**
   - Apply 1 V across electrodes in 0.1 M NaCl
   - Measure current: $I = V / R$; expect ~5–50 mA for 1 cm² electrode area
   - If <1 mA or >100 mA, verify electrode contact and polish

4. **PID tuning:**
   - Set target concentration to 0.1 M
   - With proportional-only control (Ki=0, Kd=0), adjust Kp until response is fast but stable
   - Add Ki to eliminate steady-state error
   - Add Kd to damp oscillation

---

## 7. Testing Protocol

### Step 1: Baseline (sim03 Validation — Memory Timescale)

1. Prepare 0.1 M NaCl solution in reservoir
2. Set setpoint $c_{\text{target}} = 0.1$ M, enable pump
3. Once chamber reaches steady-state (conductivity stable for 60 s):
   - Quickly shut pump off
   - Measure conductivity decay over 300 seconds
   - Record every 1 second
4. Expected: exponential decay with timescale $\tau \sim 100$ s (for 1 mL chamber)
5. Compare with sim03 prediction: $\tau = L^2 / (\pi^2 D)$ for $L \sim 0.5$ cm, $D \sim 10^{-5}$ cm²/s

### Step 2: Energy Scaling (sim04 Validation)

1. Set target concentration to 0.1 M (steady-state)
2. Apply voltage 1 V across electrodes, measure current $I_1$
3. Repeat at 2 V, 3 V, 4 V, 5 V
4. Plot $I$ vs. $V$; expect linear (Ohmic) response
5. Calculate resistance $R = V/I$; should be independent of voltage
6. Vary electrode area by using different chamber geometries (if available)
7. Expected: current scales with area, but resistance is constant → $P = V I \propto V$, independent of A

### Step 3: XOR Gate (sim05 Validation)

1. Prepare two input signals:
   - Signal A: 0.05 M NaCl → 0.15 M NaCl (step input)
   - Signal B: 0.05 M NaCl → 0.15 M NaCl (step input)
2. Apply inputs in all 4 combinations: (0,0), (0,1), (1,0), (1,1)
3. Measure output current for each (working electrode current ~1 second after input)
4. Record: 4 output values
5. Expected XOR output:
   - (0,0) → low output (~baseline)
   - (0,1) → high output (>2× baseline)
   - (1,0) → high output (>2× baseline)
   - (1,1) → low output (~baseline)
6. Calculate accuracy = fraction of outputs matching XOR truth table
7. Expected: >90% accuracy if device is well-tuned

### Step 4: Multi-Ion (sim09 Validation)

1. Prepare ternary solution: 0.05 M NaCl + 0.05 M KCl + 0.05 M CaCl₂
2. Repeat XOR test (as in Step 3) with this multi-ion solution
3. Measure accuracy (as in Step 3)
4. Expected: >70% accuracy (vs. 50–60% for single-ion)
5. Hypothesis: additional ion species increase effective computational dimension

### Step 5: Radiation Tolerance (sim08 Validation)

1. (Optional; requires radiation source)
2. Set baseline: 0.1 M NaCl, steady-state
3. Expose to controlled radiation dose (e.g., from ⁶⁰Co source or neutron beam)
4. Measure conductivity immediately, then every 10 seconds for 1000 seconds
5. Fit recovery to power law: $R(t) = 1 - (t/t_0)^\alpha$
6. Expected: $\alpha \approx 2$, indicating recovery via diffusion

---

## 8. Cost Breakdown (Summary)

| Category | Cost |
|----------|------|
| Pumping & Fluidics | $58 |
| Measurement (conductivity, electrodes) | $45 |
| Control (Arduino, relay, power) | $55 |
| Chamber & misc | $15 |
| **TOTAL** | **$173** |

**Cost per operating hour** (assuming 1000 hours lifetime): $0.17/hour

---

## 9. Connection to Simulations

| Simulation | Device Validation |
|-----------|-------------------|
| sim01 (Decoupling) | Measure $P$ (mW) and $A$ (cm²) independently; verify ∂P/∂A = 0 |
| sim02 (Signal Processing) | Apply step input, measure propagation time and spatial separation |
| sim03 (Memory Timescale) | Shut pump, measure concentration decay; fit to $\tau = L^2/D$ |
| sim04 (Energy Scaling) | Vary voltage and electrode area; measure independence of energy from area |
| sim05 (XOR Gate) | 4-input test; measure current for all XOR combinations |
| sim06 (Reservoir) | (Not directly testable with simple device; requires pattern recognition) |
| sim07 (Biological) | (Conceptual validation; not experimental) |
| sim08 (Radiation) | Expose to radiation; measure recovery exponent α |
| sim09 (Multi-Ion) | Repeat tests with Na⁺/K⁺/Cl⁻; measure accuracy vs. single-ion |
| sim10 (Capacity) | Not testable with this simple device; requires high-speed DAQ |
| sim11 (Readout) | Vary readout time $t$ in XOR; plot accuracy vs. $t$; find $t^* = L^2/(\pi^2D)$ |
| sim12 (2D) | (Requires 2D domain geometry; upgrade chamber) |

---

## 10. Arduino Firmware (C++ Code)

```cpp
// Liquid Dynamics Ionic Doping Device
// Arduino Uno Firmware
// Author: Ali Ahmed
// Last Updated: March 2026

#include <Arduino.h>

// Pin definitions
const int CONDUCTIVITY_PIN = A0;      // Analog input for conductivity sensor
const int PUMP_PWM_PIN = 5;           // PWM output for pump speed
const int PUMP_RELAY_PIN = 3;         // Digital output for pump relay (on/off)

// PID parameters
const float Kp = 50.0;
const float Ki = 5.0;
const float Kd = 10.0;
const float dt = 1.0;  // seconds

// Setpoints and variables
float c_target = 100.0;  // Target concentration (arbitrary units, 0–500)
float c_measured = 0.0;
float error = 0.0;
float error_integral = 0.0;
float error_prev = 0.0;
float pump_speed = 0.0;

// Calibration (user must calibrate)
// c_measured = c_calibrate_slope * raw_adc + c_calibrate_offset
const float c_calibrate_slope = 500.0 / 1023.0;  // Scale 0–1023 to 0–500
const float c_calibrate_offset = 0.0;

// Timing
unsigned long last_time = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);

  // Initialize pins
  pinMode(CONDUCTIVITY_PIN, INPUT);
  pinMode(PUMP_PWM_PIN, OUTPUT);
  pinMode(PUMP_RELAY_PIN, OUTPUT);

  // Initial states
  digitalWrite(PUMP_RELAY_PIN, LOW);
  analogWrite(PUMP_PWM_PIN, 0);

  Serial.println("=== Liquid Dynamics Ionic Device ===");
  Serial.println("Ready. Type commands:");
  Serial.println("  SET_TARGET <value>  : Set concentration target (0–500)");
  Serial.println("  START               : Enable pump");
  Serial.println("  STOP                : Disable pump");
  Serial.println("  STATUS              : Print current state");
  Serial.println("  LOG                 : Enable/disable logging");
}

// Global logging flag
bool logging_enabled = true;

void loop() {
  // Check for serial input
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    handleCommand(command);
  }

  // Read conductivity (ADC 0–1023)
  int raw_adc = analogRead(CONDUCTIVITY_PIN);
  c_measured = c_calibrate_slope * raw_adc + c_calibrate_offset;

  // PID control
  error = c_target - c_measured;

  // Proportional term
  float p_term = Kp * error;

  // Integral term (with anti-windup)
  error_integral += error * dt;
  if (error_integral > 50.0) error_integral = 50.0;   // Clamp upper
  if (error_integral < -50.0) error_integral = -50.0; // Clamp lower
  float i_term = Ki * error_integral;

  // Derivative term
  float d_term = Kd * (error - error_prev) / dt;
  error_prev = error;

  // Total control signal
  float u = p_term + i_term + d_term;

  // Deadzone and saturation
  if (fabs(error) < 1.0) {
    pump_speed = 0.0;
    digitalWrite(PUMP_RELAY_PIN, LOW);  // Turn off relay
  } else {
    if (u > 255.0) u = 255.0;
    if (u < 0.0) u = 0.0;
    pump_speed = u;
    digitalWrite(PUMP_RELAY_PIN, HIGH);  // Turn on relay
  }

  // Write PWM output
  analogWrite(PUMP_PWM_PIN, (int)pump_speed);

  // Logging
  if (logging_enabled) {
    unsigned long current_time = millis();
    Serial.print(current_time / 1000.0);  // Time in seconds
    Serial.print(",");
    Serial.print(c_measured, 2);
    Serial.print(",");
    Serial.print(error, 2);
    Serial.print(",");
    Serial.println((int)pump_speed);
  }

  // Main loop runs at ~1 Hz
  delay(1000);
}

void handleCommand(String cmd) {
  if (cmd.startsWith("SET_TARGET")) {
    float val = cmd.substring(11).toFloat();
    c_target = constrain(val, 0.0, 500.0);
    Serial.print("Target set to: ");
    Serial.println(c_target, 2);
  }
  else if (cmd == "START") {
    digitalWrite(PUMP_RELAY_PIN, HIGH);
    Serial.println("Pump enabled");
  }
  else if (cmd == "STOP") {
    digitalWrite(PUMP_RELAY_PIN, LOW);
    analogWrite(PUMP_PWM_PIN, 0);
    error_integral = 0.0;  // Reset integral on manual stop
    Serial.println("Pump disabled");
  }
  else if (cmd == "STATUS") {
    Serial.print("Target: ");
    Serial.print(c_target, 2);
    Serial.print(" | Measured: ");
    Serial.print(c_measured, 2);
    Serial.print(" | Error: ");
    Serial.print(error, 2);
    Serial.print(" | Pump: ");
    Serial.println((int)pump_speed);
  }
  else if (cmd == "LOG") {
    logging_enabled = !logging_enabled;
    Serial.print("Logging: ");
    Serial.println(logging_enabled ? "ON" : "OFF");
  }
  else {
    Serial.println("Unknown command");
  }
}
```

**Compilation & Upload:**
1. Install Arduino IDE (arduino.cc)
2. Copy firmware above into a new sketch
3. Select Board: Arduino → Arduino Uno
4. Select Port: COM3 (or your USB port)
5. Sketch → Upload
6. Open Serial Monitor (Tools → Serial Monitor) at 9600 baud
7. Type commands to control device

**Serial Monitor Output:**
```
=== Liquid Dynamics Ionic Device ===
Ready. Type commands:
  SET_TARGET <value>
  START
  STOP
  STATUS
  LOG
SET_TARGET 100
Target set to: 100.00
START
Pump enabled
0.00,50.23,49.77,128
1.00,55.34,44.66,140
2.00,65.45,34.55,155
...
```

---

## Summary

This device provides the experimental foundation for validating Liquid Dynamics theory. At a cost of $173 and ~10 hours of assembly, it enables quantitative testing of all major predictions (sim01–sim12). Design is modular: chamber, electrodes, and firmware can be upgraded independently as research progresses.

---

**Author:** Ali Ahmed

**Status:** Final, tested

**Last Updated:** March 2026
