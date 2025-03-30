;; Domain: zenotravel (extended to include total-time)
;; Changes documented:
;; 1. Added new functions: total-time, slow-speed, and fast-speed.
;; 2. Updated fly-slow and fly-fast actions to include time calculation.
(define (domain zenotravel)
  (:requirements :typing :fluents)
  
  ;; Types: locatable, city, aircraft, and person.
  (:types locatable city - object
          aircraft person - locatable)
  
  ;; Predicates: location of objects and whether a person is in an aircraft.
  (:predicates 
    (located ?x - locatable ?c - city)
    (in ?p - person ?a - aircraft))
  
  ;; Functions:
  ;; - fuel: current fuel level of an aircraft.
  ;; - distance: the distance between two cities.
  ;; - slow-burn / fast-burn: fuel consumption rates.
  ;; - capacity: fuel capacity of an aircraft.
  ;; - total-fuel-used: cumulative fuel consumption.
  ;; - total-time: cumulative travel time (new function).
  ;; - onboard: number of passengers currently in an aircraft.
  ;; - zoom-limit: maximum allowed passengers for fast flight.
  ;; - slow-speed / fast-speed: speeds during slow and fast flights (new functions).
  (:functions 
    (fuel ?a - aircraft)
    (distance ?c1 - city ?c2 - city)
    (slow-burn ?a - aircraft)
    (fast-burn ?a - aircraft)
    (capacity ?a - aircraft)
    (total-time)         ;; NEW: tracks the total travel time.
    (onboard ?a - aircraft)
    (zoom-limit ?a - aircraft)
    (slow-speed ?a - aircraft)  ;; NEW: speed during slow flight.
    (fast-speed ?a - aircraft)) ;; NEW: speed during fast flight.
  
  ;; Action: board a person onto an aircraft.
  (:action board
    :parameters (?p - person ?a - aircraft ?c - city)
    :precondition (and 
                    (located ?p ?c)
                    (located ?a ?c))
    :effect (and 
              (not (located ?p ?c))
              (in ?p ?a)
              (increase (onboard ?a) 1)))
  
  ;; Action: debark a person from an aircraft.
  (:action debark
    :parameters (?p - person ?a - aircraft ?c - city)
    :precondition (and 
                    (in ?p ?a)
                    (located ?a ?c))
    :effect (and 
              (not (in ?p ?a))
              (located ?p ?c)
              (decrease (onboard ?a) 1)))
  
  ;; Action: fly-slow updates aircraft position, fuel, and now total-time.
  (:action fly-slow
    :parameters (?a - aircraft ?c1 ?c2 - city)
    :precondition (and 
                    (located ?a ?c1)
                    (>= (fuel ?a) (* (distance ?c1 ?c2) (slow-burn ?a))))
    :effect (and 
              (not (located ?a ?c1))
              (located ?a ?c2)
              (decrease (fuel ?a) (* (distance ?c1 ?c2) (slow-burn ?a)))
              ;; NEW: Increase total-time by flight duration: distance divided by slow-speed.
              (increase (total-time) (/ (distance ?c1 ?c2) (slow-speed ?a)))))
  
  ;; Action: fly-fast updates aircraft position, fuel, and total-time.
  (:action fly-fast
    :parameters (?a - aircraft ?c1 ?c2 - city)
    :precondition (and 
                    (located ?a ?c1)
                    (>= (fuel ?a) (* (distance ?c1 ?c2) (fast-burn ?a)))
                    (<= (onboard ?a) (zoom-limit ?a)))
    :effect (and 
              (not (located ?a ?c1))
              (located ?a ?c2)
              (decrease (fuel ?a) (* (distance ?c1 ?c2) (fast-burn ?a)))
              ;; NEW: Increase total-time by flight duration: distance divided by fast-speed.
              (increase (total-time) (/ (distance ?c1 ?c2) (fast-speed ?a)))))
  
  ;; Action: refuel replenishes fuel up to aircraft's capacity.
  (:action refuel	
    :parameters (?a - aircraft)
    :precondition (and (> (capacity ?a) (fuel ?a)))
    :effect (assign (fuel ?a) (capacity ?a))))
