(define (problem zenotravel-problem-5)
  (:domain zenotravel)
  (:objects
    plane1 - aircraft
    plane2 - aircraft
    person1 - person
    person2 - person
    person3 - person
    person4 - person
    city0 - city
    city1 - city
    city2 - city
    city3 - city)
  (:init
    (located plane1 city1)
    (= (capacity plane1) 2990)
    (= (fuel plane1) 174)
    (= (slow-burn plane1) 1)
    (= (fast-burn plane1) 3)
    (= (onboard plane1) 0)
    (= (zoom-limit plane1) 3)
    ;; NEW: Define speeds for plane1
    (= (slow-speed plane1) 300)
    (= (fast-speed plane1) 600)
    
    (located plane2 city2)
    (= (capacity plane2) 4839)
    (= (fuel plane2) 1617)
    (= (slow-burn plane2) 2)
    (= (fast-burn plane2) 5)
    (= (onboard plane2) 0)
    (= (zoom-limit plane2) 5)
    ;; NEW: Define speeds for plane2
    (= (slow-speed plane2) 250)
    (= (fast-speed plane2) 500)
    
    (located person1 city3)
    (located person2 city0)
    (located person3 city0)
    (located person4 city1)
    (= (distance city0 city0) 0)
    (= (distance city0 city1) 569)
    (= (distance city0 city2) 607)
    (= (distance city0 city3) 754)
    (= (distance city1 city0) 569)
    (= (distance city1 city1) 0)
    (= (distance city1 city2) 504)
    (= (distance city1 city3) 557)
    (= (distance city2 city0) 607)
    (= (distance city2 city1) 504)
    (= (distance city2 city2) 0)
    (= (distance city2 city3) 660)
    (= (distance city3 city0) 754)
    (= (distance city3 city1) 557)
    (= (distance city3 city2) 660)
    (= (distance city3 city3) 0)
    (= (total-time) 0)      ;; NEW: initialize total time
  )
  (:goal (and
           (located person1 city2)
           (located person2 city3)
           (located person3 city3)
           (located person4 city3)))
  (:metric minimize (total-time)))