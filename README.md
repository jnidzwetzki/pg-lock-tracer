# Lock tracing tools for PostgreSQL
[![Make a PR](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Build Status](https://github.com/jnidzwetzki/pg-lock-tracer/actions/workflows/tests.yml/badge.svg)](https://github.com/jnidzwetzki/pg-lock-tracer/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/pg-lock-tracer?color=green)](https://pypi.org/project/pg-lock-tracer/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pg-lock-tracer)](https://pypi.org/project/pg-lock-tracer/)
[![Release date](https://img.shields.io/github/release-date/jnidzwetzki/pg-lock-tracer)](https://github.com/jnidzwetzki/pg-lock-tracer/)
[![GitHub Repo stars](https://img.shields.io/github/stars/jnidzwetzki/pg-lock-tracer?style=social)](https://github.com/jnidzwetzki/pg-lock-tracer/)

This project provides tools that allow you to gain deep insights into PostgreSQL's locking activities and troubleshoot locking-related issues (e.g., performance problems or deadlocks).

* `pg_lock_tracer` - is a PostgreSQL table level lock tracer.
* `pg_lw_lock_tracer` - is a tracer for PostgreSQL lightweight locks (LWLocks).
* `pg_row_lock_tracer` - is a tracer for PostgreSQL row locks.
* `animate_lock_graph` - creates animated locks graphs based on the `pg_lock_tracer` output.

__Note:__ These tools employ the [eBPF](https://ebpf.io/) (_Extended Berkeley Packet Filter_) technology. At the moment, PostgreSQL 12, 13, 14, 15, and 16 are supported (see additional information below).

# pg_lock_tracer
`pg_lock_tracer` observes the locking activity of a running PostgreSQL process (using _eBPF_ and _UProbes_). In contrast to the information that is present in the table `pg_locks` (which provides information about which locks are _currently_ requested), `pg_lock_tracer` gives you a continuous view of the locking activity and collects statistics and timings.

The tracer also allows dumping the output as JSON formatted lines, which allows further processing with additional tools. This repository also contains the script `animate_lock_graph`, which provides an animated version of the taken looks.

## Usage Examples
```
# Trace use binary '/home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres' for tracing
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres

# Trace use binary '/home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres' for tracing and trace pid 1234
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234

# Trace two PIDs
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -p 5678

# Be verbose
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -v 

# Use the given db connection to access the catalog of PID 1234 to resolve OIDs
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -r 1234:psql://jan@localhost/test2

# Output in JSON format
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -j

# Print stacktrace on deadlock
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -s DEADLOCK

# Print stacktrace for locks and deadlocks
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -s LOCK DEADLOCK

# Trace only Transaction and Query related events
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -t TRANSACTION QUERY

# Write the output into file 'trace'
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -o trace

# Show statistics about locks
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 --statistics

# Create an animated lock graph (with Oids)
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -j -o locks.json
animate_lock_graph -i lock -o locks.html

# Create an animated lock graph (with table names)
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -j -r 1234:psql://jan@localhost/test2 -o locks.json
animate_lock_graph -i lock -o locks.html
```

## Example Output

CLI: `pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_14_2_DEBUG/bin/postgres -p 327578 -r 327578:sql://jan@localhost/test2 --statistics`

SQL Query: `create table metrics(ts timestamptz NOT NULL, id int NOT NULL, value float);`

Tracer Output:

```
745064333930117 [Pid 327578] Query begin 'create table metrics(ts timestamptz NOT NULL, id int NOT NULL, value float);'
745064333965769 [Pid 327578] Transaction begin
745064334157640 [Pid 327578] Table open 3079 (pg_catalog.pg_extension) AccessShareLock
745064334176147 [Pid 327578] Lock object 3079 (pg_catalog.pg_extension) AccessShareLock
745064334204453 [Pid 327578] Lock granted (fastpath) 3079 (pg_catalog.pg_extension) AccessShareLock
745064334224361 [Pid 327578] Lock granted (local) 3079 (pg_catalog.pg_extension) AccessShareLock (Already hold local 0)
745064334243659 [Pid 327578] Lock was acquired in 67512 ns
[...]
```

<details>
  <summary>Full Output</summary>

```
===> Ready to trace queries
745064333930117 [Pid 327578] Query begin 'create table metrics(ts timestamptz NOT NULL, id int NOT NULL, value float);'
745064333965769 [Pid 327578] Transaction begin
745064334157640 [Pid 327578] Table open 3079 (pg_catalog.pg_extension) AccessShareLock
745064334176147 [Pid 327578] Lock object 3079 (pg_catalog.pg_extension) AccessShareLock
745064334204453 [Pid 327578] Lock granted (fastpath) 3079 (pg_catalog.pg_extension) AccessShareLock
745064334224361 [Pid 327578] Lock granted (local) 3079 (pg_catalog.pg_extension) AccessShareLock (Already hold local 0)
745064334243659 [Pid 327578] Lock was acquired in 67512 ns
745064334285877 [Pid 327578] Lock object 3081 (pg_catalog.pg_extension_name_index) AccessShareLock
745064334309610 [Pid 327578] Lock granted (fastpath) 3081 (pg_catalog.pg_extension_name_index) AccessShareLock
745064334328475 [Pid 327578] Lock granted (local) 3081 (pg_catalog.pg_extension_name_index) AccessShareLock (Already hold local 0)
745064334345266 [Pid 327578] Lock was acquired in 59389 ns
745064334562977 [Pid 327578] Lock ungranted (fastpath) 3081 (pg_catalog.pg_extension_name_index) AccessShareLock
745064334583578 [Pid 327578] Lock ungranted (local) 3081 (pg_catalog.pg_extension_name_index) AccessShareLock (Hold local 0)
745064334608957 [Pid 327578] Table close 3079 (pg_catalog.pg_extension) AccessShareLock
745064334631046 [Pid 327578] Lock ungranted (fastpath) 3079 (pg_catalog.pg_extension) AccessShareLock
745064334649932 [Pid 327578] Lock ungranted (local) 3079 (pg_catalog.pg_extension) AccessShareLock (Hold local 0)
745064334671897 [Pid 327578] Table open 3079 (pg_catalog.pg_extension) AccessShareLock
745064334688382 [Pid 327578] Lock object 3079 (pg_catalog.pg_extension) AccessShareLock
745064334712042 [Pid 327578] Lock granted (fastpath) 3079 (pg_catalog.pg_extension) AccessShareLock
745064334731081 [Pid 327578] Lock granted (local) 3079 (pg_catalog.pg_extension) AccessShareLock (Already hold local 0)
745064334748288 [Pid 327578] Lock was acquired in 59906 ns
745064334772367 [Pid 327578] Lock object 3081 (pg_catalog.pg_extension_name_index) AccessShareLock
745064334795943 [Pid 327578] Lock granted (fastpath) 3081 (pg_catalog.pg_extension_name_index) AccessShareLock
745064334814983 [Pid 327578] Lock granted (local) 3081 (pg_catalog.pg_extension_name_index) AccessShareLock (Already hold local 0)
745064334832570 [Pid 327578] Lock was acquired in 60203 ns
745064334953192 [Pid 327578] Lock ungranted (fastpath) 3081 (pg_catalog.pg_extension_name_index) AccessShareLock
745064334973518 [Pid 327578] Lock ungranted (local) 3081 (pg_catalog.pg_extension_name_index) AccessShareLock (Hold local 0)
745064334997936 [Pid 327578] Table close 3079 (pg_catalog.pg_extension) AccessShareLock
745064335019473 [Pid 327578] Lock ungranted (fastpath) 3079 (pg_catalog.pg_extension) AccessShareLock
745064335037880 [Pid 327578] Lock ungranted (local) 3079 (pg_catalog.pg_extension) AccessShareLock (Hold local 0)
745064335901618 [Pid 327578] Table open 1259 (pg_catalog.pg_class) AccessShareLock
745064335918354 [Pid 327578] Lock object 1259 (pg_catalog.pg_class) AccessShareLock
745064335941911 [Pid 327578] Lock granted (fastpath) 1259 (pg_catalog.pg_class) AccessShareLock
745064335960211 [Pid 327578] Lock granted (local) 1259 (pg_catalog.pg_class) AccessShareLock (Already hold local 0)
745064335976642 [Pid 327578] Lock was acquired in 58288 ns
745064335999654 [Pid 327578] Lock object 2663 (pg_catalog.pg_class_relname_nsp_index) AccessShareLock
745064336022776 [Pid 327578] Lock granted (fastpath) 2663 (pg_catalog.pg_class_relname_nsp_index) AccessShareLock
745064336040926 [Pid 327578] Lock granted (local) 2663 (pg_catalog.pg_class_relname_nsp_index) AccessShareLock (Already hold local 0)
745064336057158 [Pid 327578] Lock was acquired in 57504 ns
745064336187786 [Pid 327578] Lock ungranted (fastpath) 2663 (pg_catalog.pg_class_relname_nsp_index) AccessShareLock
745064336207011 [Pid 327578] Lock ungranted (local) 2663 (pg_catalog.pg_class_relname_nsp_index) AccessShareLock (Hold local 0)
745064336230761 [Pid 327578] Table close 1259 (pg_catalog.pg_class) AccessShareLock
745064336252413 [Pid 327578] Lock ungranted (fastpath) 1259 (pg_catalog.pg_class) AccessShareLock
745064336270811 [Pid 327578] Lock ungranted (local) 1259 (pg_catalog.pg_class) AccessShareLock (Hold local 0)
745064336314237 [Pid 327578] Lock granted 2615 (pg_catalog.pg_namespace) AccessShareLock (Requested locks 1)
745064336331450 [Pid 327578] Lock granted (local) 2615 (pg_catalog.pg_namespace) AccessShareLock (Already hold local 0)
745064336402316 [Pid 327578] Lock granted (local) 2615 (pg_catalog.pg_namespace) AccessShareLock (Already hold local 1)
745064336543618 [Pid 327578] Table open 1259 (pg_catalog.pg_class) RowExclusiveLock
745064336560502 [Pid 327578] Lock object 1259 (pg_catalog.pg_class) RowExclusiveLock
745064336584633 [Pid 327578] Lock granted (fastpath) 1259 (pg_catalog.pg_class) RowExclusiveLock
745064336602915 [Pid 327578] Lock granted (local) 1259 (pg_catalog.pg_class) RowExclusiveLock (Already hold local 0)
745064336619969 [Pid 327578] Lock was acquired in 59467 ns
745064336655328 [Pid 327578] Table open 1247 (pg_catalog.pg_type) AccessShareLock
745064336671769 [Pid 327578] Lock object 1247 (pg_catalog.pg_type) AccessShareLock
745064336696072 [Pid 327578] Lock granted (fastpath) 1247 (pg_catalog.pg_type) AccessShareLock
745064336714540 [Pid 327578] Lock granted (local) 1247 (pg_catalog.pg_type) AccessShareLock (Already hold local 0)
745064336731130 [Pid 327578] Lock was acquired in 59361 ns
745064336755221 [Pid 327578] Lock object 2704 (pg_catalog.pg_type_typname_nsp_index) AccessShareLock
745064336778586 [Pid 327578] Lock granted (fastpath) 2704 (pg_catalog.pg_type_typname_nsp_index) AccessShareLock
745064336797018 [Pid 327578] Lock granted (local) 2704 (pg_catalog.pg_type_typname_nsp_index) AccessShareLock (Already hold local 0)
745064336813397 [Pid 327578] Lock was acquired in 58176 ns
745064336932804 [Pid 327578] Lock ungranted (fastpath) 2704 (pg_catalog.pg_type_typname_nsp_index) AccessShareLock
745064336952174 [Pid 327578] Lock ungranted (local) 2704 (pg_catalog.pg_type_typname_nsp_index) AccessShareLock (Hold local 0)
745064336975237 [Pid 327578] Table close 1247 (pg_catalog.pg_type) AccessShareLock
745064336996581 [Pid 327578] Lock ungranted (fastpath) 1247 (pg_catalog.pg_type) AccessShareLock
745064337014858 [Pid 327578] Lock ungranted (local) 1247 (pg_catalog.pg_type) AccessShareLock (Hold local 0)
745064337047504 [Pid 327578] Lock object 2662 (pg_catalog.pg_class_oid_index) AccessShareLock
745064337070928 [Pid 327578] Lock granted (fastpath) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock
745064337089515 [Pid 327578] Lock granted (local) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock (Already hold local 0)
745064337106032 [Pid 327578] Lock was acquired in 58528 ns
745064337183488 [Pid 327578] Lock ungranted (fastpath) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock
745064337202563 [Pid 327578] Lock ungranted (local) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock (Hold local 0)
745064337621853 [Pid 327578] Table open 1247 (pg_catalog.pg_type) AccessShareLock
745064337638996 [Pid 327578] Lock object 1247 (pg_catalog.pg_type) AccessShareLock
745064337661950 [Pid 327578] Lock granted (fastpath) 1247 (pg_catalog.pg_type) AccessShareLock
745064337681169 [Pid 327578] Lock granted (local) 1247 (pg_catalog.pg_type) AccessShareLock (Already hold local 0)
745064337697945 [Pid 327578] Lock was acquired in 58949 ns
745064337723254 [Pid 327578] Lock object 2703 (pg_catalog.pg_type_oid_index) AccessShareLock
745064337746949 [Pid 327578] Lock granted (fastpath) 2703 (pg_catalog.pg_type_oid_index) AccessShareLock
745064337765491 [Pid 327578] Lock granted (local) 2703 (pg_catalog.pg_type_oid_index) AccessShareLock (Already hold local 0)
745064337781897 [Pid 327578] Lock was acquired in 58643 ns
745064337865717 [Pid 327578] Lock ungranted (fastpath) 2703 (pg_catalog.pg_type_oid_index) AccessShareLock
745064337885245 [Pid 327578] Lock ungranted (local) 2703 (pg_catalog.pg_type_oid_index) AccessShareLock (Hold local 0)
745064337907299 [Pid 327578] Table close 1247 (pg_catalog.pg_type) AccessShareLock
745064337928390 [Pid 327578] Lock ungranted (fastpath) 1247 (pg_catalog.pg_type) AccessShareLock
745064337946792 [Pid 327578] Lock ungranted (local) 1247 (pg_catalog.pg_type) AccessShareLock (Hold local 0)
745064337970694 [Pid 327578] Table open 1247 (pg_catalog.pg_type) RowExclusiveLock
745064337987065 [Pid 327578] Lock object 1247 (pg_catalog.pg_type) RowExclusiveLock
745064338010254 [Pid 327578] Lock granted (fastpath) 1247 (pg_catalog.pg_type) RowExclusiveLock
745064338028898 [Pid 327578] Lock granted (local) 1247 (pg_catalog.pg_type) RowExclusiveLock (Already hold local 0)
745064338045413 [Pid 327578] Lock was acquired in 58348 ns
745064338073508 [Pid 327578] Lock object 2703 (pg_catalog.pg_type_oid_index) AccessShareLock
745064338096688 [Pid 327578] Lock granted (fastpath) 2703 (pg_catalog.pg_type_oid_index) AccessShareLock
745064338114955 [Pid 327578] Lock granted (local) 2703 (pg_catalog.pg_type_oid_index) AccessShareLock (Already hold local 0)
745064338131934 [Pid 327578] Lock was acquired in 58426 ns
745064338198858 [Pid 327578] Lock ungranted (fastpath) 2703 (pg_catalog.pg_type_oid_index) AccessShareLock
745064338218267 [Pid 327578] Lock ungranted (local) 2703 (pg_catalog.pg_type_oid_index) AccessShareLock (Hold local 0)
745064338257754 [Pid 327578] Lock object 2703 (pg_catalog.pg_type_oid_index) RowExclusiveLock
745064338281754 [Pid 327578] Lock granted (fastpath) 2703 (pg_catalog.pg_type_oid_index) RowExclusiveLock
745064338300356 [Pid 327578] Lock granted (local) 2703 (pg_catalog.pg_type_oid_index) RowExclusiveLock (Already hold local 0)
745064338317100 [Pid 327578] Lock was acquired in 59346 ns
745064338343423 [Pid 327578] Lock object 2704 (pg_catalog.pg_type_typname_nsp_index) RowExclusiveLock
745064338366354 [Pid 327578] Lock granted (fastpath) 2704 (pg_catalog.pg_type_typname_nsp_index) RowExclusiveLock
745064338384776 [Pid 327578] Lock granted (local) 2704 (pg_catalog.pg_type_typname_nsp_index) RowExclusiveLock (Already hold local 0)
745064338401188 [Pid 327578] Lock was acquired in 57765 ns
745064338925851 [Pid 327578] Lock ungranted (fastpath) 2703 (pg_catalog.pg_type_oid_index) RowExclusiveLock
745064338945562 [Pid 327578] Lock ungranted (local) 2703 (pg_catalog.pg_type_oid_index) RowExclusiveLock (Hold local 0)
745064338969060 [Pid 327578] Lock ungranted (fastpath) 2704 (pg_catalog.pg_type_typname_nsp_index) RowExclusiveLock
745064338987686 [Pid 327578] Lock ungranted (local) 2704 (pg_catalog.pg_type_typname_nsp_index) RowExclusiveLock (Hold local 0)
745064339016433 [Pid 327578] Table open 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064339032833 [Pid 327578] Lock object 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064339056324 [Pid 327578] Lock granted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064339075245 [Pid 327578] Lock granted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Already hold local 0)
745064339092056 [Pid 327578] Lock was acquired in 59223 ns
745064339118530 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339141606 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339159893 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064339176278 [Pid 327578] Lock was acquired in 57748 ns
745064339275302 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339295035 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064339320204 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339343605 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339362550 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064339379189 [Pid 327578] Lock was acquired in 58985 ns
745064339466953 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339486483 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064339512103 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339535492 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339554170 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064339570785 [Pid 327578] Lock was acquired in 58682 ns
745064339661539 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339680770 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064339706403 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339731859 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339750907 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064339767580 [Pid 327578] Lock was acquired in 61177 ns
745064339855776 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064339875244 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064339898815 [Pid 327578] Table close 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064339920526 [Pid 327578] Lock ungranted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064339939861 [Pid 327578] Lock ungranted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Hold local 0)
745064339961989 [Pid 327578] Table open 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064339978907 [Pid 327578] Lock object 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064340001670 [Pid 327578] Lock granted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064340020405 [Pid 327578] Lock granted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Already hold local 0)
745064340036728 [Pid 327578] Lock was acquired in 57821 ns
745064340060373 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064340083157 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064340101890 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064340118486 [Pid 327578] Lock was acquired in 58113 ns
745064340198186 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064340219330 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064340250646 [Pid 327578] Lock object 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock
745064340274684 [Pid 327578] Lock granted (fastpath) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock
745064340293524 [Pid 327578] Lock granted (local) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock (Already hold local 0)
745064340310202 [Pid 327578] Lock was acquired in 59556 ns
745064340337112 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock
745064340360031 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock
745064340378739 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock (Already hold local 0)
745064340395496 [Pid 327578] Lock was acquired in 58384 ns
745064340576666 [Pid 327578] Lock ungranted (fastpath) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock
745064340596299 [Pid 327578] Lock ungranted (local) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock (Hold local 0)
745064340620661 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock
745064340639350 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock (Hold local 0)
745064340660990 [Pid 327578] Table close 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064340682154 [Pid 327578] Lock ungranted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064340700466 [Pid 327578] Lock ungranted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Hold local 0)
745064340724983 [Pid 327578] Table close 1247 (pg_catalog.pg_type) RowExclusiveLock
745064340745747 [Pid 327578] Lock ungranted (fastpath) 1247 (pg_catalog.pg_type) RowExclusiveLock
745064340763978 [Pid 327578] Lock ungranted (local) 1247 (pg_catalog.pg_type) RowExclusiveLock (Hold local 0)
745064340789474 [Pid 327578] Table open 1247 (pg_catalog.pg_type) AccessShareLock
745064340805855 [Pid 327578] Lock object 1247 (pg_catalog.pg_type) AccessShareLock
745064340828989 [Pid 327578] Lock granted (fastpath) 1247 (pg_catalog.pg_type) AccessShareLock
745064340847526 [Pid 327578] Lock granted (local) 1247 (pg_catalog.pg_type) AccessShareLock (Already hold local 0)
745064340864256 [Pid 327578] Lock was acquired in 58401 ns
745064340885838 [Pid 327578] Lock object 2704 (pg_catalog.pg_type_typname_nsp_index) AccessShareLock
745064340909039 [Pid 327578] Lock granted (fastpath) 2704 (pg_catalog.pg_type_typname_nsp_index) AccessShareLock
745064340928115 [Pid 327578] Lock granted (local) 2704 (pg_catalog.pg_type_typname_nsp_index) AccessShareLock (Already hold local 0)
745064340944601 [Pid 327578] Lock was acquired in 58763 ns
745064341048196 [Pid 327578] Lock ungranted (fastpath) 2704 (pg_catalog.pg_type_typname_nsp_index) AccessShareLock
745064341067296 [Pid 327578] Lock ungranted (local) 2704 (pg_catalog.pg_type_typname_nsp_index) AccessShareLock (Hold local 0)
745064341090013 [Pid 327578] Table close 1247 (pg_catalog.pg_type) AccessShareLock
745064341111287 [Pid 327578] Lock ungranted (fastpath) 1247 (pg_catalog.pg_type) AccessShareLock
745064341129580 [Pid 327578] Lock ungranted (local) 1247 (pg_catalog.pg_type) AccessShareLock (Hold local 0)
745064341157165 [Pid 327578] Table open 1247 (pg_catalog.pg_type) RowExclusiveLock
745064341173685 [Pid 327578] Lock object 1247 (pg_catalog.pg_type) RowExclusiveLock
745064341196776 [Pid 327578] Lock granted (fastpath) 1247 (pg_catalog.pg_type) RowExclusiveLock
745064341215241 [Pid 327578] Lock granted (local) 1247 (pg_catalog.pg_type) RowExclusiveLock (Already hold local 0)
745064341231900 [Pid 327578] Lock was acquired in 58215 ns
745064341268528 [Pid 327578] Lock object 2703 (pg_catalog.pg_type_oid_index) RowExclusiveLock
745064341292333 [Pid 327578] Lock granted (fastpath) 2703 (pg_catalog.pg_type_oid_index) RowExclusiveLock
745064341341162 [Pid 327578] Lock granted (local) 2703 (pg_catalog.pg_type_oid_index) RowExclusiveLock (Already hold local 0)
745064341358832 [Pid 327578] Lock was acquired in 90304 ns
745064341383548 [Pid 327578] Lock object 2704 (pg_catalog.pg_type_typname_nsp_index) RowExclusiveLock
745064341406525 [Pid 327578] Lock granted (fastpath) 2704 (pg_catalog.pg_type_typname_nsp_index) RowExclusiveLock
745064341424954 [Pid 327578] Lock granted (local) 2704 (pg_catalog.pg_type_typname_nsp_index) RowExclusiveLock (Already hold local 0)
745064341441633 [Pid 327578] Lock was acquired in 58085 ns
745064341627523 [Pid 327578] Lock ungranted (fastpath) 2703 (pg_catalog.pg_type_oid_index) RowExclusiveLock
745064341646818 [Pid 327578] Lock ungranted (local) 2703 (pg_catalog.pg_type_oid_index) RowExclusiveLock (Hold local 0)
745064341670307 [Pid 327578] Lock ungranted (fastpath) 2704 (pg_catalog.pg_type_typname_nsp_index) RowExclusiveLock
745064341688874 [Pid 327578] Lock ungranted (local) 2704 (pg_catalog.pg_type_typname_nsp_index) RowExclusiveLock (Hold local 0)
745064341718375 [Pid 327578] Table open 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064341735109 [Pid 327578] Lock object 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064341758861 [Pid 327578] Lock granted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064341777284 [Pid 327578] Lock granted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Already hold local 0)
745064341793917 [Pid 327578] Lock was acquired in 58808 ns
745064341817673 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064341840607 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064341859012 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064341875436 [Pid 327578] Lock was acquired in 57763 ns
745064341968082 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064341987340 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064342012766 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342036033 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342054445 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064342070843 [Pid 327578] Lock was acquired in 58077 ns
745064342158890 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342177887 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064342203087 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342226414 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342245026 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064342261449 [Pid 327578] Lock was acquired in 58362 ns
745064342345876 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342364857 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064342389842 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342412949 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342431353 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064342488520 [Pid 327578] Lock was acquired in 98678 ns
745064342575520 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342594610 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064342619914 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342643371 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342662066 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064342678513 [Pid 327578] Lock was acquired in 58599 ns
745064342770413 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342790169 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064342845082 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342868911 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064342888807 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064342905919 [Pid 327578] Lock was acquired in 60837 ns
745064342994114 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064343014416 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064343039456 [Pid 327578] Table close 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064343061781 [Pid 327578] Lock ungranted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064343081935 [Pid 327578] Lock ungranted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Hold local 0)
745064343104591 [Pid 327578] Table open 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064343121705 [Pid 327578] Lock object 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064343145901 [Pid 327578] Lock granted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064343165164 [Pid 327578] Lock granted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Already hold local 0)
745064343182282 [Pid 327578] Lock was acquired in 60577 ns
745064343207310 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064343231307 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064343250703 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064343267770 [Pid 327578] Lock was acquired in 60460 ns
745064343347934 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064343367921 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064343398614 [Pid 327578] Lock object 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock
745064343423194 [Pid 327578] Lock granted (fastpath) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock
745064343442803 [Pid 327578] Lock granted (local) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock (Already hold local 0)
745064343459844 [Pid 327578] Lock was acquired in 61230 ns
745064343485455 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock
745064343509461 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock
745064343528810 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock (Already hold local 0)
745064343545847 [Pid 327578] Lock was acquired in 60392 ns
745064343695078 [Pid 327578] Lock ungranted (fastpath) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock
745064343715321 [Pid 327578] Lock ungranted (local) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock (Hold local 0)
745064343740180 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock
745064343759691 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock (Hold local 0)
745064343782057 [Pid 327578] Table close 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064343803974 [Pid 327578] Lock ungranted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064343823230 [Pid 327578] Lock ungranted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Hold local 0)
745064343848289 [Pid 327578] Table close 1247 (pg_catalog.pg_type) RowExclusiveLock
745064343870083 [Pid 327578] Lock ungranted (fastpath) 1247 (pg_catalog.pg_type) RowExclusiveLock
745064343889205 [Pid 327578] Lock ungranted (local) 1247 (pg_catalog.pg_type) RowExclusiveLock (Hold local 0)
745064343926948 [Pid 327578] Lock object 2662 (pg_catalog.pg_class_oid_index) RowExclusiveLock
745064343951401 [Pid 327578] Lock granted (fastpath) 2662 (pg_catalog.pg_class_oid_index) RowExclusiveLock
745064343970873 [Pid 327578] Lock granted (local) 2662 (pg_catalog.pg_class_oid_index) RowExclusiveLock (Already hold local 0)
745064343987792 [Pid 327578] Lock was acquired in 60844 ns
745064344013730 [Pid 327578] Lock object 2663 (pg_catalog.pg_class_relname_nsp_index) RowExclusiveLock
745064344038107 [Pid 327578] Lock granted (fastpath) 2663 (pg_catalog.pg_class_relname_nsp_index) RowExclusiveLock
745064344058417 [Pid 327578] Lock granted (local) 2663 (pg_catalog.pg_class_relname_nsp_index) RowExclusiveLock (Already hold local 0)
745064344075613 [Pid 327578] Lock was acquired in 61883 ns
745064344101275 [Pid 327578] Lock object 3455 (pg_catalog.pg_class_tblspc_relfilenode_index) RowExclusiveLock
745064344125438 [Pid 327578] Lock granted (fastpath) 3455 (pg_catalog.pg_class_tblspc_relfilenode_index) RowExclusiveLock
745064344144823 [Pid 327578] Lock granted (local) 3455 (pg_catalog.pg_class_tblspc_relfilenode_index) RowExclusiveLock (Already hold local 0)
745064344161792 [Pid 327578] Lock was acquired in 60517 ns
745064344396301 [Pid 327578] Lock ungranted (fastpath) 2662 (pg_catalog.pg_class_oid_index) RowExclusiveLock
745064344416716 [Pid 327578] Lock ungranted (local) 2662 (pg_catalog.pg_class_oid_index) RowExclusiveLock (Hold local 0)
745064344442093 [Pid 327578] Lock ungranted (fastpath) 2663 (pg_catalog.pg_class_relname_nsp_index) RowExclusiveLock
745064344461627 [Pid 327578] Lock ungranted (local) 2663 (pg_catalog.pg_class_relname_nsp_index) RowExclusiveLock (Hold local 0)
745064344486604 [Pid 327578] Lock ungranted (fastpath) 3455 (pg_catalog.pg_class_tblspc_relfilenode_index) RowExclusiveLock
745064344506759 [Pid 327578] Lock ungranted (local) 3455 (pg_catalog.pg_class_tblspc_relfilenode_index) RowExclusiveLock (Hold local 0)
745064344530484 [Pid 327578] Table open 1249 (pg_catalog.pg_attribute) RowExclusiveLock
745064344548232 [Pid 327578] Lock object 1249 (pg_catalog.pg_attribute) RowExclusiveLock
745064344572515 [Pid 327578] Lock granted (fastpath) 1249 (pg_catalog.pg_attribute) RowExclusiveLock
745064344592394 [Pid 327578] Lock granted (local) 1249 (pg_catalog.pg_attribute) RowExclusiveLock (Already hold local 0)
745064344609832 [Pid 327578] Lock was acquired in 61600 ns
745064344638223 [Pid 327578] Lock object 2658 (pg_catalog.pg_attribute_relid_attnam_index) RowExclusiveLock
745064344662911 [Pid 327578] Lock granted (fastpath) 2658 (pg_catalog.pg_attribute_relid_attnam_index) RowExclusiveLock
745064344682442 [Pid 327578] Lock granted (local) 2658 (pg_catalog.pg_attribute_relid_attnam_index) RowExclusiveLock (Already hold local 0)
745064344699381 [Pid 327578] Lock was acquired in 61158 ns
745064344726938 [Pid 327578] Lock object 2659 (pg_catalog.pg_attribute_relid_attnum_index) RowExclusiveLock
745064344751669 [Pid 327578] Lock granted (fastpath) 2659 (pg_catalog.pg_attribute_relid_attnum_index) RowExclusiveLock
745064344771221 [Pid 327578] Lock granted (local) 2659 (pg_catalog.pg_attribute_relid_attnum_index) RowExclusiveLock (Already hold local 0)
745064344788278 [Pid 327578] Lock was acquired in 61340 ns
745064345099100 [Pid 327578] Table open 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345117485 [Pid 327578] Lock object 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345142284 [Pid 327578] Lock granted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345161787 [Pid 327578] Lock granted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Already hold local 0)
745064345178996 [Pid 327578] Lock was acquired in 61511 ns
745064345204505 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064345228926 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064345248442 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064345265473 [Pid 327578] Lock was acquired in 60968 ns
745064345393173 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064345413932 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064345438503 [Pid 327578] Table close 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345461015 [Pid 327578] Lock ungranted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345480576 [Pid 327578] Lock ungranted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Hold local 0)
745064345502818 [Pid 327578] Table open 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345519944 [Pid 327578] Lock object 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345544039 [Pid 327578] Lock granted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345563246 [Pid 327578] Lock granted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Already hold local 0)
745064345580361 [Pid 327578] Lock was acquired in 60417 ns
745064345605327 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064345629516 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064345648760 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064345665722 [Pid 327578] Lock was acquired in 60395 ns
745064345752239 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064345772579 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064345796763 [Pid 327578] Table close 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345822035 [Pid 327578] Lock ungranted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345841159 [Pid 327578] Lock ungranted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Hold local 0)
745064345863107 [Pid 327578] Table open 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345879945 [Pid 327578] Lock object 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345904002 [Pid 327578] Lock granted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064345923102 [Pid 327578] Lock granted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Already hold local 0)
745064345939934 [Pid 327578] Lock was acquired in 59989 ns
745064345964544 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064345988395 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064346007719 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064346024410 [Pid 327578] Lock was acquired in 59866 ns
745064346111281 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064346131283 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064346155446 [Pid 327578] Table close 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064346177619 [Pid 327578] Lock ungranted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064346196627 [Pid 327578] Lock ungranted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Hold local 0)
745064346803127 [Pid 327578] Lock ungranted (fastpath) 2658 (pg_catalog.pg_attribute_relid_attnam_index) RowExclusiveLock
745064346823666 [Pid 327578] Lock ungranted (local) 2658 (pg_catalog.pg_attribute_relid_attnam_index) RowExclusiveLock (Hold local 0)
745064346848221 [Pid 327578] Lock ungranted (fastpath) 2659 (pg_catalog.pg_attribute_relid_attnum_index) RowExclusiveLock
745064346867396 [Pid 327578] Lock ungranted (local) 2659 (pg_catalog.pg_attribute_relid_attnum_index) RowExclusiveLock (Hold local 0)
745064346889677 [Pid 327578] Table close 1249 (pg_catalog.pg_attribute) RowExclusiveLock
745064346911402 [Pid 327578] Lock ungranted (fastpath) 1249 (pg_catalog.pg_attribute) RowExclusiveLock
745064346930609 [Pid 327578] Lock ungranted (local) 1249 (pg_catalog.pg_attribute) RowExclusiveLock (Hold local 0)
745064346954599 [Pid 327578] Table open 1214 (pg_catalog.pg_shdepend) RowExclusiveLock
745064346971633 [Pid 327578] Lock object 1214 (pg_catalog.pg_shdepend) RowExclusiveLock
745064347005777 [Pid 327578] Lock granted 1214 (pg_catalog.pg_shdepend) RowExclusiveLock (Requested locks 1)
745064347024111 [Pid 327578] Lock granted (local) 1214 (pg_catalog.pg_shdepend) RowExclusiveLock (Already hold local 0)
745064347042353 [Pid 327578] Lock was acquired in 70720 ns
745064347068452 [Pid 327578] Lock object 1233 (pg_catalog.pg_shdepend_reference_index) AccessShareLock
745064347099104 [Pid 327578] Lock granted 1233 (pg_catalog.pg_shdepend_reference_index) AccessShareLock (Requested locks 1)
745064347116884 [Pid 327578] Lock granted (local) 1233 (pg_catalog.pg_shdepend_reference_index) AccessShareLock (Already hold local 0)
745064347134876 [Pid 327578] Lock was acquired in 66424 ns
745064347218507 [Pid 327578] Lock ungranted 1233 (pg_catalog.pg_shdepend_reference_index) AccessShareLock (Requested locks 1)
745064347242474 [Pid 327578] Lock ungranted (local) 1233 (pg_catalog.pg_shdepend_reference_index) AccessShareLock (Hold local 0)
745064347266550 [Pid 327578] Table close 1214 (pg_catalog.pg_shdepend) RowExclusiveLock
745064347289588 [Pid 327578] Lock ungranted 1214 (pg_catalog.pg_shdepend) RowExclusiveLock (Requested locks 1)
745064347311734 [Pid 327578] Lock ungranted (local) 1214 (pg_catalog.pg_shdepend) RowExclusiveLock (Hold local 0)
745064347336007 [Pid 327578] Table open 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064347353183 [Pid 327578] Lock object 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064347376890 [Pid 327578] Lock granted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064347396366 [Pid 327578] Lock granted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Already hold local 0)
745064347413477 [Pid 327578] Lock was acquired in 60294 ns
745064347438596 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064347462497 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064347481886 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064347498752 [Pid 327578] Lock was acquired in 60156 ns
745064347638679 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064347658780 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064347687516 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064347711680 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064347730837 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Already hold local 0)
745064347749468 [Pid 327578] Lock was acquired in 61952 ns
745064347836563 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock
745064347856592 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) AccessShareLock (Hold local 0)
745064347885124 [Pid 327578] Lock object 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock
745064347909388 [Pid 327578] Lock granted (fastpath) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock
745064347928524 [Pid 327578] Lock granted (local) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock (Already hold local 0)
745064347945405 [Pid 327578] Lock was acquired in 60281 ns
745064347971113 [Pid 327578] Lock object 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock
745064347995140 [Pid 327578] Lock granted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock
745064348014609 [Pid 327578] Lock granted (local) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock (Already hold local 0)
745064348102848 [Pid 327578] Lock was acquired in 131735 ns
745064359396329 [Pid 327578] Lock ungranted (fastpath) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock
745064359418584 [Pid 327578] Lock ungranted (local) 2673 (pg_catalog.pg_depend_depender_index) RowExclusiveLock (Hold local 0)
745064359442539 [Pid 327578] Lock ungranted (fastpath) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock
745064359461367 [Pid 327578] Lock ungranted (local) 2674 (pg_catalog.pg_depend_reference_index) RowExclusiveLock (Hold local 0)
745064359483081 [Pid 327578] Table close 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064359504077 [Pid 327578] Lock ungranted (fastpath) 2608 (pg_catalog.pg_depend) RowExclusiveLock
745064359522493 [Pid 327578] Lock ungranted (local) 2608 (pg_catalog.pg_depend) RowExclusiveLock (Hold local 0)
745064359548580 [Pid 327578] Table close 328332 (public.metrics) NoLock
745064359566541 [Pid 327578] Table close 1259 (pg_catalog.pg_class) RowExclusiveLock
745064359587367 [Pid 327578] Lock ungranted (fastpath) 1259 (pg_catalog.pg_class) RowExclusiveLock
745064359605717 [Pid 327578] Lock ungranted (local) 1259 (pg_catalog.pg_class) RowExclusiveLock (Hold local 0)
745064359651119 [Pid 327578] Table open 1259 (pg_catalog.pg_class) AccessShareLock
745064359667961 [Pid 327578] Lock object 1259 (pg_catalog.pg_class) AccessShareLock
745064359693375 [Pid 327578] Lock granted (fastpath) 1259 (pg_catalog.pg_class) AccessShareLock
745064359714827 [Pid 327578] Lock granted (local) 1259 (pg_catalog.pg_class) AccessShareLock (Already hold local 0)
745064359732703 [Pid 327578] Lock was acquired in 64742 ns
745064359755347 [Pid 327578] Lock object 2662 (pg_catalog.pg_class_oid_index) AccessShareLock
745064359778100 [Pid 327578] Lock granted (fastpath) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock
745064359796247 [Pid 327578] Lock granted (local) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock (Already hold local 0)
745064359812617 [Pid 327578] Lock was acquired in 57270 ns
745064359909910 [Pid 327578] Lock ungranted (fastpath) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock
745064359929042 [Pid 327578] Lock ungranted (local) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock (Hold local 0)
745064359952201 [Pid 327578] Table close 1259 (pg_catalog.pg_class) AccessShareLock
745064359973399 [Pid 327578] Lock ungranted (fastpath) 1259 (pg_catalog.pg_class) AccessShareLock
745064359991320 [Pid 327578] Lock ungranted (local) 1259 (pg_catalog.pg_class) AccessShareLock (Hold local 0)
745064360036095 [Pid 327578] Table open 1249 (pg_catalog.pg_attribute) AccessShareLock
745064360052741 [Pid 327578] Lock object 1249 (pg_catalog.pg_attribute) AccessShareLock
745064360075910 [Pid 327578] Lock granted (fastpath) 1249 (pg_catalog.pg_attribute) AccessShareLock
745064360093944 [Pid 327578] Lock granted (local) 1249 (pg_catalog.pg_attribute) AccessShareLock (Already hold local 0)
745064360110225 [Pid 327578] Lock was acquired in 57484 ns
745064360132111 [Pid 327578] Lock object 2659 (pg_catalog.pg_attribute_relid_attnum_index) AccessShareLock
745064360154727 [Pid 327578] Lock granted (fastpath) 2659 (pg_catalog.pg_attribute_relid_attnum_index) AccessShareLock
745064360172921 [Pid 327578] Lock granted (local) 2659 (pg_catalog.pg_attribute_relid_attnum_index) AccessShareLock (Already hold local 0)
745064360189385 [Pid 327578] Lock was acquired in 57274 ns
745064360354543 [Pid 327578] Lock ungranted (fastpath) 2659 (pg_catalog.pg_attribute_relid_attnum_index) AccessShareLock
745064360373938 [Pid 327578] Lock ungranted (local) 2659 (pg_catalog.pg_attribute_relid_attnum_index) AccessShareLock (Hold local 0)
745064360396537 [Pid 327578] Table close 1249 (pg_catalog.pg_attribute) AccessShareLock
745064360417835 [Pid 327578] Lock ungranted (fastpath) 1249 (pg_catalog.pg_attribute) AccessShareLock
745064360436021 [Pid 327578] Lock ungranted (local) 1249 (pg_catalog.pg_attribute) AccessShareLock (Hold local 0)
745064360483980 [Pid 327578] Lock object 328332 (public.metrics) AccessExclusiveLock
745064360606079 [Pid 327578] Lock granted 328332 (public.metrics) AccessExclusiveLock (Requested locks 1)
745064360623446 [Pid 327578] Lock granted (local) 328332 (public.metrics) AccessExclusiveLock (Already hold local 0)
745064360649586 [Pid 327578] Lock was acquired in 165606 ns
745064360728965 [Pid 327578] Table open 328332 (public.metrics) AccessExclusiveLock
745064360745603 [Pid 327578] Lock object 328332 (public.metrics) AccessExclusiveLock
745064360766604 [Pid 327578] Lock granted (local) 328332 (public.metrics) AccessExclusiveLock (Already hold local 1)
745064360781540 [Pid 327578] Lock was acquired in 35937 ns
745064360803960 [Pid 327578] Table close 328332 (public.metrics) NoLock
745064360915669 [Pid 327578] Table open 1259 (pg_catalog.pg_class) AccessShareLock
745064360932430 [Pid 327578] Lock object 1259 (pg_catalog.pg_class) AccessShareLock
745064360955869 [Pid 327578] Lock granted (fastpath) 1259 (pg_catalog.pg_class) AccessShareLock
745064360974141 [Pid 327578] Lock granted (local) 1259 (pg_catalog.pg_class) AccessShareLock (Already hold local 0)
745064360990725 [Pid 327578] Lock was acquired in 58295 ns
745064361012714 [Pid 327578] Lock object 2662 (pg_catalog.pg_class_oid_index) AccessShareLock
745064361035492 [Pid 327578] Lock granted (fastpath) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock
745064361053701 [Pid 327578] Lock granted (local) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock (Already hold local 0)
745064361070112 [Pid 327578] Lock was acquired in 57398 ns
745064361163634 [Pid 327578] Lock ungranted (fastpath) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock
745064361182887 [Pid 327578] Lock ungranted (local) 2662 (pg_catalog.pg_class_oid_index) AccessShareLock (Hold local 0)
745064361206214 [Pid 327578] Table close 1259 (pg_catalog.pg_class) AccessShareLock
745064361227633 [Pid 327578] Lock ungranted (fastpath) 1259 (pg_catalog.pg_class) AccessShareLock
745064361245881 [Pid 327578] Lock ungranted (local) 1259 (pg_catalog.pg_class) AccessShareLock (Hold local 0)
745064361287525 [Pid 327578] Table open 1259 (pg_catalog.pg_class) AccessShareLock
745064361331732 [Pid 327578] Lock object 1259 (pg_catalog.pg_class) AccessShareLock
745064361356607 [Pid 327578] Lock granted (fastpath) 1259 (pg_catalog.pg_class) AccessShareLock
745064361375138 [Pid 327578] Lock granted (local) 1259 (pg_catalog.pg_class) AccessShareLock (Already hold local 0)
745064361391959 [Pid 327578] Lock was acquired in 60227 ns
745064361424521 [Pid 327578] Table close 1259 (pg_catalog.pg_class) AccessShareLock
745064361445624 [Pid 327578] Lock ungranted (fastpath) 1259 (pg_catalog.pg_class) AccessShareLock
745064361463789 [Pid 327578] Lock ungranted (local) 1259 (pg_catalog.pg_class) AccessShareLock (Hold local 0)
745064361535429 [Pid 327578] Table open 1259 (pg_catalog.pg_class) AccessShareLock
745064361552253 [Pid 327578] Lock object 1259 (pg_catalog.pg_class) AccessShareLock
745064361575061 [Pid 327578] Lock granted (fastpath) 1259 (pg_catalog.pg_class) AccessShareLock
745064361593224 [Pid 327578] Lock granted (local) 1259 (pg_catalog.pg_class) AccessShareLock (Already hold local 0)
745064361609584 [Pid 327578] Lock was acquired in 57331 ns
745064361631520 [Pid 327578] Lock object 2663 (pg_catalog.pg_class_relname_nsp_index) AccessShareLock
745064361654381 [Pid 327578] Lock granted (fastpath) 2663 (pg_catalog.pg_class_relname_nsp_index) AccessShareLock
745064361672562 [Pid 327578] Lock granted (local) 2663 (pg_catalog.pg_class_relname_nsp_index) AccessShareLock (Already hold local 0)
745064361688805 [Pid 327578] Lock was acquired in 57285 ns
745064361788882 [Pid 327578] Lock ungranted (fastpath) 2663 (pg_catalog.pg_class_relname_nsp_index) AccessShareLock
745064361808199 [Pid 327578] Lock ungranted (local) 2663 (pg_catalog.pg_class_relname_nsp_index) AccessShareLock (Hold local 0)
745064361831553 [Pid 327578] Table close 1259 (pg_catalog.pg_class) AccessShareLock
745064361852740 [Pid 327578] Lock ungranted (fastpath) 1259 (pg_catalog.pg_class) AccessShareLock
745064361870841 [Pid 327578] Lock ungranted (local) 1259 (pg_catalog.pg_class) AccessShareLock (Hold local 0)
745064362332644 [Pid 327578] Transaction commit
745064368169138 [Pid 327578] Lock ungranted (local) 2615 (pg_catalog.pg_namespace) AccessShareLock (Hold local 2)
745064368193137 [Pid 327578] Lock ungranted (local) 328332 (public.metrics) AccessExclusiveLock (Hold local 2)
745064368236259 [Pid 327578] Lock ungranted 328332 (public.metrics) AccessExclusiveLock (Requested locks 1)
745064368260426 [Pid 327578] Lock ungranted 2615 (pg_catalog.pg_namespace) AccessShareLock (Requested locks 1)
745064368747863 [Pid 327578] Query done
```
</details>


Statistics

```
Lock statistics:
================

Locks per oid
+----------------------------------------------+----------+------------------------------+
|                  Lock Name                   | Requests | Total Lock Request Time (ns) |
+----------------------------------------------+----------+------------------------------+
|     pg_catalog.pg_depend_reference_index     |    20    |           1174663            |
|             pg_catalog.pg_depend             |    8     |            456525            |
|              pg_catalog.pg_type              |    5     |            282986            |
|     pg_catalog.pg_type_typname_nsp_index     |    4     |            229317            |
|         pg_catalog.pg_type_oid_index         |    4     |            300239            |
|             pg_catalog.pg_class              |    3     |            180540            |
|        pg_catalog.pg_class_oid_index         |    3     |            172549            |
|     pg_catalog.pg_depend_depender_index      |    3     |            171186            |
|    pg_catalog.pg_class_relname_nsp_index     |    2     |            114311            |
|           pg_catalog.pg_attribute            |    2     |            113041            |
|  pg_catalog.pg_attribute_relid_attnum_index  |    2     |            113299            |
|                public.metrics                |    2     |            223162            |
| pg_catalog.pg_class_tblspc_relfilenode_index |    1     |            56426             |
|  pg_catalog.pg_attribute_relid_attnam_index  |    1     |            57238             |
|            pg_catalog.pg_shdepend            |    1     |            65878             |
|    pg_catalog.pg_shdepend_reference_index    |    1     |            63127             |
+----------------------------------------------+----------+------------------------------+

Lock types
+---------------------+---------------------------+
|      Lock Type      | Number of requested locks |
+---------------------+---------------------------+
|   AccessShareLock   |             32            |
|   RowExclusiveLock  |             28            |
| AccessExclusiveLock |             2             |
+---------------------+---------------------------+
```

## Filter Trace Events
`pg_lock_tracer` traces per default all supported events. However, often only certain events are required for the analysis (e.g., _which tables are opened?_). The event tracing can be restricted to certain events using the `-t <EVENT1> <EVENT2>` parameter. The following events are currently supported:

| Event          | Description                                                                                          |
|----------------|------------------------------------------------------------------------------------------------------|
| `TRANSACTION`  | Transactions related events (e.g., `StartTransaction`, `CommitTransaction`, `DeadLockReport`)        |
| `QUERY`        | The executed queries (e.g., `exec_simple_query`)                                                     |
| `TABLE`        | Table open and close events (e.g., `table_open`, `table_openrv`, `table_close`)                      |
| `LOCK`         | Lock events (e.g., `LockRelationOid`, `UnlockRelationOid`, `GrantLock`, `FastPathGrantRelationLock`) |
| `INVALIDATION` | Processing of cache invalidation messages (e.g., `AcceptInvalidationMessages`)                       |
| `ERROR`        | Error related events (e.g., `bpf_errstart`)                                                          |

```
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_14_2_DEBUG/bin/postgres -p 2287921 -r 2287921:psql://jan@localhost/test2 --statistics -t TABLE
[...]
4111321097620311 [Pid 2290711] Table open (by range value) .metric_name_local AccessShareLock
4111321097626817 [Pid 2287921] Table close 343035 (public.metric_name_local) NoLock
4111321097722307 [Pid 2287921] Table open 3079 (pg_catalog.pg_extension) AccessShareLock
4111321097877109 [Pid 2287921] Table close 3079 (pg_catalog.pg_extension) AccessShareLock
4111321097904906 [Pid 2287921] Table open 3079 (pg_catalog.pg_extension) AccessShareLock
4111321098012011 [Pid 2287921] Table close 3079 (pg_catalog.pg_extension) AccessShareLock
4111321098049134 [Pid 2287921] Table open 343035 (public.metric_name_local) NoLock
4111321098072567 [Pid 2287921] Table close 343035 (public.metric_name_local) NoLock
4111321098089922 [Pid 2287921] Table open 343035 (public.metric_name_local) NoLock
4111321098116394 [Pid 2287921] Table close 343035 (public.metric_name_local) NoLock
4111321098350309 [Pid 2287921] Table open 343035 (public.metric_name_local) NoLock
4111321098484761 [Pid 2287921] Table close 343035 (public.metric_name_local) NoLock
4111321098795235 [Pid 2287921] Table open 343035 (public.metric_name_local) NoLock
4111321098931302 [Pid 2287921] Table close 343035 (public.metric_name_local) NoLock
```

## Stack Traces

It is sometimes necessary to determine where in the source code a particular lock is requested. For this purpose, the option `-s <Lock Event>` can be used. In addition to the traces, stack traces are now also shown.

For example, by specifying `-s LOCK` a stack trace is generated and shown on each lock event. The following example shows where the lock for `pg_catalog.pg_extension` was requested.

```
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_14_2_DEBUG/bin/postgres -p 1051967 -r 1051967:sql://jan@localhost/test2 -s LOCK
[...]
1990162746005798 [Pid 1051967] Lock object 3079 (pg_catalog.pg_extension) AccessShareLock
	LockRelationOid+0x0 [postgres]
	table_open+0x1d [postgres]
	parse_analyze+0xed [postgres]
	pg_analyze_and_rewrite+0x49 [postgres]
	exec_simple_query+0x2db [postgres]
	PostgresMain+0x833 [postgres]
	ExitPostmaster+0x0 [postgres]
	BackendStartup+0x1b1 [postgres]
	ServerLoop+0x2d9 [postgres]
	PostmasterMain+0x1286 [postgres]
	startup_hacks+0x0 [postgres]
	__libc_start_main+0xea [libc-2.31.so]
	[unknown]
[...]
```

### Animated Lock Graphs
See the content of the [examples](examples/) directory for examples.

# pg_lw_lock_tracer

`pg_lw_lock_trace` allows to trace lightweight locks ([LWLocks](https://github.com/postgres/postgres/blob/c8e1ba736b2b9e8c98d37a5b77c4ed31baf94147/src/backend/storage/lmgr/lwlock.c)) in a PostgreSQL process via _Userland Statically Defined Tracing_ (USDT).

## Usage Examples
```
# Trace the LW locks of the PID 1234
pg_lw_lock_tracer -p 1234

# Trace the LW locks of the PIDs 1234 and 5678
pg_lw_lock_tracer -p 1234 -p 5678

# Trace the LW locks of the PID 1234 and be verbose
pg_lw_lock_tracer -p 1234 -v

# Trace the LW locks of the PID 1234 and collect statistics
pg_lw_lock_tracer -p 1234 -v --statistics
```

## Example output

SQL Query: `insert into test values(2);`

CLI: `sudo pg_lw_lock_tracer -p 1698108 --statistics`

Tracer output:

```
2904552881615298 [Pid 1704367] Acquired lock LockFastPath (mode LW_EXCLUSIVE) / LWLockAcquire()
2904552881673849 [Pid 1704367] Unlock LockFastPath
2904552881782910 [Pid 1704367] Acquired lock ProcArray (mode LW_SHARED) / LWLockAcquire()
2904552881803614 [Pid 1704367] Unlock ProcArray
2904552881865272 [Pid 1704367] Acquired lock LockFastPath (mode LW_EXCLUSIVE) / LWLockAcquire()
2904552881883641 [Pid 1704367] Unlock LockFastPath
[...]
```

<details>
  <summary>Full Output</summary>

```
===> Ready to trace
2904552881615298 [Pid 1704367] Acquired lock LockFastPath (mode LW_EXCLUSIVE) / LWLockAcquire()
2904552881673849 [Pid 1704367] Unlock LockFastPath
2904552881782910 [Pid 1704367] Acquired lock ProcArray (mode LW_SHARED) / LWLockAcquire()
2904552881803614 [Pid 1704367] Unlock ProcArray
2904552881865272 [Pid 1704367] Acquired lock LockFastPath (mode LW_EXCLUSIVE) / LWLockAcquire()
2904552881883641 [Pid 1704367] Unlock LockFastPath
2904552882095131 [Pid 1704367] Acquired lock ProcArray (mode LW_SHARED) / LWLockAcquire()
2904552882114171 [Pid 1704367] Unlock ProcArray
2904552882225372 [Pid 1704367] Acquired lock XidGen (mode LW_EXCLUSIVE) / LWLockAcquire()
2904552882246673 [Pid 1704367] Unlock XidGen
2904552882270279 [Pid 1704367] Acquired lock LockManager (mode LW_EXCLUSIVE) / LWLockAcquire()
2904552882296782 [Pid 1704367] Unlock LockManager
2904552882335466 [Pid 1704367] Acquired lock BufferMapping (mode LW_SHARED) / LWLockAcquire()
2904552882358198 [Pid 1704367] Unlock BufferMapping
2904552882379951 [Pid 1704367] Acquired lock BufferContent (mode LW_EXCLUSIVE) / LWLockAcquire()
2904552882415333 [Pid 1704367] Acquired lock WALInsert (mode LW_EXCLUSIVE) / LWLockAcquire()
2904552882485459 [Pid 1704367] Unlock WALInsert
2904552882506167 [Pid 1704367] Unlock BufferContent
2904552882590752 [Pid 1704367] Acquired lock WALInsert (mode LW_EXCLUSIVE) / LWLockAcquire()
2904552882611656 [Pid 1704367] Unlock WALInsert
2904552882638194 [Pid 1704367] Wait for WALWrite
2904554401202251 [Pid 1704367] Wait for WALWrite lock took 1518564057 ns
2904554401222926 [Pid 1704367] Waited but not acquired WALWrite (mode LW_EXCLUSIVE) / LWLockConditionalAcquire()
2904554401234504 [Pid 1704367] Acquired lock WALWrite (mode LW_EXCLUSIVE) / LWLockConditionalAcquire()
2904554404873664 [Pid 1704367] Unlock WALWrite
2904554404928035 [Pid 1704367] Acquired lock XactSLRU (mode LW_EXCLUSIVE) / LWLockConditionalAcquire()
2904554404950334 [Pid 1704367] Unlock XactSLRU
2904554404972224 [Pid 1704367] Acquired lock ProcArray (mode LW_EXCLUSIVE) / LWLockConditionalAcquire()
2904554404993887 [Pid 1704367] Unlock ProcArray
2904554405022734 [Pid 1704367] Acquired lock LockFastPath (mode LW_EXCLUSIVE) / LWLockAcquire()
2904554405038888 [Pid 1704367] Unlock LockFastPath
2904554405059788 [Pid 1704367] Acquired lock LockFastPath (mode LW_EXCLUSIVE) / LWLockAcquire()
2904554405088143 [Pid 1704367] Unlock LockFastPath
2904554405106194 [Pid 1704367] Acquired lock LockManager (mode LW_EXCLUSIVE) / LWLockAcquire()
2904554405145780 [Pid 1704367] Unlock LockManager
2904554405622791 [Pid 1704367] Acquired lock PgStatsData (mode LW_EXCLUSIVE) / LWLockConditionalAcquire()
2904554405640885 [Pid 1704367] Unlock PgStatsData
2904554405665146 [Pid 1704367] Acquired lock PgStatsData (mode LW_EXCLUSIVE) / LWLockConditionalAcquire()
2904554405682599 [Pid 1704367] Unlock PgStatsData
2904554405704514 [Pid 1704367] Acquired lock PgStatsData (mode LW_EXCLUSIVE) / LWLockConditionalAcquire()
2904554405720734 [Pid 1704367] Unlock PgStatsData
2904554405737937 [Pid 1704367] Acquired lock PgStatsData (mode LW_EXCLUSIVE) / LWLockConditionalAcquire()
2904554405755387 [Pid 1704367] Unlock PgStatsData
```
</details>

Statistics

```
Lock statistics:
================

Locks per tranche
+---------------+----------+--------------------------+------------------------+-------------------------------+-----------------------------+-------+----------------+
|    Tranche    | Acquired | AcquireOrWait (Acquired) | AcquireOrWait (Waited) | ConditionalAcquire (Acquired) | ConditionalAcquire (Failed) | Waits | Wait time (ns) |
+---------------+----------+--------------------------+------------------------+-------------------------------+-----------------------------+-------+----------------+
| BufferContent |    1     |            0             |           0            |               0               |              0              |   0   |       0        |
| BufferMapping |    1     |            0             |           0            |               0               |              0              |   0   |       0        |
|  LockFastPath |    4     |            0             |           0            |               0               |              0              |   0   |       0        |
|  LockManager  |    2     |            0             |           0            |               0               |              0              |   0   |       0        |
|  PgStatsData  |    0     |            0             |           0            |               4               |              0              |   0   |       0        |
|   ProcArray   |    2     |            0             |           0            |               1               |              0              |   0   |       0        |
|   WALInsert   |    2     |            0             |           0            |               0               |              0              |   0   |       0        |
|    WALWrite   |    0     |            1             |           1            |               0               |              0              |   1   |   1518564057   |
|    XactSLRU   |    0     |            0             |           0            |               1               |              0              |   0   |       0        |
|     XidGen    |    1     |            0             |           0            |               0               |              0              |   0   |       0        |
+---------------+----------+--------------------------+------------------------+-------------------------------+-----------------------------+-------+----------------+

Locks per type
+--------------+----------+
|  Lock type   | Requests |
+--------------+----------+
| LW_EXCLUSIVE |    18    |
|  LW_SHARED   |    3     |
+--------------+----------+
```

# pg_row_lock_tracer

`pg_row_lock_tracer` allows to trace row locks (see the PostgreSQL [documentation](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS)) of a PostgreSQL process using _eBPF_ and _UProbes_

## Usage Examples
```
# Trace the row locks of the given PostgreSQL binary
pg_row_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres

# Trace the row locks of the PID 1234
pg_row_lock_tracer -p 1234 -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres

# Trace the row locks of the PID 1234 and 5678
pg_row_lock_tracer -p 1234 -p 5678 -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres

# Trace the row locks of the PID 1234 and be verbose
pg_row_lock_tracer -p 1234 -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres -v

# Trace the row locks and show statistics
pg_row_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres --statistics
```

## Example output

SQL Query: `SELECT * FROM temperature FOR UPDATE;`

CLI: `sudo pg_row_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres --statistics`


Tracer output:

```
[...]
2783502701862408 [Pid 2604491] LOCK_TUPLE_END TM_OK in 13100 ns
2783502701877081 [Pid 2604491] LOCK_TUPLE (Tablespace 1663 database 305234 relation 313419) - (Block and offset 7 143) - LOCK_TUPLE_EXCLUSIVE LOCK_WAIT_BLOCK
2783502701972367 [Pid 2604491] LOCK_TUPLE_END TM_OK in 95286 ns
2783502701988387 [Pid 2604491] LOCK_TUPLE (Tablespace 1663 database 305234 relation 313419) - (Block and offset 7 144) - LOCK_TUPLE_EXCLUSIVE LOCK_WAIT_BLOCK
2783502702001690 [Pid 2604491] LOCK_TUPLE_END TM_OK in 13303 ns
2783502702016387 [Pid 2604491] LOCK_TUPLE (Tablespace 1663 database 305234 relation 313419) - (Block and offset 7 145) - LOCK_TUPLE_EXCLUSIVE LOCK_WAIT_BLOCK
2783502702029375 [Pid 2604491] LOCK_TUPLE_END TM_OK in 12988 ns
^C
Lock statistics:
================

Used wait policies:
+---------+-----------------+----------------+-----------------+
|   PID   | LOCK_WAIT_BLOCK | LOCK_WAIT_SKIP | LOCK_WAIT_ERROR |
+---------+-----------------+----------------+-----------------+
| 2604491 |       1440      |       0        |        0        |
+---------+-----------------+----------------+-----------------+

Lock modes:
+---------+---------------------+------------------+---------------------------+----------------------+
|   PID   | LOCK_TUPLE_KEYSHARE | LOCK_TUPLE_SHARE | LOCK_TUPLE_NOKEYEXCLUSIVE | LOCK_TUPLE_EXCLUSIVE |
+---------+---------------------+------------------+---------------------------+----------------------+
| 2604491 |          0          |        0         |             0             |         1440         |
+---------+---------------------+------------------+---------------------------+----------------------+

Lock results:
+---------+-------+--------------+-----------------+------------+------------+------------------+---------------+
|   PID   | TM_OK | TM_INVISIBLE | TM_SELFMODIFIED | TM_UPDATED | TM_DELETED | TM_BEINGMODIFIED | TM_WOULDBLOCK |
+---------+-------+--------------+-----------------+------------+------------+------------------+---------------+
| 2604491 |  1440 |      0       |        0        |     0      |     0      |        0         |       0       |
+---------+-------+--------------+-----------------+------------+------------+------------------+---------------+
```

# Additional Information

## Installation

The PostgreSQL lock tracing tools are available as a Python package. These tools depend on the Python package for BPF. Unfortunately, this package is currently not available via `pip` (the Python package manager). Therefore, the package of the Linux distribution needs to be installed to provide this dependency. On Debian and Ubuntu, this can be done by executing the following command:

```shell
apt install python3-bpfcc
```

The tracing tools can be installed system-wide or in a dedicated [virtual environment](https://docs.python.org/3/library/venv.html). To create and install the tools in such a virtual environment, the following steps must be performed. To install the tools system-wide, these steps can be skipped.

```shell
cd <installation directory>
python3 -m venv .venv
source .venv/bin/activate

# Copy the distribution Python BCC packages into this environment
cp -av /usr/lib/python3/dist-packages/bcc* $(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
```

Now, the tracing tools can be installed directly via `pip` by executing:

```shell
pip install pg-lock-tracer
```

The tools are now installed and can be invoked by calling `pg_lock_tracer` or `pg_lw_lock_tracer`.

If you want to install the latest development snapshot and development dependencies of the tools, the following commands need to be executed:

```shell
pip install -r requirements_dev.txt
pip install git+https://github.com/jnidzwetzki/pg-lock-tracer
```

## PostgreSQL Build
The software is tested with PostgreSQL versions 12, 13, 14, and 15. In order to be able to attach the _uprobes_ to the functions, they should not to be optimized away (e.g., inlined) during the compilation of PostgreSQL. Otherwise errors like `Unable to locate function XXX` will occur when `pg_lock_tracer` is started.

It is recommended to compile PostgreSQL with following CFLAGS: `CFLAGS="-ggdb -Og -g3 -fno-omit-frame-pointer"`. 

`pg_lw_lock_trace` uses [USDT probes](https://www.postgresql.org/docs/current/dynamic-trace.html). Therefore, PostgreSQL has to be compiled with `--enable-dtrace` to use this script. 
