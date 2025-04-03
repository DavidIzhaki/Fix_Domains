# 🤖 Delivery Domain (PDDL)

The **Delivery Domain** represents a logistics-inspired environment where autonomous robots with multiple arms and trays move items between rooms. Each item has a numeric weight, and each robot has a weight-carrying capacity.

This domain models **capacity-aware object handling**, useful for evaluating numeric planning strategies, such as managing constraints and resource balancing over multiple agents.

---

## 📂 Domain Overview

### Objects

- **Bots**: Robots that navigate and manipulate items.
- **Arms**: Mounted manipulators on each bot.
- **Items**: Have weight and must be picked/delivered.
- **Rooms**: Represent a networked space with doors.

---

## ⚙️ Domain Mechanics

### Predicates

- `(at-bot ?b ?x)` — Bot `?b` is in room `?x`.
- `(at ?i ?x)` — Item `?i` is in room `?x`.
- `(door ?x ?y)` — Room `?x` is connected to `?y`.
- `(free ?a)` — Arm `?a` is currently free.
- `(in-arm ?i ?a)` — Item `?i` is held by arm `?a`.
- `(in-tray ?i ?b)` — Item `?i` is in the tray of bot `?b`.
- `(mount ?a ?b)` — Arm `?a` is mounted on bot `?b`.

---

### Functions

- `(load_limit ?b)` — Maximum capacity a bot can carry.
- `(current_load ?b)` — The current total weight the bot carries.
- `(weight ?i)` — The weight of item `?i`.
- `(cost)` — The accumulated cost of actions taken.

---

### ⚙️ Actions

#### 🚶 `move`

<pre>
(:action move
 :parameters (?b - bot ?x - room ?y - room)
 :precondition (and (at-bot ?b ?x) (door ?x ?y))
 :effect (and
   (at-bot ?b ?y)
   (not (at-bot ?b ?x))
   (increase (cost) 3)))
</pre>

#### Description:
Moves a bot from room `?x` to `?y` if a door connects them.

---

#### 🤲 `pick`

<pre>
(:action pick
 :parameters (?i - item ?x - room ?a - arm ?b - bot)
 :precondition (and
   (at ?i ?x)
   (at-bot ?b ?x)
   (free ?a)
   (mount ?a ?b)
   (<= (+ (current_load ?b) (weight ?i)) (load_limit ?b)))
 :effect (and
   (in-arm ?i ?a)
   (not (at ?i ?x))
   (not (free ?a))
   (increase (current_load ?b) (weight ?i))
   (increase (cost) 2)))
</pre>

#### Description:
Picks an item with an available arm, if within the bot's remaining capacity.

---

#### 📤 `drop`

<pre>
(:action drop
 :parameters (?i - item ?x - room ?a - arm ?b - bot)
 :precondition (and
   (in-arm ?i ?a)
   (at-bot ?b ?x)
   (mount ?a ?b))
 :effect (and
   (free ?a)
   (at ?i ?x)
   (not (in-arm ?i ?a))
   (decrease (current_load ?b) (weight ?i))
   (increase (cost) 2)))
</pre>

#### Description:
Drops an item at the current room, freeing the arm and reducing the load.

---

#### 📥 `to-tray`

<pre>
(:action to-tray
 :parameters (?i - item ?a - arm ?b - bot)
 :precondition (and (in-arm ?i ?a) (mount ?a ?b))
 :effect (and
   (free ?a)
   (not (in-arm ?i ?a))
   (in-tray ?i ?b)
   (increase (cost) 1)))
</pre>

#### Description:
Transfers an item from an arm to the tray of the same bot.

---

#### 🖐️ `from-tray`

<pre>
(:action from-tray
 :parameters (?i - item ?a - arm ?b - bot)
 :precondition (and (in-tray ?i ?b) (mount ?a ?b) (free ?a))
 :effect (and
   (not (free ?a))
   (in-arm ?i ?a)
   (not (in-tray ?i ?b))
   (increase (cost) 1)))
</pre>

#### Description:
Loads an item from the tray into a free arm.

---

## 🧮 Domain Type: Restricted Numeric Task (RT)

This domain includes numeric constraints using arithmetic in **preconditions**, like:

```lisp
(<= (+ (current_load ?b) (weight ?i)) (load_limit ?b))

```

However, effects only include constant `increase` / `decrease` operations on numeric fluents, and do not involve general linear updates.

This makes it a **Restricted Numeric Task (RT)** — more expressive than SNT, but simpler than LT.

---

## 🔍 What the Planner Tries to Do

The planner must:

- Navigate robots across a room network  
- Assign arms and trays to items efficiently  
- Obey numeric load constraints (`current_load ≤ load_limit`)  
- Deliver items to their goal positions  
- Minimize total action cost

---

## 🧾 Example

Suppose:

- Robot `b1` has two arms: `a1`, `a2`  
- Items: `i1` (weight 2), `i2` (weight 1)  
- Rooms: `r1`, `r2` connected via a door  

**Initial state:**

- `b1` is in `r1`, both items in `r1`, arms are free  
- `load_limit(b1) = 3`, `current_load(b1) = 0`

**Goal:**

- Deliver both items to `r2`  
- Use arms/tray to obey the weight limit and minimize cost

---

## 🧪 Example Use Cases

- Warehouse and delivery robotics  
- Inventory management with robot arms  
- Smart logistics under resource constraints  
- Planning with pickup-and-drop operations

---

## 🎒 Extras

This domain is especially useful for:

- Testing numeric planning with simple capacity models  
- Evaluating multi-step manipulation under resource limits  
- Benchmarking cost-aware planning strategies
