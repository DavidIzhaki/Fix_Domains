# 🛷 Expedition Domain (PDDL)

The **Expedition Domain** simulates a scenario where sleds navigate through a series of waypoints to reach a destination. This domain is useful for studying path planning, resource management, and multi-agent coordination, as sleds must manage their supplies to traverse the route effectively.

---

## 📂 Domain Overview

### Objects

- **Sleds**: Vehicles that must reach the end of a series of waypoints.
- **Waypoints**: Points along the route where sleds can pick up or deposit supplies.

---

## 🧮 Domain Type: Linear Task (LT)

This domain involves:
- **Arithmetic operations** in action preconditions and effects.
- **Resource management** using linear expressions to check and update the supply levels.

---

## ⚙️ Domain Mechanics

### Predicates

- **`(at ?s - sled ?w - waypoint)`** — Checks if a sled `?s` is at waypoint `?w`.
- **`(is_next ?x - waypoint ?y - waypoint)`** — Determines if waypoint `?y` is the next destination after waypoint `?x`.

### Functions

- **`(sled_supplies ?s - sled)`** — Returns the number of supplies currently on sled `?s`.
- **`(sled_capacity ?s - sled)`** — Returns the maximum capacity of supplies that sled `?s` can carry.
- **`(waypoint_supplies ?w - waypoint)`** — Returns the number of supplies available at waypoint `?w`.

### Actions

#### ➡️ `move_forwards`
<pre>
(:action move_forwards
  :parameters (?s - sled ?w1 ?w2 - waypoint)
  :precondition (and (at ?s ?w1) (>= (sled_supplies ?s) 1) (is_next ?w1 ?w2))
  :effect (and (not (at ?s ?w1)) (at ?s ?w2) (decrease (sled_supplies ?s) 1)))
</pre>

---

#### ⬅️ `move_backwards`
<pre>
(:action move_backwards
  :parameters (?s - sled ?w1 ?w2 - waypoint)
  :precondition (and (at ?s ?w1) (>= (sled_supplies ?s) 1) (is_next ?w2 ?w1))
  :effect (and (not (at ?s ?w1)) (at ?s ?w2) (decrease (sled_supplies ?s) 1)))
</pre>

---

#### 📥 `store_supplies`
<pre>
(:action store_supplies
  :parameters (?s - sled ?w - waypoint)
  :precondition (and (at ?s ?w) (>= (sled_supplies ?s) 1))
  :effect (and (increase (waypoint_supplies ?w) 1) (decrease (sled_supplies ?s) 1)))
</pre>

---

#### 📤 `retrieve_supplies`
<pre>
(:action retrieve_supplies
  :parameters (?s - sled ?w - waypoint)
  :precondition (and (at ?s ?w) (>= (waypoint_supplies ?w) 1) (> (sled_capacity ?s) (sled_supplies ?s)))
  :effect (and (decrease (waypoint_supplies ?w) 1) (increase (sled_supplies ?s) 1)))
</pre>

---

## 🔍 What the Planner Tries to Do

Given:

- A set of waypoints each sled must navigate
- Initial supplies and capacities for each sled

The planner must:

- Efficiently manage and distribute supplies
- Ensure all sleds reach their final destination

---

## 🧾 Example

Imagine a simple setup with two sleds and three waypoints. Each sled starts with minimal supplies:

**Initial state**:
- Both sleds are at the first waypoint with limited supplies.
- Supplies are abundant at the starting waypoint.

**Goal**:
- Both sleds reach the last waypoint using the least amount of supplies, possibly retrieving more along the way.

---

## 🧪 Example Use Cases

- Resource management in logistics
- Path planning with constraints
- Cooperative strategies in multi-agent systems

---

## 🎒 Extras

This domain is ideal for:

- Studies in cooperative multi-agent systems
- Testing resource allocation algorithms
- Developing strategies for logistics optimization
