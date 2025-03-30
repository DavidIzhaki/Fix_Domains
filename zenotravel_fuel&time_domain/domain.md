# Zenotravel Domain (Extended Version)

This document describes the **Zenotravel domain**, extended to include **total-time tracking** for flight durations. Originally developed for the IPC-2002



## Overview

The **Zenotravel domain** models air travel with constraints on **fuel consumption** and **passenger capacity**. In this extended version, new **functions** and **actions** have been added to track **flight durations**, enabling more detailed planning and optimization.



## Key Features & Changes

### 1. New Functions
To account for flight duration, the following functions were added:

- **`total-time`** → Tracks the total cumulative travel time.
- **`slow-speed`** → Defines the speed of an aircraft during slow flights.
- **`fast-speed`** → Defines the speed of an aircraft during fast flights.

### 2. Updated Actions

#### **Fly-Slow (`fly-slow`)**
- Moves an aircraft from one city to another.
- Consumes fuel based on the `slow-burn` rate.
- **NEW**: Increases `total-time` based on the distance and `slow-speed`.

#### **Fly-Fast (`fly-fast`)**
- Moves an aircraft from one city to another.
- Consumes fuel based on the `fast-burn` rate.
- **NEW**: Increases `total-time` based on the distance and `fast-speed`.
- Restricted by the `zoom-limit` (passenger capacity for fast travel).



## Predicates
These define the state of the world:

- **`located(?x - locatable, ?c - city)`** → Defines the location of an object.
- **`in(?p - person, ?a - aircraft)`** → Indicates that a person is inside an aircraft.



## Functions
These numerical functions track fuel levels, distances, and time:

- **`fuel(?a - aircraft)`** → Current fuel level of an aircraft.
- **`distance(?c1 - city, ?c2 - city)`** → Distance between two cities.
- **`slow-burn(?a - aircraft)`** → Fuel consumption rate during slow flights.
- **`fast-burn(?a - aircraft)`** → Fuel consumption rate during fast flights.
- **`capacity(?a - aircraft)`** → Maximum fuel capacity.
- **`total-fuel-used`** → Tracks total fuel consumption.
- **`total-time`** → **(New!)** Tracks cumulative travel time.
- **`onboard(?a - aircraft)`** → Number of passengers in an aircraft.
- **`zoom-limit(?a - aircraft)`** → Maximum passengers allowed for fast flights.
- **`slow-speed(?a - aircraft)`** → **(New!)** Speed of an aircraft during slow flights.
- **`fast-speed(?a - aircraft)`** → **(New!)** Speed of an aircraft during fast flights.



## Actions

### 1. Boarding & Debarking
- **Board (`board`)** → A person enters an aircraft.
- **Debark (`debark`)** → A person exits an aircraft.

### 2. Flight Actions

#### **Fly-Slow (`fly-slow`)**
- Moves an aircraft between cities.
- Consumes fuel based on `slow-burn`.
- **NEW**: Updates `total-time` based on `slow-speed`.

#### **Fly-Fast (`fly-fast`)**
- Moves an aircraft between cities.
- Consumes fuel based on `fast-burn`.
- **NEW**: Updates `total-time` based on `fast-speed`.
- Restricted by `zoom-limit` (passenger capacity).

### 3. Refueling
- **Refuel (`refuel`)** → Restores fuel to an aircraft's capacity.


## Summary
This extended **Zenotravel domain** introduces **total-time tracking** for flights, allowing for more realistic travel planning. By differentiating between **slow and fast flights** with corresponding speeds, the domain now enables **time-aware decision-making** in automated planning.
