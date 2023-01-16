# PostgreSQL Lock Tracer
<a href="https://github.com/jnidzwetzki/pg-lock-tracer/actions/workflows/tests.yaml">
  <img alt="Build Status" src="https://github.com/jnidzwetzki/pg-lock-tracer/actions/workflows/tests.yaml/badge.svg">
</a>
<a href="http://makeapullrequest.com">
 <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" />
</a>

This project provides a few BPF (_Berkeley Packet Filter_) based tools to trace locks in PostgreSQL.

* `pg_lock_tracer` - is a lock tracer for PostgreSQL.
* `pg_lw_lock_tracer` -  is a tracer for PostgreSQL lightweight locks (LWLocks).
* `animate_lock_graph` - creates animated locks graphs based on the `pg_lock_tracer` output.

__Note:__ At the moment, PostgreSQL 14 and 15 are supported (see additional information below).

# pg_lock_tracer
`pg_lock_tracer` can be used to attach to a running PostgreSQL process  (using _UProbes_). Afterward, `pg_lock_tracer` shows all taken locks by PostgreSQL. The tool is useful for debugging locking problems within PostgreSQL or PostgreSQL extensions.

The tracer also allows dumping the output as JSON formatted lines, which allows further processing with additional tools. This repository also contains the script `animate_lock_graph`, which provides an animated version of the taken looks.

## Usage Examples
```
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
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -s LOCK, DEADLOCK

# Trace only Transaction and Query related events
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -t TRANSACTION QUERY

# Write the output into file 'trace'
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -o trace

# Show statistics about locks
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 --statistics

# Create an animated lock graph
animate_lock_graph -i create_table_trace.json -o create_table_trace.html
```

## Example Output

### Lock Traces
CLI: `pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_14_2_DEBUG/bin/postgres -p 327578 -r 327578:sql://jan@localhost/test2 --statistics`

SQL Query: `create table metrics(ts timestamptz NOT NULL, id int NOT NULL, value float);`

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


<details>
  <summary>Statistics</summary>

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
</details>


### Animated Lock Graphs
See the content of the [examples](examples/) directory for examples.

## Installation

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Use distribution packages for BCC. BCC Python packages are not provided via pip at the moment.
apt install python3-bpfcc
cp -av /usr/lib/python3/dist-packages/bcc* $(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
```

# pg_lw_lock_trace

`pg_lw_lock_trace` allows to trace lightweight locks (LWLocks) in a PostgreSQL process via Userland Statically Defined Tracing (USDT).

## Usage Examples
```
# Trace the LWLocks of PID 1234
pg_lw_lock_tracer -p 1234
```

## Example output

SQL Query: `insert into test values(2);`

CLI: `sudo pg_lw_lock_tracer -p 2057969`

<details>
  <summary>Full Output</summary>

```
[2057969] Locking 23077 / mode LW_EXCLUSIVE
[2057969] Unlocking 23077
[2057969] Locking 24302 / mode LW_SHARED
[2057969] Unlocking 24302
[2057969] Locking 23077 / mode LW_EXCLUSIVE
[2057969] Unlocking 23077
[2057969] Locking 24302 / mode LW_SHARED
[2057969] Unlocking 24302
[2057969] Locking 24295 / mode LW_EXCLUSIVE
[2057969] Unlocking 24295
[2057969] Locking 23104 / mode LW_EXCLUSIVE
[2057969] Unlocking 23104
[2057969] Locking 23090 / mode LW_SHARED
[2057969] Unlocking 23090
[2057969] Locking 23022 / mode LW_EXCLUSIVE
[2057969] Locking 23012 / mode LW_EXCLUSIVE
[2057969] Unlocking 23012
[2057969] Unlocking 23022
[2057969] Locking 23012 / mode LW_EXCLUSIVE
[2057969] Unlocking 23012
[2057969] Unlocking 24349
[2057969] Unlocking 24386
[2057969] Unlocking 24302
[2057969] Locking 23077 / mode LW_EXCLUSIVE
[2057969] Unlocking 23077
[2057969] Locking 23077 / mode LW_EXCLUSIVE
[2057969] Unlocking 23077
[2057969] Locking 23104 / mode LW_EXCLUSIVE
[2057969] Unlocking 23104
[2057969] Unlocking 23321
[2057969] Unlocking 23321
[2057969] Unlocking 23321
[2057969] Unlocking 23321
```
</details>

# Additional Information

## PostgreSQL Build
The software is tested with PostgreSQL 14 and PostgreSQL 15. In order to be able to attach the _uprobes_ to the functions, they should not to be optimized away (e.g., inlined) during the compilation of PostgreSQL. Otherwise errors like `Unable to locate function XXX` will occur when `pg_lock_tracer` is started.

It is recommended to compile PostgreSQL with following CFLAGS: `CFLAGS="-ggdb -Og -g3 -fno-omit-frame-pointer"`. 

`pg_lw_lock_trace` uses [USDT probes](https://www.postgresql.org/docs/current/dynamic-trace.html). Therefore, PostgreSQL has to be compiled with `--enable-dtrace` to use this script. 

## Development

### Run tests
```shell
pytest
```
