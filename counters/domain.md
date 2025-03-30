# 🧮 Counters Domain (PDDL)

The **Counters Domain** is a simple numeric planning domain designed to explore planning over linear integer variables (counters). Each counter has a value and can be increased or decreased under certain constraints.

This domain is often used to evaluate search strategies and heuristics in numeric planning, due to its clarity and control.

---

## 📂 Domain Overview

### Objects

- **Counters**: Each counter (e.g., `c0`, `c1`, etc.) represents a numeric variable with:
  - `value`: current integer value
  - Optionally in `fo_counter`: `rate_value`: a per-step increment (like a derivative)

---

## ⚙️ Domain Mechanics

### Predicates

- `(value ?c - counter)` — The current value of counter `?c`.
- `(rate_value ?c - counter)` *(in extended domains like `fo_counter`)* — The rate of change per step.

---

### Functions

- `increase-counter`: Increases the value of a counter by 1 (if not above `max_value`)
- `decrease-counter`: Decreases the value of a counter by 1 (if not below 0 or another limit)

---

### ⚙️ Actions

#### ➕ `increase-counter`

<pre>  (:action increase-counter :parameters (?c - counter) :precondition (< (value ?c) max_int) :effect (increase (value ?c) 1) ) (:action decrease-counter :parameters (?c - counter) :precondition (> (value ?c) 0) :effect (decrease (value ?c) 1) )  </pre>

<pre>
(:action decrease-counter
  :parameters (?c - counter)
  :precondition (> (value ?c) 0)
  :effect (decrease (value ?c) 1)
) </pre>


#### Description:
Increases the counter's value by 1, only if it's below the maximum allowed (max_int).

#### ➖ decrease-counter

<pre> 
  (:action decrease-counter
  :parameters (?c - counter)
  :precondition (> (value ?c) 0)
  :effect (decrease (value ?c) 1)
)
</pre>

#### Description:
Decreases the counter's value by 1, only if it's greater than 0.

---

### 🔍 What the Planner Tries to Do

Given an initial state (counter values) and a set of **numeric constraints** (goals), the planner must:

- Choose a sequence of actions (`increase` / `decrease`)
- Move from the initial values to a new state
- Ensure all goals are satisfied (e.g., `c0 + 1 ≤ c1`)

The plan should also respect domain limits, such as:

- Staying within `[0, max_int]` bounds
- Applying actions only when preconditions are met

---

### 🧪 Example Use Cases

- **Simple scheduling**: Ensuring one task happens after another by modeling task order as counter constraints.
- **Resource balancing**: Adjusting quantities like fuel or energy while respecting system limits.
- **Numeric puzzles**: Designing games or tests based on reaching certain number configurations.

---

### 🎒 Extras

This domain pairs well with:

- Linear constraint solvers
- Heuristic planners
- Educational tools for planning logic




