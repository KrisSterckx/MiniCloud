MiniCloud
=========

MiniCloud is a lightweight Cloud orchestrator.

Use
===

MiniCloud is a lightweight orchestrator for managing multiple Cloud managers.

It defines an object model consisting of :
* Clouds :
  A Cloud currently refers to an OpenStack deployment. Multiple Clouds can be set up.
  Optionally, Clouds can be subdivided in Clusters.
* Routers :
  A Router connects multiple Networks and can provide Public IPs with NAT support.
* Networks :
  A Network is a virtual (overlay) network connecting multiple VM Instances, optionally attached to a Router.
* Instances :
  An Instance is a virtual machine, of a specified Image and Flavor, created within a certain Cloud (or Cluster in that Cloud) and attached to a Network.
  Support for remotely connecting to an Instance is provided, in which case a Public IP is assigned if applicable.
  Security Group creation to enable remote connect is automated.

MiniCloud builds an efficient object model in memory cache, in order to speed up operations and reduce remote API calls as much as possible.

MiniCloud today supports two types of Clouds : OpenStack and Stub (for local testing). CloudStack is in the pipeline.

MiniCloud is pure command-line at current stage, but is set up to easily extend to other client architectures.

Its menu looks like :

<pre>
[ MiniCloud ]
[1] : Cloud deployment topology
[2] : Cloud management
[3] : Router management
[4] : Network management
[5] : Instance management
[6] : Reset to startup
[7] : Destroy all data
[8] : Exit (keep data)
Make a choice : [1] _
</pre>

and is presenting deployment topologies like :

<pre>
      MiniCloud
      |
      +---Compute
      |   |
      |   +---Cloud: TryStack (trystack.org)
      |       |
      |       +---Cluster: Antwerp
      |       |   |
      |       |   +---Instance: Bourla [10.10.1.12] (AntwerpNet) [default] [ACTIVE]
      |       |
      |       +---Cluster: London
      |           |
      |           +---Instance: Tower [10.10.2.5] (LondonNet) [public_ssh] [8.21.28.30] [ACTIVE]
      |           +---Instance: Ben [10.10.2.6] (LondonNet) [default] [ACTIVE]
      |
      +---Networking
          |
          +---Router: LondonGateway (external)
          |   |
          |   +---Network: LondonNet [10.10.2.0/24] (2 instances)
          |   +---Network: external (external) [trystack]
          |
          +---Network: AntwerpNet [10.10.1.0/24] (1 instance)
</pre>

Instance 'Tower' in this example has a private IP in 'LondonNet' as 10.10.2.5, but has a Public IP in 'external'
network as 8.21.28.30, NAT'ed by router 'LondonRouter'.

Disclaimer
==========

This project is built for fun and comes at no warranty.

How it's built
==============

MiniCloud uses the official OpenStack clients and MySQL for data storage, using dataset.

... Enjoy!
