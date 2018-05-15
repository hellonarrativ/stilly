STILLY

Stilly is designed to be an actor based system with the goal of building
stateful distributed applications. It will expose a class that can be 
instantiated to build the system, and that system object can start and supervise
multiple actor processes and handle communication between them.

System

A system object is the fundamental unit of a stilly application. When you start
the system it will create a mailbox for itself to accept messages. The system
will always create a control actor. The system will have two addresses-
`/local/` and a `/proc_name/`- this will allow multiple distributed systems
to communicate between each other by using the actual name, and even actors in a
system to communicate with a specific actor living on another system.

Control

There are two types of Control actors. The default is a master controller. A
master controller will accept messages to start actors. If you intend to network
multiple systems together, instead the controller will start a raft actor, which
will allow multiple systems to elect a leader. There will only be one master
controller at that point, and it will send messages to start actors on other
systems. `/local/master` will be redirected to the current master controller-
even if that controller is not on the `/local/` system.