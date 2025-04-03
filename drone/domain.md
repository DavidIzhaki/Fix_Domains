# 🛩️ Drone Domain (PDDL)

The **Drone Domain** models a 3D environment where a UAV (unmanned aerial vehicle) must **visit specific locations in space**. Each target location is defined by exact 3D coordinates. The drone navigates this space using `x`, `y`, and `z` axis movement actions, and has a **limited battery capacity**.

The domain is designed to evaluate **resource-aware navigation and motion planning**. The UAV must return to its base at `(0,0,0)` to recharge, making **multi-trip plans** essential for solving the task efficiently.

It is especially useful for testing:
- **Battery-constrained movement**
- **3D spatial planning**
- **Plan reuse, recharge strategies, and numeric constraint satisfaction**

---

## 📂 Domain Overview

### Objects

- **Locations**: Each `location` represents a target that must be visited:
  - `xl`, `yl`, `zl`: their x, y, z coordinates
- The drone itself is implicitly located via:
  - `(x)`, `(y)`, `(z)`: current position in the 3D space

---

## 🧮 Domain Type: Linear Task (LT)

This domain qualifies as a **Linear Task (LT)** because it includes:

- **Arithmetic expressions** in preconditions, e.g., `(+ min_x 1)`
- **Numeric `assign`** operations (e.g., setting battery to full)
- **Fluent equality** for goal conditions (e.g., `(= (x) (xl ?l))`)

This makes it more expressive and challenging than SNT or RT domains.

---

## ⚙️ Domain Mechanics

### Predicates

- `(visited ?l - location)` — Indicates whether a given location has already been visited

---

### Functions

- `(x)` / `(y)` / `(z)` — Current position of the UAV
- `(xl ?l)` / `(yl ?l)` / `(zl ?l)` — Coordinates of each target location
- `(battery-level)` — Current battery level
- `(battery-level-full)` — Constant representing max battery
- `(min_x)` / `(max_x)` / `(min_y)` / `(max_y)` / `(min_z)` / `(max_z)` — Movement bounds in all three axes

---

### ⚙️ Actions

#### ➕ `increase_x`, `increase_y`, `increase_z`

<pre>
(:action increase_x
  :parameters ()
  :precondition (and (>= (battery-level) 1) (<= (x) (- (max_x) 1)))
  :effect (and (increase (x) 1) (decrease (battery-level) 1))
)
</pre>

Each movement increases position by 1 unit and costs 1 battery.

---

#### ➖ `decrease_x`, `decrease_y`, `decrease_z`

<pre>
(:action decrease_y
  :parameters ()
  :precondition (and (>= (battery-level) 1) (>= (y) (+ (min_y) 1)))
  :effect (and (decrease (y) 1) (decrease (battery-level) 1))
)
</pre>

These decrease position by 1 unit and also drain 1 battery per step.

---

#### 📍 `visit`

<pre>
(:action visit
  :parameters (?l - location)
  :precondition (and
    (>= (battery-level) 1)
    (= (xl ?l) (x))
    (= (yl ?l) (y))
    (= (zl ?l) (z)))
  :effect (and (visited ?l) (decrease (battery-level) 1))
)
</pre>

Visits the location if drone is at the exact matching 3D coordinates. Costs 1 battery.

---

#### 🔋 `recharge`

<pre>
(:action recharge
  :parameters ()
  :precondition (and (= (x) 0) (= (y) 0) (= (z) 0))
  :effect (assign (battery-level) (battery-level-full))
)
</pre>

Only available at origin `(0,0,0)` — resets battery level to full.

---

## 🔍 What the Planner Tries to Do

Given:

- A set of target `locations` in 3D space
- The drone's start at `(0,0,0)`
- A limited `battery-level`
- A `battery-level-full` constant

The planner must:

- Navigate to each location and use `visit`
- Return to base to recharge as needed
- Minimize overall cost or action count
- Obey movement bounds (`min_x`, `max_x`, etc.)

---

## 🧾 Example

Suppose the drone must visit 2 locations:

- `loc1` at (3, 0, 0)
- `loc2` at (0, 2, 0)

Initial battery: 5  
Battery full: 5  
Each move: -1 battery

**Plan**:
1. Move X+ to (3,0,0), visit `loc1`
2. Return to (0,0,0), recharge
3. Move Y+ to (0,2,0), visit `loc2`

This plan handles both visits with just one recharge.

---

## 🧪 Example Use Cases

- **Drone delivery** and UAV logistics
- **Battery-aware exploration**
- **Multi-goal navigation**
- **Spatiotemporal AI planning research**

---

## 🎒 Extras

This domain pairs well with:

- **Temporal planners** (when adding time cost to moves)
- **Resource-aware planning**
- **Heuristics with numeric reasoning**
- **Multi-agent UAV coordination (with extensions)**

