# 🧱 MT-Block-Grouping Domain (PDDL)

The **MT-Block-Grouping Domain** models a grid-based environment with movable blocks of different colors. The goal is to **group all blocks of the same color into the same grid cell**, while ensuring that **blocks of different colors do not share a cell**.

This domain is designed to test numeric spatial reasoning and coordination, and is particularly relevant for multi-object manipulation, robotic planning, and resource organization.

---

## 📂 Domain Overview

### Objects

- **Blocks**: Each `block` object has:
  - `x` and `y` coordinates representing its current grid position.

---

### 🔍 Domain Type: Restricted Numeric Task (RT)

This domain allows numeric preconditions with simple arithmetic expressions (e.g., `(+ (x ?b) 1)`), but only uses constant updates in effects.  
This makes it more expressive than SNT, but not as complex as LT.

---

## ⚙️ Domain Mechanics

### Functions

- `(x ?b - block)` — The horizontal position of block `?b`.
- `(y ?b - block)` — The vertical position of block `?b`.
- `(max_x)` / `(min_x)` — Upper and lower bounds for x-axis.
- `(max_y)` / `(min_y)` — Upper and lower bounds for y-axis.

These numeric fluents define the grid space and enforce bounds for block movement.

---

## 🛠️ Actions

The domain defines **four movement actions**, allowing each block to move within the grid, respecting bounds:

---

### ⬆️ `move_block_up`
<pre>(:action move_block_up
  :parameters (?b - block)
  :precondition (<= (+ (y ?b) 1) (max_y))
  :effect (increase (y ?b) 1)
)</pre>

**Description**: Increases the vertical position of the block by 1 (if within bounds).

---

### ⬇️ `move_block_down`
<pre>(:action move_block_down
  :parameters (?b - block)
  :precondition (>= (- (y ?b) 1) (min_y))
  :effect (decrease (y ?b) 1)
)</pre>

**Description**: Decreases the vertical position of the block by 1.

---

### ➡️ `move_block_right`
<pre>(:action move_block_right
  :parameters (?b - block)
  :precondition (<= (+ (x ?b) 1) (max_x))
  :effect (increase (x ?b) 1)
)</pre>

**Description**: Moves the block to the right by increasing its `x` coordinate.

---

### ⬅️ `move_block_left`
<pre>(:action move_block_left
  :parameters (?b - block)
  :precondition (>= (- (x ?b) 1) (min_x))
  :effect (decrease (x ?b) 1)
)</pre>

**Description**: Moves the block to the left by decreasing its `x` coordinate.

---

## 🎯 Goal Semantics

The main objective is to **group all blocks of the same color in the same cell**:

- Blocks with the same color → must have the same `(x, y)` position.
- Blocks of different colors → must be in **distinct cells**.

This creates a **group-by-color** clustering challenge within a bounded numeric space.


---

## 🧾 Example

Suppose we have three blocks:

- `b1` and `b2` are **red**
- `b3` is **blue**

Initial state:
- `b1` at (1,1)
- `b2` at (2,1)
- `b3` at (3,3)

Goal:
- Move `b1` and `b2` to the **same location**, e.g., (2,2)
- Ensure `b3` is in a **different location**, e.g., (0,0)

This satisfies the requirement that blocks of the same color share a cell, and different colors do not.


## 🔍 What the Planner Tries to Do

Given:

- Initial positions of all blocks
- A color mapping (defined in the problem file)
- Grid boundaries (`min_x`, `max_x`, etc.)

The planner must:

- Move blocks via the defined actions
- Ensure correct spatial grouping by color
- Avoid placing different-colored blocks in the same location

---

## 🧪 Example Use Cases

- Object sorting tasks in robotics
- Color-coded resource binning
- Warehouse grid optimization
- Logistics and multi-agent coordination problems

---

## 🎒 Extras

This domain is especially interesting for:

- **Numeric planners** with fluent tracking
- **Group formation tasks** in grid spaces
- **Spatial reasoning** with local movement constraints
