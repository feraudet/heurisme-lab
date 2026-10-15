# Restarting a node of the production database

## 1. Before you start

This procedure applies to the production PostgreSQL cluster, made of one primary node and two replicas. It does not apply to the staging environment, which has a single node.

First check that no backup is running. An interrupted backup must be restarted from scratch, which takes about four hours. Full backups start every night at two o'clock and usually finish before six.

Then check that both replicas are up to date. The replication lag shown on the dashboard must be under ten seconds. If it goes over one minute, do not restart anything: the cause of the lag must be understood first.

Warn the team on the incident channel before any action, with the node concerned and the planned time of the restart.

## 2. Restarting a replica

A replica can be restarted at any time, provided the other replica is healthy. First remove the replica from the read load balancing, wait for the open connections to finish, then restart the service.

After the restart, the replica catches up on its own. Put it back into the load balancing only when its lag is back under ten seconds.

## 3. Restarting the primary

The primary is never restarted directly. You must fail over first: promote an up-to-date replica to new primary, check that the applications do write to it, then restart the old primary, which comes back as a replica.

During the failover, writes are refused for a few seconds. Applications must retry automatically; if an application returns errors more than two minutes after the failover, warn its team.

## 4. If it fails

If the service does not restart, read the node's logs before any new attempt. The most common errors are a full disk and a configuration file edited by hand. Never delete files in the data directory to free up space: escalate to level 2.
