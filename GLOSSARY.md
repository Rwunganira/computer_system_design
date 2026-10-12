# Glossary

The book's key terms in plain language, in the order the course meets them. On the course website,
these terms show their definition when you hover over them.

## Complexity (Module 1)

- **Emergent property**: behaviour of the whole system that no single part has on its own.
- **Propagation of effects**: a small change in one place forcing changes in many distant places.
- **Incommensurate scaling**: parts of a system growing at different rates, so a design that worked at one size breaks at another.
- **Modularity**: dividing a system into parts that interact only through defined interfaces.
- **Abstraction**: hiding how a module works behind a description of what it does.
- **Layering**: building each layer of a system only on the layer directly below it.
- **Hierarchy**: grouping modules into larger modules, so each level stays small enough to understand.

## Elements and naming (Modules 2 and 3)

- **Interpreter**: an active element that repeatedly fetches an instruction, decodes it and executes it.
- **Read/write coherence**: the guarantee that a read returns the value of the most recent write.
- **Naming scheme**: the rules that say which names exist, which values they can refer to and how to resolve them.
- **Name resolution**: looking up the value that a name refers to in a given context.
- **Binding**: the association between a name and a value in a context.
- **Context**: the table of bindings in which a name is resolved, such as one clinic's patient list.
- **Overloaded name**: a name that also carries information about the thing it names, such as name plus date of birth.
- **Indirection**: referring to something through a name that can be rebound, so the target can change without changing the users.

## Clients and services (Module 4)

- **Soft modularity**: modularity by convention, such as function calls in one program, where one buggy module can still damage another.
- **Enforced modularity**: modularity guaranteed by the system, such as separate programs that talk only by messages.
- **Remote procedure call**: a request to another program that looks like a function call but can fail, time out or run twice.
- **At-least-once**: a guarantee that a request runs one or more times, achieved by retrying until a reply arrives.
- **At-most-once**: a guarantee that a request never runs twice, achieved by remembering requests already handled.
- **Idempotent**: an operation that has the same effect whether it runs once or many times.
- **Idempotency key**: a unique identifier sent with a request so the service can recognise and ignore a repeat.

## Virtualization (Module 5)

- **Virtualization**: giving each program the illusion of its own processor, memory or communication link.
- **Thread**: an independent sequence of execution that shares memory with other threads in the same program.
- **Race condition**: a bug where the result depends on the unpredictable timing of concurrent threads.
- **Lock**: a mechanism that lets only one thread at a time run a piece of code that touches shared data.
- **Bounded buffer**: a fixed-size queue between producers and consumers, where producers wait when it is full.
- **Sequence coordination**: making one thread wait until another has done something, such as putting an item in a buffer.

## Performance (Module 6)

- **Latency**: the time from starting a request to getting its result.
- **Throughput**: the number of requests completed per unit of time.
- **Bottleneck**: the stage that limits the throughput of the whole system.
- **Batching**: combining many small operations into one larger one to share the fixed cost.
- **Caching**: keeping a copy of a result close by so repeated requests do not recompute it.
- **Little's law**: the average number of things in a system equals their arrival rate multiplied by the average time each spends inside.

## Networks (Module 7)

- **Best effort**: a network's promise to try to deliver a packet, with no guarantee that it arrives once, in order or at all.
- **End-to-end argument**: a function that needs the application's knowledge to be done correctly should be done at the endpoints, not in the network.
- **Acknowledgement**: a reply telling the sender that a message arrived.
- **Retransmission**: sending a message again when no acknowledgement arrives in time.
- **Duplicate suppression**: recognising and discarding a message that has already been received.

## Fault tolerance (Module 8)

- **Fault**: an underlying defect, such as a flipped bit or a bug.
- **Error**: an incorrect internal state caused by a fault.
- **Failure**: the system not delivering what it promised, as seen from outside.
- **Availability**: the fraction of time a system is working, equal to MTTF divided by MTTF plus MTTR.
- **Checksum**: a short value computed from data so that a later change to the data can be detected.
- **Triple modular redundancy**: running three replicas and taking the majority answer, so one faulty replica is outvoted.
- **Fail-fast**: stopping and reporting a problem as soon as it is detected, rather than continuing with bad data.

## Atomicity (Module 9)

- **All-or-nothing atomicity**: an action either completes entirely or leaves no trace, even if the system crashes part-way.
- **Before-or-after atomicity**: concurrent actions have the same effect as if they ran one after another.
- **Shadow copy**: writing a complete new version beside the old one, then switching to it in one atomic step.
- **Write-ahead log**: recording what an action will do before doing it, so recovery can finish or undo it after a crash.
- **Two-phase commit**: a protocol in which a coordinator asks every participant to prepare and commits only if all agree.

## Consistency (Module 10)

- **Strict consistency**: every read sees the result of the most recent write, wherever it happened.
- **Eventual consistency**: replicas may disagree for a while but converge once updates stop arriving.
- **Last writer wins**: a sync rule that keeps the update with the latest timestamp and discards the others.
- **Version vector**: a counter per replica that shows whether one version came before another or both changed concurrently.
- **Reconciliation**: merging conflicting versions into one, using a rule that fits the data.

## Security (Module 11)

- **Authentication**: verifying who is making a request.
- **Authorization**: deciding whether that principal may perform the requested action.
- **Audit log**: a record of who did what and when, kept so misuse can be detected afterwards.
- **Principle of least privilege**: giving each user and program only the access it needs.
- **Fail-safe defaults**: denying access unless it has been explicitly granted.
- **Complete mediation**: checking every access, every time, rather than only the first.
- **Message authentication code**: a value computed from a message and a secret key that shows the message was not altered.
