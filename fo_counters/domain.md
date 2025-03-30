# 🔄 FO-Counters Domain (PDDL)

The **FO-Counters Domain** is an extension of the original Counters domain. It adds the concept of a `rate_value` to each counter, allowing values to **automatically increase over time** — simulating systems where variables evolve even without direct actions.

This is especially useful for modeling **time-based progression**, **natural growth/decay**, and **flow-based systems**.

---

## 📂 Domain Overview

### Objects

- **Counters**: Each counter (e.g., `c0`, `c1`, etc.) represents a numeric variable with:
  - `value`: current integer value
  - `rate_value`: automatic increment added every time step (like a derivative or speed)

---

## ⚙️ Domain Mechanics

### Predicates

- `(value ?c - counter)` — The current value of counter `?c`.
- `(rate_value ?c - counter)` — The rate of change applied at every step.

---

### Functions

- `increase-counter`: Increases the value of a counter by 1 (if not above `max_value`)
- `decrease-counter`: Decreases the value of a counter by 1 (if not below 0 or another limit)
- *(Optionally handled in simulation logic)*: auto-updates via `rate_value`

---

## 🛠️ Actions

### ➕ `increase-counter`

<pre>(:action increase-counter
  :parameters (?c - counter)
  :precondition (< (value ?c) max_int)
  :effect (increase (value ?c) 1)
)</pre>

### Description:
Increases the counter's value by 1, if it has not yet reached max_int.

### ➖ decrease-counter
<pre>(:action decrease-counter
  :parameters (?c - counter)
  :precondition (> (value ?c) 0)
  :effect (decrease (value ?c) 1)
)</pre>

### Description:
Decreases the counter's value by 1, only if the current value is greater than 0.

---
## 🔁 Auto-update Mechanism (by rate_value)
In FO-Counters, each counter is also affected by its rate_value. At every simulation step, the value is increased by its rate:
<pre>value(c) ← value(c) + rate_value(c)</pre>
This behavior may be implemented explicitly as an action or handled automatically in the environment/simulator.

---
## 🔍 What the Planner Tries to Do
Given an initial state (with values and rate values) and a set of numeric constraints (goals), the planner must:

- Choose a sequence of actions (increase / decrease)

- Let rate effects evolve over time

- Ensure all goals are satisfied (e.g., c0 + 1 ≤ c1)

The plan must also respect domain constraints such as:

- Staying within [0, max_int] bounds

- Applying actions only when preconditions are met

---
## 🧪 Example Use Cases
- Time-based simulations: Where values naturally grow or decay over time.

- Flow modeling: Like battery charging, water levels, or temperature increases.

- System dynamics: Modeling systems with continuous evolution and discrete decisions.
---
## 🎒 Extras
This domain pairs well with:

- Temporal/numeric planners

- Simulation-driven planning

- Hybrid logic & constraint solvers


