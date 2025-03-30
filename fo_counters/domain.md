# 🔄 FO-Counters Domain (PDDL)

The **FO-Counters Domain** is an extension of the basic Counters domain, where each counter is not only manually adjustable but also **automatically influenced over time** by its `rate_value`. This simulates continuous or dynamic systems where counters evolve with each time step.

---

## 🧠 Motivation

This domain is designed to model and study **forward-propagating effects**, where the values of variables (counters) naturally change over time. This makes it suitable for simulating time-dependent systems, energy flow, temperature change, or any dynamic value progression.

---

## 📂 Domain Structure

### Counters

Each counter includes:
- `value`: the current state of the counter.
- `rate_value`: the amount by which the counter's value increases each time step.

Example:
```lisp
(= (value c0) 3)
(= (rate_value c0) 2) ; Automatically adds 2 every step
