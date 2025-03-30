# Zenotravel Domain - Fuel Optimization

## Overview
The **Zenotravel domain** models a transportation system where **people board aircraft, travel between cities, and consume fuel**.  
The original domain was introduced in **IPC-2002** and has been adapted for better efficiency in fuel consumption.

## Key Issue: Linear Metric Problems
- The **original domain structure** creates **linear metric inconsistencies** that can cause **suboptimal or infeasible plans**.
- To **mitigate this issue**, the focus is on **fuel consumption adjustments**.

## Fuel Mechanics
Fuel is a critical resource, and **aircraft consume fuel based on their travel speed**.  
Each aircraft has:
- **`fuel(?a - aircraft)`** → Current fuel level.
- **`capacity(?a - aircraft)`** → Maximum fuel capacity.
- **`total-fuel-used`** → Tracks overall fuel consumption.
- **`slow-burn(?a - aircraft)`** → Fuel burned per distance unit in slow travel.
- **`fast-burn(?a - aircraft)`** → Fuel burned per distance unit in fast travel.

## Optimization Strategy
### 1. Ensuring **Fast Travel is More Efficient**
To achieve **better domain performance**, **`fast-burn` must be lower than `slow-burn`**, meaning:
**fast-burn(a) < slow-burn(a)**
This ensures:
- **Fast travel is preferable** when fuel efficiency is required.
- The planner will **choose the right travel mode** based on constraints.

### 2. Fuel Consumption Adjustments
#### **Refueling (`refuel`)**
- Restores aircraft fuel to full capacity.

#### **Flight Actions**
- **Fly-Slow (`fly-slow`)**:  
  - Uses **`slow-burn`** to determine fuel usage.
  - Moves an aircraft while consuming more fuel.
  
- **Fly-Fast (`fly-fast`)**:  
  - Uses **`fast-burn`** (which must be **lower than `slow-burn`**).
  - **Zoom-limit** restricts fast travel to a limited number of passengers.

## Summary
This adaptation of **Zenotravel** improves **fuel efficiency** by ensuring that:
- **`fast-burn` is always lower than `slow-burn`** for optimal planning.
- The planner **prefers fuel-efficient routes** while maintaining constraints.
- Refueling, boarding, and debarking remain **unaffected** but support **better energy management**.

By making **fast travel more fuel-efficient**, the domain now produces **more optimal plans** and resolves **metric inconsistencies**.
